"""
Simple test for restaurant page crawling fix without Supabase dependency
"""

import asyncio
import logging
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from page_type_detector import detect_page_type
from css_selector_config import CSSConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_restaurant_page_crawling():
    """Test that restaurant pages can now be crawled with correct selectors"""
    
    # Test restaurant URL that was failing before
    restaurant_url = "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/"
    
    print("🧪 Testing Restaurant Page Crawling Fix (No Supabase)")
    print("=" * 60)
    print(f"🍽️  Testing URL: {restaurant_url}")
    
    # 1. Test page type detection
    print("\n🔍 Step 1: Page Type Detection")
    page_type = detect_page_type(restaurant_url)
    print(f"✅ Detected page type: {page_type.value}")
    
    # 2. Test CSS selector configuration
    print("\n🔧 Step 2: CSS Selector Configuration")
    config_dict = CSSConfigManager.get_crawl_config_for_page_type(page_type)
    print(f"✅ Wait for selectors: {config_dict['wait_for']}")
    print(f"✅ Timeout: {config_dict['timeout']}s")
    
    # 3. Test actual crawling with new selectors
    print("\n🚀 Step 3: Testing Actual Crawling")
    print("This will make a real HTTP request to verify the fix works...")
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        # Create crawl config with the CORRECT selectors for restaurant pages
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=config_dict['timeout'] * 1000,  # Convert to milliseconds
            delay_before_return_html=3.0,
            wait_for=f"css:{config_dict['wait_for']}",  # 🎯 USE CORRECT SELECTORS!
            css_selector="body",
            screenshot=False,
            verbose=False
        )
        
        print(f"⏳ Crawling with selectors: {config_dict['wait_for']}")
        
        # This is the crucial test - does crawl4ai succeed with restaurant selectors?
        result = await crawler.arun(url=restaurant_url, config=config)
        
        if result.success:
            print("🎉 SUCCESS! Restaurant page crawled successfully!")
            print(f"✅ HTML content length: {len(result.html)} characters")
            print(f"✅ Response status: {getattr(result, 'status_code', 'N/A')}")
            
            # Check if we got meaningful content
            if len(result.html) > 1000:
                print("✅ Got substantial content (likely successful)")
                
                # Quick check for restaurant-specific content
                restaurant_indicators = [
                    "restaurant", "venue", "review", "rating", "address", 
                    "phone", "hours", "menu", "vegan", "vegetarian"
                ]
                
                found_indicators = []
                for indicator in restaurant_indicators:
                    if indicator.lower() in result.html.lower():
                        found_indicators.append(indicator)
                
                print(f"✅ Found restaurant content indicators: {found_indicators[:5]}...")
                return True
            else:
                print("⚠️  Got minimal content - might be blocked or empty page")
                return False
        else:
            print("❌ FAILED! Restaurant page still couldn't be crawled")
            print(f"❌ Error: {getattr(result, 'error_message', 'Unknown error')}")
            return False

async def test_comparison_with_wrong_selectors():
    """Test what happens with the OLD (wrong) selectors for comparison"""
    
    restaurant_url = "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/"
    
    print("\n" + "=" * 60)
    print("🔄 Comparison Test: OLD vs NEW Selectors")
    print("=" * 60)
    
    # Test with OLD (wrong) selectors that were causing the problem
    old_selectors = ".card-listing, .venue-list-item, .no-results"
    print(f"\n❌ Testing with OLD selectors: {old_selectors}")
    print("(This should fail/timeout because these elements don't exist on restaurant pages)")
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=10000,  # Short timeout for this test
            delay_before_return_html=2.0,
            wait_for=f"css:{old_selectors}",  # OLD (wrong) selectors
            css_selector="body",
            screenshot=False,
            verbose=False
        )
        
        print("⏳ Testing old selectors (should timeout)...")
        
        try:
            result = await crawler.arun(url=restaurant_url, config=config)
            
            if result.success:
                print("😱 Unexpected: Old selectors worked (maybe page structure changed?)")
            else:
                print("✅ Expected: Old selectors failed as expected")
                print(f"   Error: {getattr(result, 'error_message', 'Timeout waiting for selectors')}")
        except Exception as e:
            print(f"✅ Expected: Old selectors caused exception: {e}")

if __name__ == "__main__":
    print("🧪 HappyCow Restaurant Page Crawling Fix - Simple Test")
    print("=" * 60)
    
    # Test the fix
    success = asyncio.run(test_restaurant_page_crawling())
    
    if success:
        print("\n🎉 CONCLUSION: The fix works! Restaurant pages can now be crawled!")
        
        # Optional: Show comparison with old selectors
        print("\n🤔 Want to see how the OLD selectors would fail?")
        user_input = input("Press Enter to test old selectors, or 'n' to skip: ").strip().lower()
        
        if user_input != 'n':
            asyncio.run(test_comparison_with_wrong_selectors())
    else:
        print("\n⚠️  CONCLUSION: There may still be issues with the fix.")
        print("Check if the restaurant page structure has changed or if there are other issues.") 