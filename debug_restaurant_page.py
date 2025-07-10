import asyncio
import os
import random
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

async def debug_restaurant_page():
    """Debug why individual restaurant pages are failing to crawl"""
    print("🔍 Debugging individual restaurant page access...")
    
    # Test URLs from the failed attempts
    test_urls = [
        "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/update",
        "https://www.happycow.net/reviews/la-vegan-los-angeles-14477",
        "https://www.happycow.net/reviews/my-vegan-los-angeles-119792"
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🧪 Test {i}: {url}")
        
        # First try with direct Playwright (visible browser)
        print("  📱 Testing with visible Playwright...")
        await test_with_playwright(url)
        
        # Then try with crawl4ai (headless)
        print("  🤖 Testing with crawl4ai...")
        await test_with_crawl4ai(url)

async def test_with_playwright(url):
    """Test the URL with visible Playwright"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            print(f"    🌐 Navigating to: {url}")
            response = await page.goto(url, wait_until='load', timeout=30000)
            
            if response:
                print(f"    📊 Status: {response.status}")
                print(f"    📊 Final URL: {response.url}")
                
                if response.status == 200:
                    title = await page.title()
                    print(f"    📋 Title: {title}")
                    
                    # Check for content
                    content = await page.content()
                    print(f"    📄 Content length: {len(content)} chars")
                    
                    # Look for blocking indicators
                    content_lower = content.lower()
                    blocking_words = ["captcha", "blocked", "access denied", "cloudflare"]
                    found_blocking = [word for word in blocking_words if word in content_lower]
                    if found_blocking:
                        print(f"    ⚠️ Blocking indicators: {found_blocking}")
                    else:
                        print(f"    ✅ No obvious blocking detected")
                        
                    # Check if it's a valid restaurant page
                    soup = BeautifulSoup(content, 'html.parser')
                    restaurant_indicators = soup.select('.restaurant-name, .venue-name, h1, .venue-details')
                    print(f"    🍽️ Restaurant content elements: {len(restaurant_indicators)}")
                    
                else:
                    print(f"    ❌ HTTP Error: {response.status}")
            else:
                print(f"    ❌ No response received")
                
            await browser.close()
            
    except Exception as e:
        print(f"    ❌ Playwright error: {e}")

async def test_with_crawl4ai(url):
    """Test the URL with crawl4ai (same as scraper)"""
    try:
        USER_AGENTS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        crawler = AsyncWebCrawler(
            headless=True,
            browser_type="chromium",
            verbose=False
        )
        
        async with crawler:
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000,
                delay_before_return_html=3.0,
                user_agent=random.choice(USER_AGENTS),
                wait_for="css:.card-listing, .venue-list-item, .no-results",
                css_selector="body",
                screenshot=False,
                verbose=False
            )
            
            print(f"    🌐 Crawling with crawl4ai...")
            result = await crawler.arun(url=url, config=config)
            
            print(f"    📊 Success: {result.success}")
            if result.success:
                print(f"    📄 HTML length: {len(result.html)} chars")
                
                # Check for blocking
                content_lower = result.html.lower()
                blocking_words = ["captcha", "blocked", "access denied", "cloudflare"]
                found_blocking = [word for word in blocking_words if word in content_lower]
                if found_blocking:
                    print(f"    ⚠️ Blocking indicators: {found_blocking}")
                else:
                    print(f"    ✅ No obvious blocking detected")
                    
                # Check for restaurant content
                soup = BeautifulSoup(result.html, 'html.parser')
                restaurant_indicators = soup.select('.restaurant-name, .venue-name, h1, .venue-details')
                print(f"    🍽️ Restaurant content elements: {len(restaurant_indicators)}")
                
                # Save HTML for inspection
                filename = f"restaurant_debug_{url.split('/')[-1]}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(result.html)
                print(f"    💾 Saved HTML to {filename}")
                
            else:
                print(f"    ❌ Crawl failed")
                
    except Exception as e:
        print(f"    ❌ Crawl4ai error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_restaurant_page()) 