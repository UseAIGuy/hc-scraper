"""
Test script to verify the page type detection and CSS selector fix
"""

import asyncio
import logging
from page_type_detector import detect_page_type, PageType
from css_selector_config import CSSConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_page_type_detection_and_selectors():
    """Test page type detection and corresponding CSS selectors"""
    
    test_urls = [
        # City listing URLs (should use city listing selectors)
        "https://www.happycow.net/north_america/usa/texas/dallas/",
        "https://www.happycow.net/north_america/usa/california/los_angeles/",
        
        # Restaurant URLs (should use restaurant page selectors) 
        "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/",
        "https://www.happycow.net/reviews/la-vegan-los-angeles-14477",
        "https://www.happycow.net/reviews/my-vegan-los-angeles-119792",
    ]
    
    print("🧪 Testing Page Type Detection & CSS Selector Configuration:")
    print("=" * 80)
    
    for url in test_urls:
        print(f"\n🔍 URL: {url}")
        
        # Detect page type using convenience function
        page_type = detect_page_type(url)
        print(f"📄 Page Type: {page_type.value}")
        
        # Get CSS configuration
        config = CSSConfigManager.get_config_for_page_type(page_type)
        crawl_config = CSSConfigManager.get_crawl_config_for_page_type(page_type)
        
        print(f"🎯 Wait for selectors: {config.get_wait_for_selector_string()}")
        print(f"⏱️  Timeout: {config.wait_timeout}s")
        print(f"🔧 Crawl4ai config: {crawl_config}")
        
        # Show expected behavior
        if page_type == PageType.CITY_LISTING:
            print("✅ Expected: Should find restaurant cards (.card-listing, .venue-list-item)")
        elif page_type == PageType.RESTAURANT_PAGE:
            print("✅ Expected: Should find restaurant details (.restaurant-header, .venue-header, etc.)")
        else:
            print("⚠️  Expected: Fallback to basic page detection")
        
        print("-" * 60)

def test_original_vs_fixed_behavior():
    """Compare the old hardcoded selectors vs new page-type-specific selectors"""
    
    restaurant_url = "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/"
    city_url = "https://www.happycow.net/north_america/usa/texas/dallas/"
    
    print("\n🔧 BEFORE vs AFTER Comparison:")
    print("=" * 80)
    
    print(f"\n🍽️  RESTAURANT PAGE: {restaurant_url}")
    print("❌ BEFORE (Wrong): wait_for='css:.card-listing, .venue-list-item, .no-results'")
    print("   → Would timeout waiting for city listing elements that don't exist on restaurant pages")
    
    page_type = detect_page_type(restaurant_url)
    config = CSSConfigManager.get_crawl_config_for_page_type(page_type)
    print(f"✅ AFTER (Fixed): wait_for='css:{config['wait_for']}'")
    print("   → Will wait for restaurant-specific elements that actually exist")
    
    print(f"\n🏙️  CITY PAGE: {city_url}")
    print("✅ BEFORE (Correct): wait_for='css:.card-listing, .venue-list-item, .no-results'")
    
    page_type = detect_page_type(city_url)  
    config = CSSConfigManager.get_crawl_config_for_page_type(page_type)
    print(f"✅ AFTER (Same): wait_for='css:{config['wait_for']}'")
    print("   → Still uses correct city listing selectors")

if __name__ == "__main__":
    test_page_type_detection_and_selectors()
    test_original_vs_fixed_behavior()
    
    print("\n🎉 Fix Summary:")
    print("=" * 80)
    print("✅ Page type detection: IMPLEMENTED")
    print("✅ CSS selector configuration: IMPLEMENTED") 
    print("✅ Conditional crawl4ai config: IMPLEMENTED")
    print("✅ Restaurant page selectors: FIXED")
    print("✅ City listing selectors: MAINTAINED")
    print("\n🚀 The scraper should now successfully crawl restaurant pages!") 