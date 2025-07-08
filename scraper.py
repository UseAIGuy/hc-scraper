"""
HappyCow Restaurant Scraper
Scrapes restaurant data from HappyCow.net and stores in Supabase
"""

import asyncio
import json
import logging
import random
import aiohttp
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Third-party imports
from pydantic import BaseModel, Field
from supabase import create_client, Client
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

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
    state_name: Optional[str] = Field(None, description="State name (legacy)")
    country_code: Optional[str] = Field("US", description="Country code")
    type: Optional[str] = Field(None, description="Restaurant type (legacy)")  # Maps to vegan_status

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

class HappyCowScraper:
    """Complete HappyCow scraper with Supabase integration"""
    
    def __init__(self, supabase_url: str, supabase_key: str, use_local_llm: bool = True, 
                 max_workers: int = 3, min_delay: float = 2.0, max_delay: float = 5.0, 
                 batch_delay: float = 8.0, max_restaurants: Optional[int] = None):
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
    
    async def human_delay(self):
        """Add human-like delay between requests using instance configuration"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
        
    async def __aenter__(self):
        """Initialize crawler"""
        self.crawler = AsyncWebCrawler(verbose=True)
        await self.crawler.__aenter__()
        
        # Initialize semaphore for concurrency control
        self.semaphore = asyncio.Semaphore(self.max_workers)
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup crawler"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

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

    async def scrape_city_listings(self, city_name: str, city_path: Optional[str] = None) -> List[RestaurantListing]:
        """Scrape restaurant listings from a city page with enhanced anti-detection"""
        city_url = f"https://www.happycow.net/{city_path or self._get_city_path(city_name)}/"
        logger.info(f"Scraping listings for {city_name}")
        
        # Enhanced human delay with variance
        await self.enhanced_human_delay()
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0
        )
        
        result = await self.crawler.arun(url=city_url, config=config)
        
        if not result.success:
            logger.error(f"Failed to crawl {city_name}")
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
            data = restaurant.dict()
            
            db_data = {
                'name': data['name'],
                'city_name': data['city_name'],
                'state_name': data.get('state', 'Unknown'),
                'country_code': data.get('country', 'US'),
                'city_path': self._get_city_path(data['city_name']),
                'happycow_url': data['happycow_url'],
                'vegan_status': data.get('vegan_status'),
                'description': data.get('description'),
                'last_updated': data['last_updated'].isoformat(),
                'scraped_at': data['last_updated'].isoformat(),
                'created_at': data['last_updated'].isoformat(),
                'updated_at': data['last_updated'].isoformat()
            }
            
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

    async def scrape_city_complete(self, city_name: str, max_restaurants: Optional[int] = None, city_path: Optional[str] = None) -> Dict[str, Any]:
        """Complete scraping workflow for a city"""
        logger.info(f"🏙️  Starting complete scrape for {city_name}")
        
        # Step 1: Get restaurant listings
        listings = await self.scrape_city_listings(city_name, city_path)
        
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
        saved_count = 0
        skipped_count = 0
        
        for i, listing in enumerate(listings):
            logger.info(f"[{i + 1}/{len(listings)}] Processing: {listing.name}")
            
            restaurant = await self.scrape_individual_restaurant(listing)
            if restaurant is None:
                skipped_count += 1
                continue
            
            saved = await self.save_to_supabase(restaurant)
            if saved:
                saved_count += 1
        
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

    def detect_blocking_in_content(self, html_content: str) -> bool:
        """Detect if we're being blocked based on page content"""
        blocking_indicators = [
            "captcha", "blocked", "access denied", "rate limit", 
            "too many requests", "forbidden", "cloudflare",
            "please verify", "human verification", "security check",
            "unusual traffic", "automated requests"
        ]
        
        content_lower = html_content.lower()
        for indicator in blocking_indicators:
            if indicator in content_lower:
                logger.warning(f"🚫 Blocking detected: '{indicator}' found in page content")
                return True
        return False

    async def enhanced_human_delay(self):
        """Enhanced human-like delay with realistic variance"""
        # Base delay with more realistic human patterns
        base_delay = random.uniform(self.min_delay, self.max_delay)
        
        # Add occasional longer pauses (human behavior)
        if random.random() < 0.1:  # 10% chance of longer pause
            base_delay += random.uniform(5.0, 15.0)
            logger.info(f"🤔 Taking a longer break: {base_delay:.1f}s")
        
        # Add micro-delays to simulate human reading
        reading_time = random.uniform(0.5, 2.0)
        total_delay = base_delay + reading_time
        
        await asyncio.sleep(total_delay)

    async def scrape_individual_restaurant(self, listing: RestaurantListing) -> Optional[RestaurantDetail]:
        """Scrape detailed information from an individual restaurant page"""
        # Check if restaurant already exists in database
        if await self.check_existing_restaurant(f"https://www.happycow.net{listing.url}"):
            logger.info(f"⏭️  Skipping existing restaurant: {listing.name}")
            return None
            
        restaurant_url = f"https://www.happycow.net{listing.url}"
        logger.info(f"🍽️  Scraping individual restaurant: {listing.name}")
        
        # Enhanced human delay before individual page requests
        await self.enhanced_human_delay()
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0
        )
        
        try:
            result = await self.crawler.arun(url=restaurant_url, config=config)
            
            if not result.success:
                logger.error(f"Failed to crawl restaurant page: {restaurant_url}")
                return None
            
            logger.info(f"Fetched restaurant page: {len(result.html)} chars")
            
            # Check for blocking indicators
            if self.detect_blocking_in_content(result.html):
                logger.warning(f"🚫 Blocking detected on restaurant page: {restaurant_url}")
                await self.exponential_backoff()
                return None
            
            # Extract detailed restaurant data using CSS selectors (primary strategy)
            restaurant_data = await self.extract_restaurant_details_css(result.html, listing)
            
            if not restaurant_data:
                # Fallback to regex extraction
                logger.info(f"CSS extraction failed, trying regex fallback for {listing.name}")
                restaurant_data = await self.extract_restaurant_details_regex(result.html, listing)
            
            if not restaurant_data:
                logger.warning(f"Failed to extract details for {listing.name}")
                return None
            
            return restaurant_data
            
        except Exception as e:
            logger.error(f"Error scraping restaurant {listing.name}: {e}")
            return None

    async def extract_restaurant_details_css(self, html_content: str, listing: RestaurantListing) -> Optional[RestaurantDetail]:
        """Extract restaurant details using CSS selectors (primary strategy)"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Initialize with basic data from listing
            data = {
                'name': listing.name,
                'city_name': listing.city,
                'happycow_url': f"https://www.happycow.net{listing.url}",
                'vegan_status': listing.listing_type or 'veg-friendly',
                'last_updated': datetime.now(timezone.utc)
            }
            
            # Extract detailed information using CSS selectors
            # These selectors are based on HappyCow's typical page structure
            
            # Description
            desc_elem = soup.select_one('.venue-summary, .description, .venue-description')
            if desc_elem:
                data['description'] = desc_elem.get_text(strip=True)
            
            # Address
            address_elem = soup.select_one('.address, .venue-address, .location-address')
            if address_elem:
                data['address'] = address_elem.get_text(strip=True)
            
            # Phone
            phone_elem = soup.select_one('.phone, .venue-phone, a[href^=\"tel:\"]')
            if phone_elem:
                data['phone'] = phone_elem.get_text(strip=True)
            
            # Website
            website_elem = soup.select_one('.website, .venue-website, a[href^=\"http\"]')
            if website_elem and website_elem.get('href'):
                data['website'] = website_elem.get('href')
            
            # Rating
            rating_elem = soup.select_one('.rating, .venue-rating, .stars')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Extract numeric rating (e.g., "4.5" from "4.5 stars")
                import re
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    data['rating'] = float(rating_match.group(1))
            
            # Review count
            review_elem = soup.select_one('.review-count, .reviews-count, .venue-reviews')
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    data['review_count'] = int(review_match.group(1))
            
            # Cuisine types
            cuisine_elems = soup.select('.cuisine, .cuisine-tag, .category')
            if cuisine_elems:
                data['cuisine_types'] = [elem.get_text(strip=True) for elem in cuisine_elems]
            
            # Price range
            price_elem = soup.select_one('.price, .price-range, .venue-price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Normalize price indicators
                if '$$$' in price_text:
                    data['price_range'] = '$$$'
                elif '$$' in price_text:
                    data['price_range'] = '$$'
                elif '$' in price_text:
                    data['price_range'] = '$'
            
            # Hours (this would need more complex parsing)
            hours_elem = soup.select_one('.hours, .opening-hours, .venue-hours')
            if hours_elem:
                # For now, store as text - could be enhanced to parse into structured format
                data['hours'] = {'raw': hours_elem.get_text(strip=True)}
            
            # Social media
            instagram_elem = soup.select_one('a[href*=\"instagram.com\"]')
            if instagram_elem:
                data['instagram'] = instagram_elem.get('href')
            
            facebook_elem = soup.select_one('a[href*=\"facebook.com\"]')
            if facebook_elem:
                data['facebook'] = facebook_elem.get('href')
            
            # Extract HappyCow ID from URL
            id_match = re.search(r'/reviews/(\d+)', listing.url)
            if id_match:
                data['happycow_id'] = id_match.group(1)
            
            # Set default values for missing fields
            defaults = {
                'state': 'Unknown',
                'country': 'USA',
                'country_code': 'US',
                'cuisine_tags': data.get('cuisine_types', []),
                'features': [],
                'recent_reviews': []
            }
            
            for key, value in defaults.items():
                if key not in data:
                    data[key] = value
            
            return RestaurantDetail(**data)
            
        except Exception as e:
            logger.error(f"CSS extraction error for {listing.name}: {e}")
            return None

    async def extract_restaurant_details_regex(self, html_content: str, listing: RestaurantListing) -> Optional[RestaurantDetail]:
        """Extract restaurant details using regex patterns (fallback strategy)"""
        import re
        
        try:
            # Initialize with basic data
            data = {
                'name': listing.name,
                'city_name': listing.city,
                'happycow_url': f"https://www.happycow.net{listing.url}",
                'vegan_status': listing.listing_type or 'veg-friendly',
                'last_updated': datetime.now(timezone.utc)
            }
            
            # Regex patterns for common data extraction
            patterns = {
                'phone': r'(?:tel:|phone[:\s]*)([\+\d\s\-\(\)\.]+)',
                'rating': r'(?:rating|stars?)[:\s]*(\d+\.?\d*)',
                'address': r'(?:address|location)[:\s]*([^<>\n]+)',
                'website': r'(?:website|url)[:\s]*(?:href=["\']?)?(https?://[^\s"\'<>]+)',
                'description': r'(?:description|summary)[:\s]*([^<>\n]{20,200})'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    if field == 'rating':
                        try:
                            data[field] = float(value)
                        except ValueError:
                            pass
                    else:
                        data[field] = value
            
            # Extract HappyCow ID
            id_match = re.search(r'/reviews/(\d+)', listing.url)
            if id_match:
                data['happycow_id'] = id_match.group(1)
            
            # Set defaults
            defaults = {
                'state': 'Unknown',
                'country': 'USA',
                'country_code': 'US',
                'cuisine_types': [],
                'cuisine_tags': [],
                'features': [],
                'recent_reviews': []
            }
            
            for key, value in defaults.items():
                if key not in data:
                    data[key] = value
            
            return RestaurantDetail(**data)
            
        except Exception as e:
            logger.error(f"Regex extraction error for {listing.name}: {e}")
            return None 