"""
HappyCow Restaurant Scraper
Scrapes restaurant data from HappyCow.net and stores in Supabase
"""

import asyncio
import json
import logging
import random
import re
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

# Third-party imports
from pydantic import BaseModel, Field
from supabase import create_client, Client
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

# Local imports
from enhanced_extraction_engine import EnhancedExtractionEngine
from review_extraction_engine import ReviewExtractionEngine, RestaurantReview
from page_type_detector import detect_page_type, PageType
from css_selector_config import CSSConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Complete restaurant data model matching Supabase schema exactly"""
    # Basic Info
    name: str = Field(..., description="Restaurant name")
    description: Optional[str] = Field(None, description="Restaurant description")
    vegan_status: Optional[str] = Field(None, description="Fully vegan, vegan options, etc.")
    
    # Location
    address: Optional[str] = Field(None, description="Full street address")
    city_name: str = Field(..., description="City name") # Match DB field name
    state: Optional[str] = Field(None, description="State/Province") # Match DB field name
    country: Optional[str] = Field(None, description="Country") # Match DB field name
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
    
    # Cuisine (using both fields to match DB)
    cuisine_types: List[str] = Field(default_factory=list, description="List of cuisine types")
    cuisine_tags: List[str] = Field(default_factory=list, description="Cuisine tags (legacy)")
    
    # Reviews & Ratings
    rating: Optional[float] = Field(None, description="Average rating 0-5")
    review_count: Optional[int] = Field(None, description="Number of reviews")
    recent_reviews: List[Dict[str, Any]] = Field(default_factory=list, description="Recent review excerpts")
    
    # Meta
    happycow_url: str = Field(..., description="Full HappyCow URL")
    happycow_id: Optional[str] = Field(None, description="HappyCow venue ID")
    venue_id: Optional[str] = Field(None, description="Venue ID from scraping")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Additional DB fields for compatibility
    city_path: Optional[str] = Field(None, description="City path for URL generation")
    full_path: Optional[str] = Field(None, description="Full path from city_queue (foreign key)")
    state_name: Optional[str] = Field(None, description="State name (legacy)")
    country_code: Optional[str] = Field("US", description="Country code")
    type: Optional[str] = Field(None, description="Restaurant type (legacy)")  # Maps to vegan_status

@dataclass
class StealthConfig:
    """Configuration for human-like browsing behavior"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]
    
    # Free proxy list (rotate through these)
    FREE_PROXIES = [
        # Add working proxies here - these are examples
        # "http://proxy1.example.com:8080",
        # "http://proxy2.example.com:3128",
        # "socks5://proxy3.example.com:1080"
    ]
    
    # Balanced delays - reduced for faster scraping while avoiding CAPTCHA
    MIN_DELAY = 2.0  # Reduced from 5.0
    MAX_DELAY = 6.0  # Reduced from 12.0
    BATCH_DELAY = 8.0  # Reduced from 20.0
    
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
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    
    @staticmethod
    def get_random_proxy() -> Optional[str]:
        """Get a random proxy from the list"""
        if StealthConfig.FREE_PROXIES:
            return random.choice(StealthConfig.FREE_PROXIES)
        return None

class HappyCowScraper:
    """Complete HappyCow scraper with Supabase integration"""
    
    def __init__(self, supabase_url: str, supabase_key: str, use_local_llm: bool = True, 
                 max_workers: int = 3, min_delay: float = 2.0, max_delay: float = 5.0, 
                 batch_delay: float = 8.0, max_restaurants: Optional[int] = None, proxy_url: Optional[str] = None):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
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
        self.proxy_url = proxy_url
        self.supabase: Optional[Client] = None
        self.crawlers: List[AsyncWebCrawler] = []
        self._session_semaphore = asyncio.Semaphore(max_workers)
        
        # Crawler config
        self.crawler_config = {
            "headless": True,
            "verbose": False,
            "browser_type": "chromium",
            "headers": StealthConfig.get_headers(),
            "page_timeout": 30000,
            "request_timeout": 20000
        }
        
        # Initialize extraction engines
        self.extraction_engine = EnhancedExtractionEngine()
        self.review_engine = ReviewExtractionEngine()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def _get_city_path(self, city_name: str) -> str:
        """Convert city name to HappyCow URL path"""
        # State abbreviation mapping
        state_abbreviations = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia',
            'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa',
            'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
            'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
            'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont',
            'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
        }
        
        # First try to look up in database
        try:
            if hasattr(self, 'supabase') and self.supabase:
                # Check if city_name looks like a full_path (contains underscores, lowercase)
                if '_' in city_name and city_name.islower():
                    # Try full_path lookup first
                    result = self.supabase.table('city_queue').select('url, city, state').eq('full_path', city_name).execute()
                    if result.data and len(result.data) > 0:
                        self.logger.info(f"Found city by full_path '{city_name}': {result.data[0]['city']}, {result.data[0]['state']}")
                        url = result.data[0]['url']
                        return url.replace('https://www.happycow.net/', '').rstrip('/')
                
                # Try exact city name match
                result = self.supabase.table('city_queue').select('url').eq('city', city_name).execute()
                if result.data and len(result.data) > 0:
                    url = result.data[0]['url']
                    # Extract path from URL: https://www.happycow.net/north_america/usa/texas/dallas/ -> north_america/usa/texas/dallas
                    return url.replace('https://www.happycow.net/', '').rstrip('/')
                
                # If city_name contains comma, parse as "City, State"
                if ',' in city_name:
                    parts = city_name.split(',', 1)
                    city_part = parts[0].strip()
                    state_part = parts[1].strip()
                    
                    # Convert state abbreviation to full name if needed
                    if state_part.upper() in state_abbreviations:
                        state_part = state_abbreviations[state_part.upper()]
                    
                    # Try to find city with matching state
                    result = self.supabase.table('city_queue').select('url, city, state').eq('city', city_part).execute()
                    if result.data:
                        # If multiple cities with same name, try to match by state
                        for row in result.data:
                            if row['state'].lower() == state_part.lower():
                                url = row['url']
                                return url.replace('https://www.happycow.net/', '').rstrip('/')
                        
                        # If no state match, use the first one and log a warning
                        logger.warning(f"Multiple cities named '{city_part}' found, using first match: {result.data[0]['city']}, {result.data[0]['state']}")
                        url = result.data[0]['url']
                        return url.replace('https://www.happycow.net/', '').rstrip('/')
                
                # Try without state part (e.g., "Dallas" instead of "Dallas, Texas")
                city_name_short = city_name.split(',')[0].strip()
                result = self.supabase.table('city_queue').select('url, city, state').eq('city', city_name_short).execute()
                if result.data:
                    if len(result.data) > 1:
                        logger.warning(f"Multiple cities named '{city_name_short}' found, using first match: {result.data[0]['city']}, {result.data[0]['state']}")
                    url = result.data[0]['url']
                    return url.replace('https://www.happycow.net/', '').rstrip('/')
        except Exception as e:
            logger.error(f"Database lookup failed for '{city_name}': {e}")
            # If database lookup fails, fall back to hardcoded paths
            pass
        
        # Fall back to hardcoded paths
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
    
    async def human_delay(self):
        """Add human-like delay between requests using instance configuration"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
        
    async def __aenter__(self):
        """Async context manager entry"""
        # Initialize Supabase client
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize crawler with proxy support
        self.crawler = await self._create_crawler_with_stealth(self.proxy_url)
        
        logger.info(f"🚀 HappyCow scraper initialized with {self.max_workers} workers")
        if self.proxy_url:
            logger.info(f"🌐 Using proxy: {self.proxy_url}")
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup crawler"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    def _extract_restaurants_from_html(self, html_content: str, city_name: str) -> List[Dict[str, Any]]:
        """Extract restaurant data using regex patterns - faster than LLM"""
        restaurants = []
        
        # Pattern 1: Look for restaurant names in h4 tags with /reviews/ links, EXCLUDING /update URLs
        # Matches: <h4><a href="/reviews/restaurant-name-city-id">Restaurant Name</a></h4>
        review_pattern = r'<h4[^>]*><a[^>]*href="(/reviews/[^"]*)"[^>]*>([^<]+)</a></h4>'
        matches = re.findall(review_pattern, html_content, re.IGNORECASE)
        
        for url, name in matches:
            # 🚫 SKIP /update URLs - these are edit forms, not restaurant pages
            if url.endswith('/update') or '/update/' in url:
                logger.debug(f"Skipping update URL: {url}")
                continue
                
            # Clean up the name
            name = re.sub(r'<[^>]+>', '', name).strip()
            if name and len(name) > 2:  # Basic validation
                restaurants.append({
                    'name': name,
                    'url': url
                })
        
        # Remove duplicates
        seen = set()
        unique_restaurants = []
        for restaurant in restaurants:
            key = (restaurant['name'].lower(), restaurant['url'])
            if key not in seen:
                seen.add(key)
                unique_restaurants.append(restaurant)
        
        logger.info(f"Regex extraction found {len(unique_restaurants)} restaurants (filtered out /update URLs)")
        return unique_restaurants

    async def scrape_city_listings(self, city_name: str, city_path: Optional[str] = None) -> List[RestaurantListing]:
        """Scrape restaurant listings from a city page with enhanced anti-detection"""
        city_url = f"https://www.happycow.net/{city_path or self._get_city_path(city_name)}/"
        logger.info(f"Scraping listings for {city_name}")
        
        # Enhanced human delay with variance
        await self.enhanced_human_delay()
        
        # 🔍 DETECT PAGE TYPE AND GET APPROPRIATE CSS SELECTORS
        page_type = detect_page_type(city_url)
        logger.info(f"🎯 Detected page type: {page_type.value} for {city_url}")
        
        # Get page-type-specific crawl configuration
        crawl_config_dict = CSSConfigManager.get_crawl_config_for_page_type(page_type)
        
        # Use the stealth config with page-type-specific selectors
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            user_agent=random.choice(StealthConfig.USER_AGENTS),
            wait_for=f"css:{crawl_config_dict['wait_for']}",  # 🎯 USE CORRECT SELECTORS!
            js_code="""
                // Remove ALL automation indicators
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                // Add realistic browser properties
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
            """,
            css_selector="body",
            screenshot=False,
            verbose=False
        )
        
        logger.info(f"🔧 Using selectors for {page_type.value}: {crawl_config_dict['wait_for']}")
        
        result = await self.crawler.arun(url=city_url, config=config)
        
        if not result.success:
            logger.error(f"Failed to crawl {city_name}: {getattr(result, 'error_message', 'Unknown crawler error')}")
            return []
        
        logger.info(f"Fetched {city_name} page: {len(result.html)} chars")
        
        # Check for blocking indicators in content
        if self.detect_blocking_in_content(result.html):
            logger.warning(f"🚫 Blocking detected in {city_name} page content")
            await self.exponential_backoff()
            return []
        
        # Extract restaurant data using regex patterns
        restaurants_data = self._extract_restaurants_from_html(result.html, city_name)
        
        if not restaurants_data:
            logger.error(f"No restaurants found for {city_name}")
            return []
        
        # Convert to RestaurantListing objects
        listings = []
        for item in restaurants_data:
            try:
                listing = RestaurantListing(
                    name=item['name'],
                    url=item['url'],
                    city=city_name,
                    listing_type=None,  # Will be determined from individual page
                    is_featured=False,  # Default value
                    is_new=False       # Default value
                )
                listings.append(listing)
            except Exception as e:
                logger.warning(f"Error creating RestaurantListing: {e}")
                continue
                
        return listings

    async def check_existing_restaurant(self, happycow_url: str) -> bool:
        """Check if restaurant already exists in database"""
        try:
            result = self.supabase.table('restaurants').select('id').eq('happycow_url', happycow_url).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking existing restaurant: {e}")
            return False
    
    async def save_to_supabase(self, restaurant: RestaurantDetail) -> bool:
        """Save restaurant data to Supabase"""
        try:
            # Convert to dict and prepare for database
            restaurant_dict = restaurant.model_dump()
            
            # Convert datetime to string for JSON serialization
            if 'last_updated' in restaurant_dict:
                restaurant_dict['last_updated'] = restaurant_dict['last_updated'].isoformat()
            
            # 🔧 FIX: Send lists directly to Supabase - PostgreSQL expects actual arrays, not JSON strings
            # Convert complex objects to JSON strings, but keep arrays as arrays
            json_fields = ['recent_reviews', 'hours']  # Only complex objects need JSON serialization
            for field in json_fields:
                if field in restaurant_dict and restaurant_dict[field]:
                    restaurant_dict[field] = json.dumps(restaurant_dict[field])
            
            # Ensure array fields are proper Python lists (not JSON strings)
            array_fields = ['features', 'cuisine_types', 'cuisine_tags']
            for field in array_fields:
                if field in restaurant_dict and restaurant_dict[field]:
                    # Ensure it's a list, not a JSON string
                    if isinstance(restaurant_dict[field], str):
                        try:
                            # If it's a JSON string, parse it back to a list
                            restaurant_dict[field] = json.loads(restaurant_dict[field])
                        except json.JSONDecodeError:
                            # If it's not valid JSON, treat as single item
                            restaurant_dict[field] = [restaurant_dict[field]]
                    elif not isinstance(restaurant_dict[field], list):
                        # Convert other types to list
                        restaurant_dict[field] = [restaurant_dict[field]]
            
            # Remove None values to avoid database issues
            db_data = {k: v for k, v in restaurant_dict.items() if v is not None}
            
            # Remove None values
            db_data = {k: v for k, v in db_data.items() if v is not None}
            
            result = self.supabase.table('restaurants').insert(db_data).execute()
            
            if result.data:
                logger.info(f"💾 Saved to Supabase: {restaurant.name}")
                return True
            else:
                logger.error(f"Failed to save {restaurant.name}")
                return False
            
        except Exception as e:
            logger.error(f"Error saving {restaurant.name} to Supabase: {e}")
            return False
    
    async def save_reviews_to_supabase(self, reviews: List[RestaurantReview], restaurant_id: str, happycow_url: str) -> int:
        """Save reviews to Supabase and return count of saved reviews"""
        if not reviews:
            return 0
            
        saved_count = 0
        
        for review in reviews:
            try:
                # Convert review to dict for Supabase
                review_dict = {
                    'restaurant_id': restaurant_id,
                    'happycow_restaurant_url': happycow_url,  # ✅ FIXED: Use correct database field name
                    'review_id': review.review_id,
                    'author_username': review.author.username,
                    'author_profile_url': review.author.profile_url,
                    'author_avatar_url': review.author.avatar_url,
                    'author_points': review.author.points,
                    'author_dietary_preference': review.author.dietary_preference,
                    'author_is_ambassador': review.author.is_ambassador,
                    'rating': review.rating,
                    'review_date': review.date,  # ✅ FIXED: Use review.date not review.review_date
                    'title': review.title,
                    'content': review.content,
                    'language': review.language,
                    'helpful_count': review.helpful_count,
                    'review_timestamp': review.date_timestamp  # ✅ FIXED: Use review_timestamp not date_timestamp
                }
                
                # Remove None values
                review_dict = {k: v for k, v in review_dict.items() if v is not None}
                
                # Insert review (ignore duplicates)
                result = self.supabase.table('reviews').insert(review_dict).execute()
                
                if result.data:
                    saved_count += 1
                    logger.debug(f"💬 Saved review {review.review_id} by {review.author.username}")
                    
            except Exception as e:
                logger.warning(f"Error saving review {review.review_id}: {e}")
                continue
        
        logger.info(f"💬 Saved {saved_count}/{len(reviews)} reviews to database")
        return saved_count
    
    async def scrape_city_complete(self, city_name: str, max_restaurants: Optional[int] = None, 
                                 city_path: Optional[str] = None, city_task: Optional[Any] = None) -> Dict[str, Any]:
        """Complete scraping workflow for a city"""
        logger.info(f"🏙️  Starting complete scrape for {city_name}")
        
        # Extract city/state data from city_task if available
        city_state_data = {}
        if city_task:
            city_state_data = {
                'city': city_task.city,
                'state': city_task.state, 
                'full_path': city_task.full_path,
                'city_path': city_path or city_task.full_path
            }
            logger.info(f"🗺️  Using city queue data: {city_task.city}, {city_task.state} ({city_task.full_path})")
        else:
            # Fallback for manual cities - try to extract state from city_name
            city_state_data = {
                'city': city_name,
                'state': None,  # Will need to be handled
                'full_path': city_path or self._get_city_path(city_name),
                'city_path': city_path or self._get_city_path(city_name)
            }
            logger.warning(f"⚠️  No city queue data available for {city_name} - state will be unknown")
        
        # Step 1: Get restaurant listings
        try:
            listings = await self.scrape_city_listings(city_name, city_path)
        except Exception as e:
            logger.error(f"Exception during city listings scraping for {city_name}: {e}")
            return {
                'city': city_name,
                'success': False,
                'error': f"Exception during listings scraping: {str(e)}",
                'listings_found': 0,
                'restaurants_scraped': 0,
                'restaurants_saved': 0
            }
        
        if not listings:
            logger.error(f"No listings found for {city_name} - check if the city path is correct or if the site is blocking us")
            return {
                'city': city_name,
                'success': False,
                'error': 'No restaurant listings found - city may not exist or site may be blocking requests',
                'listings_found': 0,
                'restaurants_scraped': 0,
                'restaurants_saved': 0
            }
        
        # Limit restaurants if specified
        if max_restaurants:
            listings = listings[:max_restaurants]
        
        # Step 2: Process each restaurant
        saved_count = 0
        skipped_count = 0
        
        for i, listing in enumerate(listings):
            logger.info(f"[{i + 1}/{len(listings)}] Processing: {listing.name}")
            
            # Get restaurant details and reviews in one go - PASS CITY STATE DATA
            result = await self.scrape_individual_restaurant(listing, city_state_data)
            if result is None:
                skipped_count += 1
                continue
            
            # result is now a tuple of (restaurant_data, reviews_list)
            if isinstance(result, tuple):
                restaurant, reviews = result
            else:
                # Backward compatibility - if just restaurant data returned
                restaurant = result
                reviews = []
            
            # Save restaurant to database
            saved = await self.save_to_supabase(restaurant)
            if saved:
                saved_count += 1
                
                # Save reviews if we have any
                if reviews:
                    try:
                        # Get the restaurant ID from database for review linking
                        db_result = self.supabase.table('restaurants').select('id').eq('happycow_url', restaurant.happycow_url).execute()
                        if db_result.data:
                            restaurant_id = db_result.data[0]['id']
                            review_count = await self.save_reviews_to_supabase(reviews, restaurant_id, restaurant.happycow_url)
                            logger.info(f"📝 Saved {review_count} reviews for {restaurant.name}")
                        else:
                            logger.warning(f"Could not find restaurant ID for {restaurant.name} to save reviews")
                    except Exception as e:
                        logger.warning(f"Error saving reviews for {restaurant.name}: {e}")
        
        result = {
            'city': city_name,
            'success': True,
            'listings_found': len(listings),
            'restaurants_scraped': len(listings) - skipped_count,
            'restaurants_saved': saved_count,
            'restaurants_skipped': skipped_count
        }
        
        logger.info(f"🎉 Completed {city_name}: {saved_count} saved, {skipped_count} skipped")
        return result

    async def handle_http_errors(self, response_status: int, url: str) -> bool:
        """Handle HTTP errors and implement backoff strategies"""
        if response_status in [403, 429, 503]:
            logger.warning(f"🚫 Rate limited or blocked (HTTP {response_status}) for {url}")
            await self.exponential_backoff()
            return True
        elif response_status in [404, 410]:
            logger.warning(f"⚠️  Resource not found (HTTP {response_status}) for {url}")
            return False
        elif response_status >= 500:
            logger.warning(f"🔧 Server error (HTTP {response_status}) for {url}")
            await self.exponential_backoff(base_delay=10.0)
            return True
        return False

    async def exponential_backoff(self, base_delay: float = 60.0, max_delay: float = 600.0):
        """Implement exponential backoff when blocking is detected - more aggressive for CAPTCHA"""
        if not hasattr(self, '_backoff_count'):
            self._backoff_count = 0
        
        self._backoff_count += 1
        delay = min(base_delay * (2 ** self._backoff_count), max_delay)
        
        logger.warning(f"⏳ Exponential backoff: waiting {delay:.1f} seconds (attempt {self._backoff_count})")
        logger.warning(f"🛡️  Anti-bot protection detected. Being more patient...")
        
        # Add some randomness to the delay to avoid predictable patterns
        jitter = random.uniform(0.8, 1.2)
        actual_delay = delay * jitter
        
        await asyncio.sleep(actual_delay)
        
        # Reset backoff count after successful delay
        if self._backoff_count >= 3:  # Reduced from 5 to 3 attempts
            logger.error("🛑 Max backoff attempts reached. Consider waiting longer before retrying.")
            self._backoff_count = 0
            # Wait an additional 10 minutes before giving up
            logger.warning("😴 Taking a 10-minute break to cool down...")
            await asyncio.sleep(600)  # 10 minutes

    def detect_blocking_in_content(self, html_content: str) -> bool:
        """Detect if we're being blocked based on page content"""
        # More specific blocking indicators to avoid false positives
        blocking_indicators = [
            "access denied", "rate limit exceeded", "too many requests", 
            "forbidden", "cloudflare challenge", "security check required",
            "unusual traffic detected", "automated requests blocked",
            "please complete the captcha", "human verification required"
        ]
        
        content_lower = html_content.lower()
        for indicator in blocking_indicators:
            if indicator in content_lower:
                logger.warning(f"🚫 Blocking detected: '{indicator}' found in page content")
                return True
                
        # Check for specific CAPTCHA challenge pages (not just presence of reCAPTCHA elements)
        if "challenge.cloudflare.com" in content_lower or "captcha-delivery.com" in content_lower:
            logger.warning(f"🚫 Blocking detected: CAPTCHA challenge page")
            return True
            
        return False

    async def enhanced_human_delay(self):
        """Enhanced human-like delay with realistic variance to avoid CAPTCHA"""
        # Base delay with more realistic human patterns
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # Add occasional much longer pauses (human behavior - checking phone, getting coffee, etc.)
        if random.random() < 0.2:  # 20% chance of longer pause
            base_delay += random.uniform(10.0, 30.0)
            logger.info(f"☕ Taking a coffee break: {base_delay:.1f}s")
        elif random.random() < 0.1:  # 10% chance of very long pause
            base_delay += random.uniform(30.0, 60.0)
            logger.info(f"📱 Checking phone: {base_delay:.1f}s")
        
        # Add micro-delays to simulate human reading and scrolling
        reading_time = random.uniform(1.0, 4.0)  # Increased reading time
        thinking_time = random.uniform(0.5, 2.0)  # Time to "think" about what to click
        
        total_delay = base_delay + reading_time + thinking_time
        
        # Ensure minimum delay of 8 seconds to be very conservative
        total_delay = max(total_delay, 8.0)
        
        logger.info(f"⏱️  Human delay: {total_delay:.1f}s")
        await asyncio.sleep(total_delay)

    async def scrape_individual_restaurant(self, listing: RestaurantListing, city_state_data: Dict[str, Any]):
        """Scrape detailed information from an individual restaurant page using enhanced extraction"""
        # Check if restaurant already exists in database
        if await self.check_existing_restaurant(f"https://www.happycow.net{listing.url}"):
            logger.info(f"⏭️  Skipping existing restaurant: {listing.name}")
            return None
            
        restaurant_url = f"https://www.happycow.net{listing.url}"
        logger.info(f"🍽️  Scraping individual restaurant: {listing.name}")
        
        # Enhanced human delay before individual page requests
        await self.enhanced_human_delay()
        
        # 🔍 DETECT PAGE TYPE AND GET APPROPRIATE CSS SELECTORS
        page_type = detect_page_type(restaurant_url)
        logger.info(f"🎯 Detected page type: {page_type.value} for {restaurant_url}")
        
        # Get page-type-specific crawl configuration
        crawl_config_dict = CSSConfigManager.get_crawl_config_for_page_type(page_type)
        
        # Use the stealth config with page-type-specific selectors
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            user_agent=random.choice(StealthConfig.USER_AGENTS),
            wait_for=f"css:{crawl_config_dict['wait_for']}",  # 🎯 USE CORRECT SELECTORS!
            js_code="""
                // Remove ALL automation indicators
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                // Add realistic browser properties
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
            """,
            verbose=False
        )
        
        logger.info(f"🎯 Using selectors for {page_type.value}: {crawl_config_dict['wait_for']}")
        
        try:
            result = await self.crawler.arun(url=restaurant_url, config=config)
            
            if not result.success:
                logger.error(f"Failed to crawl restaurant page: {restaurant_url}")
                return None
            
            # Extract restaurant data using the enhanced extraction engine
            extracted_data = await self.extraction_engine.extract_restaurant_data(restaurant_url, result.html)
            
            if not extracted_data:
                logger.warning(f"No data extracted for {listing.name}")
                return None
            
            # Convert to RestaurantDetail model - PASS CITY STATE DATA
            restaurant_data = self._convert_extracted_data_to_model(extracted_data, listing, city_state_data)
            
            if not restaurant_data:
                logger.error(f"Failed to convert extracted data to model for {listing.name}")
                return None
            
            logger.info(f"✅ Successfully extracted restaurant data for {listing.name}")
            
            # Extract reviews from the same page
            reviews = []
            try:
                reviews = self.review_engine.extract_reviews_from_html(result.html)
                if reviews:
                    logger.info(f"📝 Extracted {len(reviews)} reviews for {listing.name}")
                    # Store reviews in the restaurant data for summary
                    restaurant_data.recent_reviews = [
                        {
                            'author': review.author.username,
                            'rating': review.rating,
                            'title': review.title,
                            'content': review.content[:200] + '...' if len(review.content) > 200 else review.content,
                            'date': review.date if review.date else None  # ✅ FIXED: Use review.date not review.review_date
                        }
                        for review in reviews[:5]  # Store first 5 reviews as summary
                    ]
                else:
                    logger.info(f"📝 No reviews found for {listing.name}")
            except Exception as e:
                logger.warning(f"Error extracting reviews for {listing.name}: {e}")
            
            # Return both restaurant data and reviews
            return (restaurant_data, reviews)
            
        except Exception as e:
            logger.error(f"Error scraping restaurant {listing.name}: {e}")
            return None

    def _convert_extracted_data_to_model(self, extracted_data: Dict[str, Any], listing: RestaurantListing, city_state_data: Dict[str, Any]) -> Optional[RestaurantDetail]:
        """Convert extracted data dictionary to RestaurantDetail model"""
        try:
            # Start with extracted data and fill in missing required fields
            model_data = extracted_data.copy()
            
            # 🔍 DEBUG: Log what we have before name assignment
            self.logger.info(f"🔍 DEBUG - extracted_data.get('name'): {extracted_data.get('name')}")
            self.logger.info(f"🔍 DEBUG - listing.name: {listing.name}")
            
            # Ensure required fields are present
            model_data['name'] = model_data.get('name') or listing.name
            
            # 🔍 DEBUG: Log final name
            self.logger.info(f"🔍 DEBUG - Final model_data['name']: {model_data['name']}")
            model_data['city_name'] = listing.city
            model_data['happycow_url'] = f"https://www.happycow.net{listing.url}"
            model_data['last_updated'] = datetime.now(timezone.utc)
            
            # 🔧 FIX: Use city_state_data for proper state and path information
            model_data['state'] = city_state_data.get('state')  # From city_queue
            model_data['state_name'] = city_state_data.get('state')  # Same as state for compatibility
            model_data['city_path'] = city_state_data.get('city_path')  # From city_queue 
            model_data['full_path'] = city_state_data.get('full_path')  # Add full_path for FK relationship
            
            # Set defaults for other required fields
            if 'country' not in model_data or not model_data['country']:
                model_data['country'] = 'USA'
            if 'country_code' not in model_data or not model_data['country_code']:
                model_data['country_code'] = 'US'
            
            # Set additional fields for database compatibility
            model_data['type'] = model_data.get('vegan_status')
            
            # Ensure arrays are properly formatted
            def convert_to_list(value):
                """Convert various formats to proper list"""
                if isinstance(value, list):
                    return value
                
                if isinstance(value, str):
                    # Skip empty or whitespace-only strings
                    if not value.strip():
                        return []
                    
                    # Skip obvious HTML content (contains < or >)
                    if '<' in value or '>' in value or len(value) > 1000:
                        self.logger.warning(f"Skipping HTML-like content in array field: {value[:100]}...")
                        return []
                    
                    # Handle common array string formats
                    try:
                        # Remove extra whitespace and normalize
                        value = value.strip()
                        
                        # Handle JSON-like arrays
                        if value.startswith('[') and value.endswith(']'):
                            # Try to parse as JSON
                            try:
                                parsed = json.loads(value)
                                if isinstance(parsed, list):
                                    return [str(item).strip() for item in parsed if str(item).strip()]
                            except json.JSONDecodeError:
                                # If JSON parsing fails, split by comma and clean
                                inner = value[1:-1]  # Remove brackets
                                return [item.strip().strip('"\'') for item in inner.split(',') if item.strip().strip('"\'')]
                        
                        # Handle comma-separated values
                        if ',' in value:
                            return [item.strip().strip('"\'') for item in value.split(',') if item.strip().strip('"\'')]
                        
                        # Single value
                        return [value]
                        
                    except Exception as e:
                        self.logger.warning(f"Error converting string to list: {e}")
                        return [str(value)]
                
                # Convert other types to string and wrap in list
                if value is not None:
                    return [str(value)]
                
                return []

            # Apply array conversion to relevant fields
            for array_field in ['cuisine_types', 'features']:
                if array_field in model_data:
                    original_value = model_data[array_field]
                    converted_value = convert_to_list(original_value)
                    model_data[array_field] = converted_value
                    self.logger.info(f"🔄 Converted {array_field}: {original_value} -> {converted_value}")
            
            # Copy cuisine_types to cuisine_tags for compatibility
            if model_data['cuisine_types'] and not model_data['cuisine_tags']:
                model_data['cuisine_tags'] = model_data['cuisine_types'].copy()
            
            # Ensure numeric fields have proper defaults only if not extracted
            if 'rating' not in model_data:
                model_data['rating'] = None
            if 'review_count' not in model_data:
                model_data['review_count'] = None
            
            # Handle hours field - convert to dict if it's a string
            if isinstance(model_data.get('hours'), str):
                model_data['hours'] = {'raw': model_data['hours']}
            elif not isinstance(model_data.get('hours'), dict):
                model_data['hours'] = None
            
            return RestaurantDetail(**model_data)
            
        except Exception as e:
            self.logger.error(f"Error converting extracted data to model: {e}")
            self.logger.debug(f"Extracted data: {extracted_data}")
            return None

    async def _create_crawler_with_stealth(self, proxy_url: Optional[str] = None) -> AsyncWebCrawler:
        """Create a crawler with enhanced stealth configuration"""
        # Use provided proxy or get random proxy
        proxy = proxy_url or StealthConfig.get_random_proxy()
        
        # Enhanced browser arguments for stealth
        browser_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            
            # Anti-detection flags
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            
            # Make it look like a real browser
            "--window-size=1920,1080",
            "--start-maximized",
            "--disable-infobars",
            "--disable-notifications",
            "--disable-popup-blocking",
            "--disable-save-password-bubble",
            
            # Add realistic browser flags
            "--enable-automation=false",
            "--disable-browser-side-navigation",
            "--no-zygote",
            "--single-process",
        ]
        
        # Add proxy if available
        if proxy:
            logger.info(f"🌐 Using proxy: {proxy}")
            browser_args.append(f"--proxy-server={proxy}")
            
            # For authenticated proxies like Decodo, we need to handle auth differently
            if "@" in proxy:
                # Format: http://username:password@host:port
                logger.info("🔐 Using authenticated proxy")
        
        # Store configuration for use in arun() calls
        self.stealth_config = CrawlerRunConfig(
            user_agent=random.choice(StealthConfig.USER_AGENTS),
            wait_for="css:.main-content",
            delay_before_return_html=random.uniform(2.0, 5.0),
            js_code="""
                // Remove ALL automation indicators
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                // Add realistic browser properties
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
                
                // Simulate human mouse and scroll behavior
                let mouseX = Math.random() * window.innerWidth;
                let mouseY = Math.random() * window.innerHeight;
                
                // Add mouse movement event listeners
                document.addEventListener('mousemove', (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                });
                
                // Random human-like scrolling
                function humanScroll() {
                    const scrollAmount = Math.random() * 200 + 100;
                    const scrollDelay = Math.random() * 1000 + 500;
                    
                    setTimeout(() => {
                        window.scrollBy(0, scrollAmount);
                        if (Math.random() > 0.7) humanScroll(); // 30% chance to scroll again
                    }, scrollDelay);
                }
                
                // Start human behavior after page load
                setTimeout(() => {
                    humanScroll();
                    
                    // Simulate reading time
                    setTimeout(() => {
                        if (Math.random() > 0.5) {
                            window.scrollTo(0, 0); // Sometimes scroll back to top
                        }
                    }, Math.random() * 3000 + 2000);
                }, Math.random() * 2000 + 1000);
                
                // Add realistic timing
                const originalSetTimeout = window.setTimeout;
                window.setTimeout = function(fn, delay) {
                    return originalSetTimeout(fn, delay + Math.random() * 100);
                };
            """,
            css_selector="body",
            screenshot=False,
            verbose=False
        )
        
        # Create crawler with browser arguments (no config here)
        return AsyncWebCrawler(
            headless=True,
            browser_type="chromium", 
            chrome_args=browser_args
        )

    async def reset_session(self):
        """Reset browser session to clear any bot detection flags"""
        if hasattr(self, 'crawler') and self.crawler:
            try:
                await self.crawler.__aexit__(None, None, None)
            except:
                pass
        
        # Create fresh crawler with new session
        self.crawler = await self._create_crawler_with_stealth(self.proxy_url)
        logger.info("🔄 Browser session reset - fresh start") 