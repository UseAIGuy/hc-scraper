"""
Debug script to isolate why crawl4ai is timing out on restaurant pages
even though selectors exist
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def debug_crawl4ai_selectors():
    """Test each selector individually to find the issue"""
    
    restaurant_url = "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/"
    
    # Test selectors individually
    test_selectors = [
        "h1",
        ".venue", 
        ".content",
        ".venue-info",
        ".title",
        ".main",
        "body",  # Should always work
        "html"   # Should always work
    ]
    
    print("🔍 DEBUG: Testing Individual Selectors with crawl4ai")
    print("=" * 70)
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        
        # Test 1: No wait condition (should work)
        print("\n🧪 TEST 1: No wait condition")
        print("-" * 40)
        try:
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=15000
            )
            result = await crawler.arun(url=restaurant_url, config=config)
            print(f"✅ SUCCESS: Got {len(result.html)} characters")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return
        
        # Test 2: Test each selector individually
        print("\n🧪 TEST 2: Individual Selector Testing")
        print("-" * 40)
        
        for selector in test_selectors:
            print(f"\n🎯 Testing selector: '{selector}'")
            try:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=10000,
                    wait_for=f"css:{selector}"
                )
                result = await crawler.arun(url=restaurant_url, config=config)
                print(f"   ✅ SUCCESS: {selector}")
            except Exception as e:
                print(f"   ❌ FAILED: {selector} - {e}")
        
        # Test 3: Test combinations
        print("\n🧪 TEST 3: Combination Testing")
        print("-" * 40)
        
        combinations = [
            "h1",
            "h1, .venue",
            "h1, .venue, .content",
            ".venue, .content",
            ".main, .content"
        ]
        
        for combo in combinations:
            print(f"\n🎯 Testing combination: '{combo}'")
            try:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=10000,
                    wait_for=f"css:{combo}"
                )
                result = await crawler.arun(url=restaurant_url, config=config)
                print(f"   ✅ SUCCESS: {combo}")
            except Exception as e:
                print(f"   ❌ FAILED: {combo} - {e}")
        
        # Test 4: Different wait_for formats
        print("\n🧪 TEST 4: Different wait_for Formats")
        print("-" * 40)
        
        formats = [
            "css:h1",           # Explicit CSS
            "h1",               # Implicit CSS
            "css:h1, css:.venue", # Multiple explicit
            "h1, .venue"        # Multiple implicit
        ]
        
        for format_test in formats:
            print(f"\n🎯 Testing format: '{format_test}'")
            try:
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=10000,
                    wait_for=format_test
                )
                result = await crawler.arun(url=restaurant_url, config=config)
                print(f"   ✅ SUCCESS: {format_test}")
            except Exception as e:
                print(f"   ❌ FAILED: {format_test} - {e}")

if __name__ == "__main__":
    asyncio.run(debug_crawl4ai_selectors()) 