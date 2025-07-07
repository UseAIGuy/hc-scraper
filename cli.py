#!/usr/bin/env python3
"""
Command-line interface for HappyCow scraper
"""
import argparse
import asyncio
import logging
from typing import List, Dict, Optional
import sys
from config import ScrapingConfig, load_config
from scraper import HappyCowScraper
from queue_manager import QueueManager, CityTask

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description="HappyCow Restaurant Scraper")
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--cities", type=str, help="Comma-separated list of cities to scrape")
    mode_group.add_argument("--queue", action="store_true", help="Use queue-based scraping from city_queue table")
    mode_group.add_argument("--status", action="store_true", help="Show queue status and exit")
    
    # Queue-based options
    parser.add_argument("--max-cities", type=int, default=1, help="Maximum cities to process in this run")
    parser.add_argument("--min-entries", type=int, default=50, help="Minimum restaurant entries for a city")
    parser.add_argument("--max-entries", type=int, default=1500, help="Maximum restaurant entries for a city")
    parser.add_argument("--states", type=str, help="Comma-separated list of states to target")
    parser.add_argument("--resume", action="store_true", default=True, help="Resume cities from last page")
    parser.add_argument("--no-resume", dest="resume", action="store_false", help="Start cities from page 1")
    
    # General scraping options
    parser.add_argument("--test", action="store_true", help="Test mode with limited restaurants")
    parser.add_argument("--max-restaurants", type=int, help="Max restaurants per city (test mode)")
    parser.add_argument("--max-pages", type=int, help="Max pages per city")
    parser.add_argument("--workers", type=int, default=3, help="Number of concurrent workers")
    parser.add_argument("--start-page", type=int, default=1, help="Page to start from (manual cities only)")
    
    return parser.parse_args()

async def show_queue_status(queue_manager: QueueManager):
    """Display current queue status"""
    print("\n🔍 HappyCow Scraper Queue Status")
    print("=" * 50)
    
    status = await queue_manager.get_queue_status()
    
    if not status:
        print("❌ Could not retrieve queue status")
        return
    
    print(f"📊 Total Cities: {status['total_cities']}")
    print(f"🍽️  Total Pending Restaurants: {status['total_pending_restaurants']:,}")
    print()
    
    print("📋 Cities by Status:")
    for status_name, count in status['status_counts'].items():
        emoji = {
            'pending': '⏳',
            'running': '🏃',
            'completed': '✅',
            'error': '❌',
            'skip': '⏭️'
        }.get(status_name, '📄')
        print(f"  {emoji} {status_name.title()}: {count}")
    
    # Show next city to be processed
    next_city = await queue_manager.get_next_city()
    if next_city:
        print(f"\n🎯 Next City: {next_city.city}, {next_city.state}")
        print(f"   📍 Entries: {next_city.entries}")
        print(f"   📄 Start Page: {next_city.current_page}")
        print(f"   🔗 Path: {next_city.full_path}")

async def scrape_from_queue(config: ScrapingConfig, args):
    """Scrape cities from the queue"""
    queue_manager = QueueManager(config)
    
    async with HappyCowScraper(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_key,
        max_workers=config.max_concurrency,
        min_delay=config.human_delay_range[0],
        max_delay=config.human_delay_range[1]
    ) as scraper:
        
        cities_processed = 0
        
        print(f"\n🚀 Starting queue-based scraping (max {args.max_cities} cities)")
        print("=" * 60)
        
        while cities_processed < args.max_cities:
            # Get next city
            city_task = await queue_manager.get_next_city()
            
            if not city_task:
                print("✅ No more cities available for scraping")
                break
            
            print(f"\n🏙️  Processing: {city_task.city}, {city_task.state}")
            print(f"   📊 Expected entries: {city_task.entries}")
            print(f"   📄 Starting from page: {city_task.current_page}")
            
            # Mark city as running
            await queue_manager.mark_city_running(city_task)
            
            try:
                # Extract the proper path from the URL
                # URL format: https://www.happycow.net/north_america/usa/state/city/
                city_path = city_task.url.replace('https://www.happycow.net/', '').rstrip('/')
                
                # Scrape the city using the proper path from database
                result = await scraper.scrape_city_complete(
                    city_task.city,
                    max_restaurants=config.max_restaurants_per_city if config.test_mode else None,
                    city_path=city_path  # Use the extracted path from URL
                )
                
                restaurants_scraped = len(result.get('restaurants', []))
                
                if result.get('success', False):
                    await queue_manager.mark_city_completed(city_task, restaurants_scraped)
                    print(f"✅ Completed {city_task.city}: {restaurants_scraped} restaurants scraped")
                else:
                    error_msg = f"Scraping failed: {result.get('error', 'Unknown error')}"
                    await queue_manager.mark_city_error(city_task, error_msg)
                    print(f"❌ Failed {city_task.city}: {error_msg}")
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                await queue_manager.mark_city_error(city_task, error_msg)
                print(f"💥 Error processing {city_task.city}: {error_msg}")
                logger.exception("Scraping error")
            
            cities_processed += 1
            
            if cities_processed < args.max_cities:
                print(f"\n⏳ Processed {cities_processed}/{args.max_cities} cities")
        
        print(f"\n🎉 Queue scraping completed! Processed {cities_processed} cities.")

async def scrape_manual_cities(config: ScrapingConfig, args):
    """Scrape manually specified cities"""
    async with HappyCowScraper(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_key,
        max_workers=config.max_concurrency,
        min_delay=config.human_delay_range[0],
        max_delay=config.human_delay_range[1]
    ) as scraper:
        
        # Parse cities
        cities = {}
        for city_name in args.cities.split(','):
            # Clean up city name - remove quotes, backslashes, and extra whitespace
            city_name = city_name.strip().strip('"').strip("'").strip('\\').strip()
            if city_name:  # Only add non-empty city names
                cities[city_name] = f"https://www.happycow.net/{scraper._get_city_path(city_name)}/"
        
        print(f"\n🏙️  Scraping {len(cities)} manual cities")
        print("=" * 50)
        
        # Process each city
        for city_name, city_url in cities.items():
            print(f"\n📍 Processing: {city_name}")
            
            try:
                result = await scraper.scrape_city_complete(
                    city_name, 
                    max_restaurants=config.max_restaurants_per_city if config.test_mode else None
                )
                
                if result.get('success', False):
                    print(f"✅ {city_name}: {result['restaurants_saved']} saved, {result['restaurants_skipped']} skipped")
                else:
                    print(f"❌ {city_name}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"💥 Error processing {city_name}: {e}")
                logger.exception("Scraping error")

async def main():
    args = parse_arguments()
    
    # Load configuration
    config = load_config()
    
    # Apply CLI overrides
    config.test_mode = args.test
    config.max_concurrency = args.workers
    config.resume_city = args.resume
    
    if args.max_restaurants:
        config.max_restaurants_per_city = args.max_restaurants
    
    # Queue-specific config
    if args.queue or args.status:
        config.queue_mode = True
        config.max_cities_per_run = args.max_cities
        config.min_entries_threshold = args.min_entries
        config.max_entries_threshold = args.max_entries
        
        if args.states:
            config.target_states = [s.strip() for s in args.states.split(',')]
    
    # Validate configuration
    if not config.supabase_url or not config.supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
        sys.exit(1)
    
    # Handle different modes
    if args.status:
        queue_manager = QueueManager(config)
        await show_queue_status(queue_manager)
        
    elif args.queue:
        await scrape_from_queue(config, args)
        
    elif args.cities:
        await scrape_manual_cities(config, args)

if __name__ == "__main__":
    asyncio.run(main()) 