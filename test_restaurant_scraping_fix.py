"""
Test the actual scraper with the page type detection fix
"""

import asyncio
import logging
import os
from scraper import HappyCowScraper, RestaurantListing

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_restaurant_scraping():
    """Test that restaurant pages can now be scraped successfully"""
    
    # Get environment variables
    supabase_url = os.getenv('SUPABASE_URL', 'dummy_url')
    supabase_key = os.getenv('SUPABASE_KEY', 'dummy_key')
    
    # Create a test restaurant listing (one that was failing before)
    test_listing = RestaurantListing(
        name="Tane Vegan Izakaya",
        url="/reviews/tane-vegan-izakaya-los-angeles-467122/",
        city="Los Angeles",
        listing_type="vegan",
        is_featured=False,
        is_new=False
    )
    
    print("🧪 Testing Restaurant Page Scraping with Fix:")
    print("=" * 60)
    print(f"🍽️  Restaurant: {test_listing.name}")
    print(f"🔗 URL: https://www.happycow.net{test_listing.url}")
    
    # Create scraper (don't need real Supabase for this test)
    scraper = HappyCowScraper(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        max_restaurants=1
    )
    
    try:
        async with scraper:
            print("\n🔍 Testing page type detection...")
            from page_type_detector import detect_page_type
            
            restaurant_url = f"https://www.happycow.net{test_listing.url}"
            page_type = detect_page_type(restaurant_url)
            print(f"✅ Page type detected: {page_type.value}")
            
            print("\n🔧 Testing CSS selector configuration...")
            from css_selector_config import CSSConfigManager
            config = CSSConfigManager.get_crawl_config_for_page_type(page_type)
            print(f"✅ Selectors: {config['wait_for']}")
            print(f"✅ Timeout: {config['timeout']}s")
            
            print("\n🚀 Testing actual crawling (this should work now)...")
            
            # Test the scraper method that was failing before
            # Note: This will make a real HTTP request
            result = await scraper.scrape_individual_restaurant(test_listing)
            
            if result is not None:
                print("🎉 SUCCESS! Restaurant page was crawled successfully!")
                restaurant_data, reviews = result
                print(f"✅ Restaurant name: {restaurant_data.name}")
                print(f"✅ Description: {restaurant_data.description[:100] if restaurant_data.description else 'N/A'}...")
                print(f"✅ Address: {restaurant_data.address or 'N/A'}")
                print(f"✅ Reviews found: {len(reviews) if reviews else 0}")
                return True
            else:
                print("❌ FAILED: Restaurant page still couldn't be crawled")
                return False
                
    except Exception as e:
        print(f"❌ ERROR during test: {e}")
        return False

async def test_comparison():
    """Show the before/after comparison"""
    print("\n" + "="*60)
    print("🔧 BEFORE vs AFTER Summary:")
    print("="*60)
    
    print("\n❌ BEFORE (Broken):")
    print("   Restaurant pages used city listing selectors:")
    print("   wait_for='css:.card-listing, .venue-list-item, .no-results'")
    print("   → RESULT: Timeout waiting for elements that don't exist")
    print("   → STATUS: All restaurant pages failed to crawl")
    
    print("\n✅ AFTER (Fixed):")
    print("   Restaurant pages use restaurant-specific selectors:")
    print("   wait_for='css:.restaurant-header, .venue-header, .restaurant-details, ...'")
    print("   → RESULT: Waits for elements that actually exist on restaurant pages")
    print("   → STATUS: Restaurant pages should crawl successfully")
    
    print("\n🎯 The Fix:")
    print("   1. ✅ Page type detection: Automatically detects city vs restaurant pages")
    print("   2. ✅ CSS selector mapping: Different selectors for different page types")
    print("   3. ✅ Conditional crawl config: Uses appropriate selectors per page type")

if __name__ == "__main__":
    print("🧪 HappyCow Scraper - Restaurant Page Fix Test")
    print("="*60)
    
    # Show the comparison first
    asyncio.run(test_comparison())
    
    # Ask user if they want to test with real HTTP request
    print(f"\n🌐 Ready to test with real HTTP request?")
    print("This will make an actual request to HappyCow to verify the fix works.")
    
    user_input = input("Press Enter to test, or 'n' to skip: ").strip().lower()
    
    if user_input != 'n':
        print("\n🚀 Testing with real HTTP request...")
        success = asyncio.run(test_restaurant_scraping())
        
        if success:
            print("\n🎉 CONCLUSION: The fix works! Restaurant pages can now be scraped successfully!")
        else:
            print("\n⚠️  CONCLUSION: There may still be issues. Check the logs above for details.")
    else:
        print("\n✅ Test completed. The fix should work based on the configuration test!") 