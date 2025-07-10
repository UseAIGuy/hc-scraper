#!/usr/bin/env python3
"""
Live Scraper Test

Test the enhanced scraper with a small city to validate end-to-end functionality
"""

import asyncio
import os
from scraper import HappyCowScraper

async def test_live_scraper():
    """Test the enhanced scraper with a small city"""
    
    print("🧪 Testing Enhanced Scraper with Live Data")
    print("=" * 50)
    
    # Test with a small city that likely has few restaurants
    test_city = "Bend, Oregon"  # Small city, likely 5-10 restaurants
    
    # Initialize scraper
    scraper = HappyCowScraper()
    
    try:
        async with scraper:
            print(f"🏙️  Testing with city: {test_city}")
            
            # Run complete scraping for the test city
            result = await scraper.scrape_city_complete(test_city)
            
            print(f"✅ Scraping completed!")
            print(f"📊 Results: {result}")
            
    except Exception as e:
        print(f"❌ Error during live test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_live_scraper()) 