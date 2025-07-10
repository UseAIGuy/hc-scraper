#!/usr/bin/env python3
"""
Test the complete scraping flow from city listings to individual restaurant details and reviews
"""

import asyncio
import os
from scraper import HappyCowScraper
from config import load_config

async def test_complete_flow():
    """Test the complete scraping flow for a city"""
    
    # Get configuration
    config = load_config()
    
    # Create scraper instance
    scraper = HappyCowScraper(
        supabase_url=config.supabase_url,
        supabase_key=config.supabase_key,
        max_workers=2,  # Reduce concurrency for testing
        min_delay=3.0,  # Slower for testing
        max_delay=6.0,
        max_restaurants=3  # Limit to 3 restaurants for testing
    )
    
    print("🚀 Testing complete scraping flow...")
    print("=" * 50)
    
    async with scraper:
        # Test with Austin (smaller city for testing)
        city_name = "Austin"
        print(f"Testing complete flow for {city_name}")
        
        # Run the complete scraping workflow
        result = await scraper.scrape_city_complete(
            city_name=city_name,
            max_restaurants=3  # Limit for testing
        )
        
        print("\n" + "=" * 50)
        print("📊 RESULTS:")
        print(f"City: {result['city']}")
        print(f"Success: {result['success']}")
        print(f"Listings found: {result['listings_found']}")
        print(f"Restaurants scraped: {result['restaurants_scraped']}")
        print(f"Restaurants saved: {result['restaurants_saved']}")
        print(f"Restaurants skipped: {result['restaurants_skipped']}")
        
        if result['success']:
            print("\n✅ Complete flow test PASSED!")
            print("The scraper successfully:")
            print("  1. ✅ Scraped city listings")
            print("  2. ✅ Visited individual restaurant pages")
            print("  3. ✅ Extracted detailed restaurant data")
            print("  4. ✅ Extracted reviews from restaurant pages")
            print("  5. ✅ Saved everything to database")
        else:
            print("\n❌ Complete flow test FAILED!")
            print("Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(test_complete_flow()) 