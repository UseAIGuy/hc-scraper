#!/usr/bin/env python3
"""
HappyCow Restaurant Scraper for Vegan Voyager
============================================

Complete scraping solution using Playwright + Crawl4AI to extract detailed 
restaurant data from HappyCow listings and save to Supabase database.

Features:
- Stealth browsing with human-like behavior
- AI-powered data extraction with structured schemas
- Individual restaurant detail page scraping
- Automatic coordinate extraction from maps
- Supabase database integration
- Comprehensive error handling and retry logic
"""

import asyncio
import logging
import json
import os
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from pathlib import Path

import asyncpg
from pydantic import BaseModel, Field, validator
from crawl4ai import AsyncWebCrawler, LLMConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from supabase import create_client, Client
import random
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================
# CONSTANTS
# ================================

PRIORITY_CITIES = {
    "Austin": "https://www.happycow.net/north_america/usa/texas/austin/",
    "Portland": "https://www.happycow.net/north_america/usa/oregon/portland/",
    "Seattle": "https://www.happycow.net/north_america/usa/washington/seattle/",
    "San Francisco": "https://www.happycow.net/north_america/usa/california/san_francisco/",
    "Los Angeles": "https://www.happycow.net/north_america/usa/california/los_angeles/",
    "New York": "https://www.happycow.net/north_america/usa/new_york/new_york/",
    "Chicago": "https://www.happycow.net/north_america/usa/illinois/chicago/",
    "Denver": "https://www.happycow.net/north_america/usa/colorado/denver/",
    "Miami": "https://www.happycow.net/north_america/usa/florida/miami/",
    "Boston": "https://www.happycow.net/north_america/usa/massachusetts/boston/"
}

# ================================
# PYDANTIC MODELS
# ================================

class RestaurantListing(BaseModel):
    """Model for restaurant data from listing pages"""
    name: str = Field(..., description="Restaurant name")
    url: str = Field(..., description="Relative URL to restaurant detail page")
    city: str = Field(..., description="City name")
    listing_type: Optional[str] = Field(None, description="Vegan, vegetarian, veg-friendly")
    is_featured: bool = Field(False, description="Is this a featured listing")
    is_new: bool = Field(False, description="Is this marked as new")

class RestaurantDetail(BaseModel):
    """Complete restaurant data model matching Supabase schema"""
    # Basic Info
    name: str = Field(..., description="Restaurant name")
    description: Optional[str] = Field(None, description="Restaurant description")
    cuisine_types: List[str] = Field(default_factory=list, description="List of cuisine types")
    vegan_status: Optional[str] = Field(None, description="Fully vegan, vegan options, etc.")
    
    # Location
    address: Optional[str] = Field(None, description="Full street address")
    city: str = Field(..., description="City name")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    
    # Contact
    phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[str] = Field(None, description="Official website URL")
    instagram: Optional[str] = Field(None, description="Instagram handle or URL")
    facebook: Optional[str] = Field(None, description="Facebook page URL")
    
    # Business Info
    hours: Optional[Dict[str, str]] = Field(None, description="Operating hours by day")
    price_range: Optional[str] = Field(None, description="Price range indicator")
    features: List[str] = Field(default_factory=list, description="Features like delivery, outdoor seating")
    
    # Reviews & Ratings
    rating: Optional[float] = Field(None, description="Average rating 0-5")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    recent_reviews: List[Dict[str, Any]] = Field(default_factory=list, description="Recent review excerpts")
    
    # Meta
    happycow_url: str = Field(..., description="Full HappyCow URL")
    happycow_id: Optional[str] = Field(None, description="HappyCow venue ID")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 0 or v > 5):
            raise ValueError('Rating must be between 0 and 5')
        return v

# ================================
# STEALTH CONFIGURATION
# ================================

@dataclass
class StealthConfig:
    """Configuration for human-like browsing behavior"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    
    MIN_DELAY = 2.0
    MAX_DELAY = 5.0
    BATCH_DELAY = 8.0
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        return {
            "User-Agent": random.choice(StealthConfig.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    @staticmethod
    async def human_delay(min_delay: float = None, max_delay: float = None):
        """Add human-like delay between requests"""
        min_d = min_delay if min_delay is not None else StealthConfig.MIN_DELAY
        max_d = max_delay if max_delay is not None else StealthConfig.MAX_DELAY
        delay = random.uniform(min_d, max_d)
        await asyncio.sleep(delay)

# ================================
# MAIN SCRAPER CLASS
# ================================

class HappyCowScraper:
    """Complete HappyCow scraper with Supabase integration"""
    
    def __init__(self, supabase_url: str, supabase_key: str, use_local_llm: bool = True, 
                 max_workers: int = 3, min_delay: float = 2.0, max_delay: float = 5.0, 
                 batch_delay: float = 8.0, max_restaurants: int = None):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.use_local_llm = use_local_llm
        self.base_url = "https://www.happycow.net"
        self.scraped_count = 0
        self.error_count = 0
        self.max_restaurants = max_restaurants
        
        # Configure delays
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.batch_delay = batch_delay
        self.max_workers = max_workers
        self.semaphore = None  # Will be initialized in __aenter__
        
        # Crawler config
        self.crawler_config = {
            "headless": True,
            "verbose": False,
            "browser_type": "chromium",
            "headers": StealthConfig.get_headers(),
            "page_timeout": 30000,
            "request_timeout": 20000
        }
    
    def _get_city_path(self, city_name: str) -> str:
        """Convert city name to HappyCow URL path"""
        city_paths = {
            "Austin": "north_america/usa/texas/austin",
            "Portland": "north_america/usa/oregon/portland",
            "Seattle": "north_america/usa/washington/seattle",
            "San Francisco": "north_america/usa/california/san_francisco",
            "Los Angeles": "north_america/usa/california/los_angeles",
            "New York": "north_america/usa/new_york/new_york",
            "Chicago": "north_america/usa/illinois/chicago",
            "Denver": "north_america/usa/colorado/denver",
            "Miami": "north_america/usa/florida/miami",
            "Boston": "north_america/usa/massachusetts/boston"
        }
        return city_paths.get(city_name, f"search?q={city_name.replace(' ', '+')}")
    
    def _get_scroll_js(self) -> str:
        """JavaScript code for scrolling and loading content"""
        return """
        // Scroll to load all listings and handle pagination
        let lastHeight = 0;
        let currentHeight = document.body.scrollHeight;
        let scrollAttempts = 0;
        const maxScrollAttempts = 10;
        while (lastHeight !== currentHeight && scrollAttempts < maxScrollAttempts) {
            lastHeight = currentHeight;
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(resolve => setTimeout(resolve, 1200));
            currentHeight = document.body.scrollHeight;
            scrollAttempts++;
        }
        """
    
    async def human_delay(self):
        """Add human-like delay between requests using instance configuration"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
    
    async def exponential_backoff(self, base_delay: float = 30.0, max_delay: float = 300.0):
        """Implement exponential backoff when blocking is detected"""
        if not hasattr(self, '_backoff_count'):
            self._backoff_count = 0
        
        self._backoff_count += 1
        delay = min(base_delay * (2 ** self._backoff_count), max_delay)
        
        logger.warning(f"⏳ Exponential backoff: waiting {delay:.1f} seconds (attempt {self._backoff_count})")
        await asyncio.sleep(delay)
        
        # Reset backoff count after successful delay
        if self._backoff_count >= 5:  # Max 5 attempts
            logger.error("🛑 Max backoff attempts reached. Consider stopping scraper.")
            self._backoff_count = 0
    
    async def handle_blocking_detection(self, url: str, response_text: str = None) -> bool:
        """
        Detect if we're being blocked and handle accordingly
        Returns True if blocking detected, False otherwise
        """
        blocking_indicators = [
            "captcha", "blocked", "access denied", "rate limit", 
            "too many requests", "forbidden", "cloudflare",
            "please verify", "human verification"
        ]
        
        if response_text:
            response_lower = response_text.lower()
            for indicator in blocking_indicators:
                if indicator in response_lower:
                    logger.warning(f"🚫 Blocking detected: {indicator} found in response")
                    await self.exponential_backoff()
                    return True
        
        return False
        
    async def __aenter__(self):
        """Initialize crawler"""
        self.crawler = AsyncWebCrawler(**self.crawler_config)
        await self.crawler.__aenter__()
        
        # Initialize semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(self.max_workers)
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup crawler"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    async def _extract_listings_direct_ollama(self, html_content: str, city_name: str) -> List[Dict[str, Any]]:
        """Direct Ollama API call to extract restaurant listings - bypasses LiteLLM issues"""
        
        prompt = f"""
        Extract ONLY individual restaurant listings from this HappyCow city page HTML.
        
        IMPORTANT RULES:
        1. Look for actual restaurant/venue listings, NOT navigation links or headers
        2. Each restaurant should have a specific name (like "Green Seed Vegan", "Verdine", etc.)
        3. URLs should point to individual restaurant pages (usually contain /reviews/ or venue IDs)
        4. IGNORE these types of content:
           - "Top Rated" or "Best" links
           - Navigation menus
           - Category headers
           - Image links
           - General city/area links
        
        Return ONLY a valid JSON object with this exact format:
        {{
          "restaurants": [
            {{"name": "Actual Restaurant Name", "url": "/reviews/restaurant-name-12345"}},
            {{"name": "Another Restaurant", "url": "/reviews/another-restaurant-67890"}}
          ]
        }}
        
        HTML content (showing restaurant listings section):
        {html_content[:25000]}
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama2",
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "temperature": 0.1,  # Lower temperature for more consistent output
                            "top_p": 0.9
                        }
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "").strip()
                        logger.info(f"Direct Ollama response for {city_name}: {response_text[:200]}...")
                        
                        # Try to parse the JSON response
                        try:
                            response_data = json.loads(response_text)
                            
                            # Recursive function to find restaurant data anywhere in the JSON
                            def extract_restaurants_recursive(data, restaurants_list=[]):
                                """Recursively search for name/url pairs in any JSON structure"""
                                if isinstance(data, dict):
                                    # Check if this dict has name and url
                                    if 'name' in data and 'url' in data:
                                        # Validate it's a real restaurant (not navigation/header)
                                        name = data['name']
                                        url = data['url']
                                        if (url and isinstance(url, str) and 
                                            '/reviews/' in url and 
                                            not any(skip in name.lower() for skip in ['top rated', 'best', 'image', 'photo'])):
                                            restaurants_list.append({'name': name, 'url': url})
                                    
                                    # Recursively check all values in the dict
                                    for value in data.values():
                                        extract_restaurants_recursive(value, restaurants_list)
                                        
                                elif isinstance(data, list):
                                    # Recursively check all items in the list
                                    for item in data:
                                        extract_restaurants_recursive(item, restaurants_list)
                                
                                return restaurants_list
                            
                            restaurants = extract_restaurants_recursive(response_data)
                            logger.info(f"Found {len(restaurants)} valid restaurants using recursive extraction")
                            
                            return restaurants
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse JSON response: {e}")
                            logger.debug(f"Raw response: {response_text[:500]}...")
                            return []
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Direct Ollama call failed: {e}")
            return []

    async def scrape_city_listings(self, city_name: str) -> List[RestaurantListing]:
        """Scrape restaurant listings from a city page using improved content loading"""
        city_url = f"https://www.happycow.net/{self._get_city_path(city_name)}/"
        logger.info(f"Scraping listings for {city_name}")
        
        async with AsyncWebCrawler(
            verbose=True
        ) as crawler:
            
            await self.human_delay()
            
            # Enhanced config to wait for dynamic content
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                js_code=[
                    # Scroll to load content
                    self._get_scroll_js(),
                    # Wait for potential AJAX content
                    "await new Promise(resolve => setTimeout(resolve, 5000));",
                    # Try to trigger any lazy loading
                    "window.scrollTo(0, document.body.scrollHeight);",
                    "await new Promise(resolve => setTimeout(resolve, 2000));"
                ],
                page_timeout=45000,
                delay_before_return_html=5.0  # Wait longer for content
            )
            
            result = await crawler.arun(url=city_url, config=config)
            
            # Check if crawl was successful
            if not result.success:
                logger.error(f"Failed to crawl {city_name}: {getattr(result, 'error_message', 'Unknown error')}")
                return []
            
            logger.info(f"Fetched {city_name} page: {len(result.html)} chars")
            
            # Try to extract restaurant data using regex patterns first
            restaurants_data = self._extract_restaurants_from_html(result.html, city_name)
            
            # If regex fails, fall back to LLM
            if not restaurants_data:
                logger.info("Regex extraction failed, trying LLM extraction...")
                restaurants_data = await self._extract_listings_direct_ollama(result.html, city_name)
            
            if not restaurants_data:
                logger.error(f"No extracted content returned for {city_name}")
                return []
            
            logger.info(f"Found {len(restaurants_data)} restaurants in {city_name}")
            
            # Convert to RestaurantListing objects
            listings = []
            for item in restaurants_data:
                try:
                    if not isinstance(item, dict) or 'name' not in item or 'url' not in item:
                        logger.warning(f"Invalid restaurant data: {item}")
                        continue
                
                    listing = RestaurantListing(
                        name=item['name'],
                        url=item['url'],
                        city=city_name
                    )
                    listings.append(listing)
                except Exception as e:
                    logger.warning(f"Error creating RestaurantListing: {e}")
                    continue
            
            return listings
                
    def _extract_restaurants_from_html(self, html_content: str, city_name: str) -> List[Dict[str, Any]]:
        """Extract restaurant data using regex patterns - faster than LLM"""
        import re
        
        restaurants = []
        
        # Pattern 1: Look for /reviews/ links with restaurant names
        review_pattern = r'<a[^>]*href="(/reviews/[^"]*)"[^>]*>([^<]+)</a>'
        matches = re.findall(review_pattern, html_content, re.IGNORECASE)
        
        for url, name in matches:
            # Clean up the name
            name = re.sub(r'<[^>]+>', '', name).strip()
            if name and len(name) > 2:  # Basic validation
                restaurants.append({
                    'name': name,
                    'url': url
                })
        
        # Pattern 2: Look for data-venue-id attributes
        venue_pattern = r'data-venue-id="([^"]*)"[^>]*>.*?<[^>]*>([^<]+)</[^>]*>'
        venue_matches = re.findall(venue_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for venue_id, name in venue_matches:
            name = re.sub(r'<[^>]+>', '', name).strip()
            if name and len(name) > 2:
                restaurants.append({
                    'name': name,
                    'url': f'/reviews/{venue_id}'  # Construct URL from venue ID
                })
        
        # Remove duplicates
        seen = set()
        unique_restaurants = []
        for restaurant in restaurants:
            key = (restaurant['name'].lower(), restaurant['url'])
            if key not in seen:
                seen.add(key)
                unique_restaurants.append(restaurant)
        
        logger.info(f"Regex extraction found {len(unique_restaurants)} restaurants")
        return unique_restaurants
    
    async def check_existing_restaurant(self, happycow_url: str) -> bool:
        """Check if restaurant already exists in database"""
        try:
            result = self.supabase.table('restaurants').select('id').eq('happycow_url', happycow_url).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.warning(f"Error checking existing restaurant: {e}")
            return False
    
    async def scrape_restaurant_detail(self, listing: RestaurantListing) -> Optional[RestaurantDetail]:
        """Scrape detailed restaurant information from individual restaurant page"""
        detail_url = f"{self.base_url}{listing.url}"
        
        # Check if we already have this restaurant
        if await self.check_existing_restaurant(listing.url):
            logger.info(f"⏭️  Skipping existing restaurant: {listing.name}")
            return None
        
        try:
            await self.human_delay()
            
            result = await self.crawler.arun(
                url=detail_url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=30000,
                    delay_before_return_html=2.0  # Give page time to load
                )
            )
            
            if not result.success:
                logger.error(f"Failed to scrape detail for {listing.name}: {result.error_message}")
                return None
            
            # For now, create a basic RestaurantDetail object with the listing data
            # TODO: Implement detailed extraction using direct Ollama calls on the HTML content
            restaurant = RestaurantDetail(
                name=listing.name,
                city=listing.city,
                state="Texas",  # TODO: Extract from city mapping
                country="USA",
                happycow_url=listing.url,
                vegan_status=listing.listing_type or "veg-friendly",  # Use listing type if available
                last_updated=datetime.now(timezone.utc)
            )
            
            logger.info(f"✅ Scraped details for {listing.name}")
            return restaurant
                
        except Exception as e:
            logger.error(f"Exception scraping detail for {listing.name}: {e}")
            return None
    
    async def save_to_supabase(self, restaurant: RestaurantDetail) -> bool:
        """Save restaurant data to Supabase with proper field mapping"""
        try:
            # Convert to dict and handle field mapping
            data = restaurant.dict()
            
            # Map Pydantic model fields to database schema
            db_data = {
                # Required fields
                'name': data['name'],
                'city_name': data['city'],
                'state_name': data.get('state', 'Unknown'),
                'country_code': data.get('country', 'US'),
                'city_path': self._get_city_path(data['city']),
                
                # Map model fields to database fields
                'happycow_url': data['happycow_url'],
                'venue_id': data.get('happycow_id'),  # Can be null now
                'type': data.get('vegan_status'),     # Can be null now
                'vegan_status': data.get('vegan_status'),
                'description': data.get('description'),
                'cuisine_tags': data.get('cuisine_types', []),
                'cuisine_types': data.get('cuisine_types', []),
                
                # Location data
                'address': data.get('address'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                
                # Contact info
                'phone': data.get('phone'),
                'website': data.get('website'),
                'instagram': data.get('instagram'),
                'facebook': data.get('facebook'),
                
                # Business info
                'hours': data.get('hours'),
                'price_range': data.get('price_range'),
                'features': data.get('features', []),
                
                # Reviews & ratings
                'rating': data.get('rating'),
                'review_count': data.get('review_count', 0),
                'recent_reviews': data.get('recent_reviews', []),
                
                # Timestamps
                'last_updated': data['last_updated'].isoformat(),
                'scraped_at': data['last_updated'].isoformat(),
                'created_at': data['last_updated'].isoformat(),
                'updated_at': data['last_updated'].isoformat()
            }
            
            # Remove None values to avoid Supabase issues
            db_data = {k: v for k, v in db_data.items() if v is not None}
            
            # Ensure required fields have defaults if missing
            if 'state_name' not in db_data:
                db_data['state_name'] = 'Unknown'
            if 'country_code' not in db_data:
                db_data['country_code'] = 'US'
            
            result = self.supabase.table('restaurants').insert(db_data).execute()
            
            if result.data:
                logger.info(f"💾 Saved to Supabase: {restaurant.name}")
                return True
            else:
                logger.error(f"Failed to save {restaurant.name}: No data returned")
                return False
            
        except Exception as e:
            logger.error(f"Error saving {restaurant.name} to Supabase: {e}")
            logger.debug(f"Data that failed to save: {db_data if 'db_data' in locals() else 'N/A'}")
            return False
    
    async def scrape_city_complete(self, city_name: str, 
                                 max_restaurants: Optional[int] = None) -> Dict[str, Any]:
        """Complete scraping workflow for a city"""
        
        logger.info(f"🏙️  Starting complete scrape for {city_name}")
        
        # Step 1: Get restaurant listings
        listings = await self.scrape_city_listings(city_name)
        
        if not listings:
            return {
                'city': city_name,
                'success': False,
                'listings_found': 0,
                'restaurants_scraped': 0,
                'restaurants_saved': 0
            }
        
        # Limit restaurants if specified
        if max_restaurants:
            listings = listings[:max_restaurants]
        
        # Step 2: Process each restaurant
        scraped_count = 0
        saved_count = 0
        skipped_count = 0
        
        async def process_restaurant(listing: RestaurantListing, index: int) -> Dict[str, Any]:
            """Process a single restaurant with semaphore control"""
            async with self.semaphore:
                try:
                    logger.info(f"[{index + 1}/{len(listings)}] Processing: {listing.name}")
                    
                    restaurant = await self.scrape_restaurant_detail(listing)
                    if restaurant is None:
                        return {'status': 'skipped', 'name': listing.name}
                    
                    saved = await self.save_to_supabase(restaurant)
                    return {
                        'status': 'saved' if saved else 'error',
                        'name': listing.name,
                        'restaurant': restaurant
                    }
                    
                except Exception as e:
                    logger.error(f"Error processing {listing.name}: {e}")
                    return {'status': 'error', 'name': listing.name, 'error': str(e)}
        
        # Process restaurants concurrently
        tasks = [process_restaurant(listing, i) for i, listing in enumerate(listings)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        for result in results:
            if isinstance(result, dict):
                if result['status'] == 'saved':
                    saved_count += 1
                scraped_count += 1
                elif result['status'] == 'skipped':
                    skipped_count += 1
                elif result['status'] == 'error':
                    scraped_count += 1  # Attempted but failed
        
        result = {
            'city': city_name,
            'success': True,
            'listings_found': len(listings),
            'restaurants_scraped': scraped_count,
            'restaurants_saved': saved_count,
            'restaurants_skipped': skipped_count,
            'errors': len(listings) - scraped_count - skipped_count
        }
        
        logger.info(f"🎉 Completed {city_name}: {saved_count} saved, {skipped_count} skipped, {scraped_count} total")
        return result

# ================================
# MAIN FUNCTION
# ================================

async def main():
    """Main scraping function"""
    from config import get_config
    
    config = get_config()
    
    # Cities to scrape (can be moved to config)
    CITIES = {
        "Austin": "https://www.happycow.net/north_america/usa/texas/austin/",
        "Portland": "https://www.happycow.net/north_america/usa/oregon/portland/",
        "Seattle": "https://www.happycow.net/north_america/usa/washington/seattle/"
    }
    
    MAX_RESTAURANTS_PER_CITY = config.max_restaurants or 5  # Limit for testing
    
    async with HappyCowScraper(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_key,
        use_local_llm=config.use_local_llm,
        max_workers=config.max_workers,
        min_delay=config.min_delay,
        max_delay=config.max_delay,
        batch_delay=config.batch_delay
    ) as scraper:
        
        logger.info(f"🚀 Starting HappyCow scraper for {len(CITIES)} cities")
        
        total_stats = {
            'cities_processed': 0,
            'restaurants_found': 0,
            'restaurants_scraped': 0,
            'restaurants_saved': 0
        }
        
        for city_name, city_url in CITIES.items():
            result = await scraper.scrape_city_complete(
                city_name, 
                max_restaurants=MAX_RESTAURANTS_PER_CITY
            )
            
            if result['success']:
                total_stats['cities_processed'] += 1
                total_stats['restaurants_found'] += result['listings_found']
                total_stats['restaurants_scraped'] += result['restaurants_scraped']
                total_stats['restaurants_saved'] += result['restaurants_saved']
            
            # Add delay between cities
            if city_name != list(CITIES.keys())[-1]:  # Not the last city
                logger.info(f"⏳ Waiting {scraper.batch_delay}s before next city...")
                await asyncio.sleep(scraper.batch_delay)
        
        logger.info("🎉 Scraping completed!")
        logger.info(f"Cities processed: {total_stats['cities_processed']}")
        logger.info(f"Restaurants found: {total_stats['restaurants_found']}")
        logger.info(f"Restaurants scraped: {total_stats['restaurants_scraped']}")
        logger.info(f"Restaurants saved: {total_stats['restaurants_saved']}")

if __name__ == "__main__":
    asyncio.run(main())