#!/usr/bin/env python3
"""
Test Fixed Scraper

Quick test to verify the enhanced extraction is working with the fixed data model conversion.
"""

import asyncio
import os
from dotenv import load_dotenv
from scraper import HappyCowScraper

# Load environment variables
load_dotenv()

async def test_fixed_scraper():
    """Test the fixed scraper with a single restaurant"""
    
    print("🧪 Testing Fixed Enhanced Scraper")
    print("=" * 40)
    
    # Test with a very small city
    test_city = "Santa Barbara, California"  # Small city with few restaurants
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    # Initialize scraper with limit of 1 restaurant for testing
    scraper = HappyCowScraper(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        max_restaurants=1,
        min_delay=1.0,
        max_delay=2.0
    )
    
    try:
        async with scraper:
            print(f"🏙️  Testing with: {test_city}")
            print(f"📊 Limiting to 1 restaurant for testing")
            
            # Run scraping
            result = await scraper.scrape_city_complete(test_city, max_restaurants=1)
            
            print(f"\n🎉 Test Results:")
            print(f"Success: {result['success']}")
            print(f"Restaurants Found: {result['listings_found']}")
            print(f"Restaurants Saved: {result['restaurants_saved']}")
            
            if result['restaurants_saved'] > 0:
                print("\n✅ SUCCESS! Enhanced scraper is working")
                
                # Check the latest restaurant in database
                try:
                    latest = scraper.supabase.table('restaurants').select('*').order('created_at', desc=True).limit(1).execute()
                    if latest.data:
                        restaurant = latest.data[0]
                        print(f"\n📊 Latest Restaurant Data:")
                        print(f"  Name: {restaurant.get('name', 'N/A')}")
                        print(f"  Rating: {restaurant.get('rating', 'N/A')}")
                        print(f"  Review Count: {restaurant.get('review_count', 'N/A')}")
                        print(f"  Phone: {restaurant.get('phone', 'N/A')}")
                        print(f"  Website: {restaurant.get('website', 'N/A')}")
                        print(f"  Address: {restaurant.get('address', 'N/A')}")
                        print(f"  Description: {restaurant.get('description', 'N/A')[:100]}...")
                        print(f"  Vegan Status: {restaurant.get('vegan_status', 'N/A')}")
                        
                        # Check for reviews
                        reviews = scraper.supabase.table('reviews').select('*').eq('restaurant_id', restaurant['id']).execute()
                        if reviews.data:
                            print(f"  Reviews: {len(reviews.data)} found!")
                            sample_review = reviews.data[0]
                            print(f"    Sample: {sample_review.get('rating', 'N/A')}/5 by {sample_review.get('author_username', 'Unknown')}")
                        else:
                            print(f"  Reviews: None found")
                            
                except Exception as e:
                    print(f"⚠️  Error checking latest data: {e}")
            else:
                print("\n⚠️  No restaurants were saved - might be existing data")
                
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_scraper()) 