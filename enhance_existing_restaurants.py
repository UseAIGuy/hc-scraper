#!/usr/bin/env python3
"""
Enhance Existing Restaurants

This script takes existing restaurants from the database (that only have basic info)
and enhances them with detailed data by scraping their individual HappyCow pages.
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from scraper import HappyCowScraper, RestaurantListing
from enhanced_extraction_engine import EnhancedExtractionEngine
from review_extraction_engine import ReviewExtractionEngine
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

# Load environment variables
load_dotenv()

class RestaurantEnhancer:
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.extraction_engine = EnhancedExtractionEngine()
        self.review_engine = ReviewExtractionEngine()
        self.crawler = None
        
    async def __aenter__(self):
        """Initialize crawler"""
        self.crawler = AsyncWebCrawler(
            headless=True,
            verbose=False,
            browser_type="chromium"
        )
        await self.crawler.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup crawler"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    async def enhance_restaurants(self, limit: int = 5, city_filter: str = None):
        """Enhance existing restaurants with detailed data"""
        
        # Initialize scraper for database operations
        scraper = HappyCowScraper(self.supabase_url, self.supabase_key)
        
        print(f"🔍 Finding restaurants to enhance...")
        
        # Get restaurants that need enhancement (missing rating data)
        query = scraper.supabase.table('restaurants').select('*').is_('rating', 'null')
        
        if city_filter:
            query = query.eq('city_name', city_filter)
            
        query = query.limit(limit)
        
        result = query.execute()
        
        if not result.data:
            print("❌ No restaurants found that need enhancement")
            return
            
        restaurants = result.data
        print(f"📊 Found {len(restaurants)} restaurants to enhance")
        
        if city_filter:
            print(f"🏙️  Filtering by city: {city_filter}")
        
        enhanced_count = 0
        error_count = 0
        
        for i, restaurant in enumerate(restaurants):
            print(f"\n[{i+1}/{len(restaurants)}] Enhancing: {restaurant['name']}")
            
            try:
                # Build full URL
                happycow_url = restaurant['happycow_url']
                if not happycow_url.startswith('http'):
                    full_url = f"https://www.happycow.net{happycow_url}"
                else:
                    full_url = happycow_url
                
                print(f"  🌐 URL: {full_url}")
                
                # Scrape the individual page
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=30000,
                    delay_before_return_html=2.0
                )
                
                result = await self.crawler.arun(url=full_url, config=config)
                
                if not result.success:
                    print(f"  ❌ Failed to fetch page")
                    error_count += 1
                    continue
                
                # Extract enhanced data
                extracted_data = await self.extraction_engine.extract_restaurant_data(full_url, result.html)
                
                if not extracted_data:
                    print(f"  ⚠️  No data extracted")
                    error_count += 1
                    continue
                
                # Prepare update data
                update_data = {
                    'rating': extracted_data.get('rating'),
                    'review_count': extracted_data.get('review_count'),
                    'phone': extracted_data.get('phone'),
                    'website': extracted_data.get('website'),
                    'address': extracted_data.get('address'),
                    'description': extracted_data.get('description'),
                    'vegan_status': extracted_data.get('vegan_status'),
                    'instagram': extracted_data.get('instagram'),
                    'facebook': extracted_data.get('facebook'),
                    'twitter': extracted_data.get('twitter'),
                    'hours': json.dumps(extracted_data.get('hours', {})) if extracted_data.get('hours') else None,
                    'features': json.dumps(extracted_data.get('features', [])) if extracted_data.get('features') else None,
                    'cuisine_types': json.dumps(extracted_data.get('cuisine_types', [])) if extracted_data.get('cuisine_types') else None,
                    'price_range': extracted_data.get('price_range')
                }
                
                # Remove None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                
                # Update the restaurant
                update_result = scraper.supabase.table('restaurants').update(update_data).eq('id', restaurant['id']).execute()
                
                if update_result.data:
                    enhanced_count += 1
                    print(f"  ✅ Enhanced with {len(update_data)} fields")
                    
                    # Show what was extracted
                    if extracted_data.get('rating'):
                        print(f"     Rating: {extracted_data['rating']}/5 ({extracted_data.get('review_count', 0)} reviews)")
                    if extracted_data.get('phone'):
                        print(f"     Phone: {extracted_data['phone']}")
                    if extracted_data.get('website'):
                        print(f"     Website: {extracted_data['website']}")
                    if extracted_data.get('vegan_status'):
                        print(f"     Status: {extracted_data['vegan_status']}")
                    
                    # Extract and save reviews
                    try:
                        print(f"  📝 Extracting reviews...")
                        reviews = self.review_engine.extract_reviews_from_html(result.html)
                        
                        if reviews:
                            # Save reviews using the scraper's method
                            review_count = await scraper.save_reviews_to_supabase(reviews, restaurant['id'], full_url)
                            print(f"     💬 Saved {review_count} reviews")
                        else:
                            print(f"     💬 No reviews found")
                            
                    except Exception as e:
                        print(f"     ⚠️  Review extraction failed: {e}")
                        
                else:
                    print(f"  ❌ Failed to update database")
                    error_count += 1
                
                # Delay between requests
                await asyncio.sleep(2.0)
                
            except Exception as e:
                print(f"  ❌ Error enhancing restaurant: {e}")
                error_count += 1
                continue
        
        print(f"\n🎉 Enhancement Complete!")
        print(f"   ✅ Enhanced: {enhanced_count} restaurants")
        print(f"   ❌ Errors: {error_count} restaurants")
        print(f"   📊 Success Rate: {enhanced_count/(enhanced_count+error_count)*100:.1f}%")

async def main():
    """Main function"""
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        return
    
    print("🚀 Restaurant Enhancement Tool")
    print("=" * 50)
    
    # You can modify these parameters:
    LIMIT = 5  # Number of restaurants to enhance
    CITY_FILTER = None  # Set to city name to filter, or None for all cities
    
    print(f"📊 Settings:")
    print(f"   Limit: {LIMIT} restaurants")
    print(f"   City Filter: {CITY_FILTER or 'All cities'}")
    
    async with RestaurantEnhancer(supabase_url, supabase_key) as enhancer:
        await enhancer.enhance_restaurants(limit=LIMIT, city_filter=CITY_FILTER)

if __name__ == "__main__":
    asyncio.run(main()) 