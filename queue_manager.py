"""
Queue Manager for HappyCow Scraper
Handles dynamic city selection, progress tracking, and resume capability
"""

import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from dataclasses import dataclass
import logging
from supabase import create_client, Client

from config import ScrapingConfig

logger = logging.getLogger(__name__)

@dataclass
class CityTask:
    """Represents a city to be scraped"""
    id: str
    state: str
    city: str
    entries: int
    full_path: str
    url: str
    trigger_status: str
    last_scraped: Optional[datetime]
    current_page: int = 1
    total_pages: Optional[int] = None
    restaurants_scraped: int = 0

class QueueManager:
    """Manages the city scraping queue and progress tracking"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.supabase: Client = create_client(config.supabase_url, config.supabase_key)
    
    async def get_next_city(self) -> Optional[CityTask]:
        """Get the next city to scrape based on priority and status"""
        
        # Build query conditions
        conditions = []
        
        # Skip cities that are too small or too large
        if self.config.min_entries_threshold:
            conditions.append(f"entries >= {self.config.min_entries_threshold}")
        if self.config.max_entries_threshold:
            conditions.append(f"entries <= {self.config.max_entries_threshold}")
        
        # Skip running cities if configured
        if self.config.skip_running_cities:
            conditions.append("trigger_status != 'running'")
        
        # Filter by target states if specified
        if self.config.target_states:
            state_list = "','".join(self.config.target_states)
            conditions.append(f"state IN ('{state_list}')")
        
        # Prefer pending cities, then completed cities for re-scraping
        conditions.append("trigger_status IN ('pending', 'completed', 'error')")
        
        where_clause = " AND ".join(conditions) if conditions else "true"
        
        # Order by priority: pending first, then by entries (descending)
        query = f"""
        SELECT * FROM city_queue 
        WHERE {where_clause}
        ORDER BY 
            CASE WHEN trigger_status = 'pending' THEN 0 ELSE 1 END,
            entries DESC
        LIMIT 1
        """
        
        try:
            result = self.supabase.table('city_queue').select('*').execute()
            
            if not result.data or len(result.data) == 0:
                logger.info("No cities available for scraping")
                return None
            
            city_data = result.data[0]
            
            # Check if we should resume this city
            resume_page = await self._get_resume_page(city_data['full_path'])
            
            city_task = CityTask(
                id=city_data['id'],
                state=city_data['state'],
                city=city_data['city'],
                entries=city_data['entries'],
                full_path=city_data['full_path'],
                url=city_data['url'],
                trigger_status=city_data['trigger_status'],
                last_scraped=city_data.get('last_scraped'),
                current_page=resume_page
            )
            
            logger.info(f"Selected city: {city_task.city}, {city_task.state} "
                       f"({city_task.entries} entries, starting page {city_task.current_page})")
            
            return city_task
            
        except Exception as e:
            logger.error(f"Error getting next city: {e}")
            return None
    
    async def _get_resume_page(self, city_path: str) -> int:
        """Determine which page to resume from for a city"""
        
        if not self.config.resume_city:
            return 1
        
        try:
            # Count how many restaurants we've already scraped for this city
            result = self.supabase.table('restaurants') \
                .select('page_number', count='exact') \
                .eq('city_path', city_path) \
                .execute()
            
            if not result.data:
                return 1
            
            # Get the highest page number we've scraped
            max_page_result = self.supabase.table('restaurants') \
                .select('page_number') \
                .eq('city_path', city_path) \
                .order('page_number', desc=True) \
                .limit(1) \
                .execute()
            
            if max_page_result.data:
                last_page = max_page_result.data[0]['page_number']
                resume_page = last_page + 1 if last_page else 1
                logger.info(f"Resuming {city_path} from page {resume_page} "
                           f"({len(result.data)} restaurants already scraped)")
                return resume_page
            
            return 1
            
        except Exception as e:
            logger.warning(f"Error determining resume page for {city_path}: {e}")
            return 1
    
    async def mark_city_running(self, city_task: CityTask) -> bool:
        """Mark a city as currently being scraped"""
        try:
            self.supabase.table('city_queue') \
                .update({
                    'trigger_status': 'running',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }) \
                .eq('id', city_task.id) \
                .execute()
            
            logger.info(f"Marked {city_task.city}, {city_task.state} as running")
            return True
            
        except Exception as e:
            logger.error(f"Error marking city as running: {e}")
            return False
    
    async def mark_city_completed(self, city_task: CityTask, restaurants_scraped: int):
        """Mark city as completed with restaurant count"""
        try:
            # Get total restaurants actually found vs expected
            total_restaurants_in_db = await self._count_city_restaurants(city_task)
            
            # Only mark as completed if we've made significant progress
            # Either we have a reasonable number of restaurants OR we've hit the expected count
            completion_threshold = min(50, city_task.entries * 0.1)  # At least 10% or 50 restaurants
            
            if total_restaurants_in_db >= completion_threshold or total_restaurants_in_db >= city_task.entries:
                status = 'completed'
                logger.info(f"Marking {city_task.city} as completed: {total_restaurants_in_db} restaurants (threshold: {completion_threshold})")
            else:
                status = 'pending'  # Keep as pending for more scraping
                logger.info(f"Keeping {city_task.city} as pending: {total_restaurants_in_db} restaurants (need {completion_threshold})")
            
            result = self.supabase.table('city_queue').update({
                'trigger_status': status,
                'last_scraped': datetime.now(timezone.utc).isoformat(),
                'restaurants_scraped': total_restaurants_in_db
            }).eq('id', city_task.id).execute()
            
            if result.data:
                logger.info(f"Updated {city_task.city} status to {status}")
            else:
                logger.error(f"Failed to update {city_task.city} status")
                
        except Exception as e:
            logger.error(f"Error marking city completed: {e}")
    
    async def _count_city_restaurants(self, city_task: CityTask) -> int:
        """Count how many restaurants we have for this city"""
        try:
            # Try multiple ways to match restaurants to this city
            result = self.supabase.table('restaurants').select('id').or_(
                f'city_name.eq.{city_task.city},'
                f'city_path.eq.{city_task.full_path},'
                f'city_path.like.%{city_task.city.lower().replace(" ", "_")}%'
            ).execute()
            
            return len(result.data) if result.data else 0
        except Exception as e:
            logger.warning(f"Error counting restaurants for {city_task.city}: {e}")
            return 0
    
    async def mark_city_error(self, city_task: CityTask, error_message: str) -> bool:
        """Mark a city as having an error"""
        try:
            self.supabase.table('city_queue') \
                .update({
                    'trigger_status': 'error',
                    'error_message': error_message[:500],  # Truncate long error messages
                    'retry_count': self.supabase.table('city_queue').select('retry_count').eq('id', city_task.id).execute().data[0].get('retry_count', 0) + 1,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }) \
                .eq('id', city_task.id) \
                .execute()
            
            logger.error(f"Marked {city_task.city}, {city_task.state} as error: {error_message}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking city as error: {e}")
            return False
    
    async def update_city_progress(self, city_task: CityTask, page: int, restaurants_count: int) -> bool:
        """Update progress for a city being scraped"""
        try:
            # We could add a progress field to city_queue table if needed
            # For now, just log the progress
            logger.info(f"Progress for {city_task.city}: page {page}, {restaurants_count} restaurants")
            return True
            
        except Exception as e:
            logger.error(f"Error updating city progress: {e}")
            return False
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get overall queue status"""
        try:
            # Count cities by status
            status_counts = {}
            
            for status in ['pending', 'running', 'completed', 'error', 'skip']:
                result = self.supabase.table('city_queue') \
                    .select('*', count='exact') \
                    .eq('trigger_status', status) \
                    .execute()
                status_counts[status] = result.count
            
            # Get total entries across all pending cities
            pending_result = self.supabase.table('city_queue') \
                .select('entries') \
                .eq('trigger_status', 'pending') \
                .execute()
            
            total_pending_restaurants = sum(city['entries'] for city in pending_result.data)
            
            return {
                'status_counts': status_counts,
                'total_pending_restaurants': total_pending_restaurants,
                'total_cities': sum(status_counts.values())
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {} 