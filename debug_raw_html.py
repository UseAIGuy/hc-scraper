import asyncio
import os
import random
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

async def debug_raw_html():
    """Get the raw HTML that crawl4ai receives and save it for inspection"""
    print("🔍 Getting raw HTML from crawl4ai...")
    
    # Use the same user agents as the scraper
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    crawler = AsyncWebCrawler(
        headless=True,
        browser_type="chromium",
        verbose=False
    )
    
    try:
        async with crawler:
            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000,
                delay_before_return_html=3.0,
                user_agent=random.choice(USER_AGENTS),
                wait_for="css:.venue-item, .card-listing, .no-results, .captcha",
                css_selector="body",
                screenshot=False,
                verbose=False
            )
            
            city_url = "https://www.happycow.net/north_america/usa/texas/dallas/"
            print(f"🌐 Fetching: {city_url}")
            
            result = await crawler.arun(url=city_url, config=config)
            
            print(f"📄 Result:")
            print(f"  Success: {result.success}")
            print(f"  HTML length: {len(result.html)} chars")
            
            # Save the HTML
            with open("raw_html_output.html", "w", encoding="utf-8") as f:
                f.write(result.html)
            print("💾 Saved HTML to raw_html_output.html")
            
            # Check for blocking indicators
            html_lower = result.html.lower()
            blocking_indicators = [
                "captcha", "blocked", "access denied", "rate limit", 
                "too many requests", "forbidden", "cloudflare",
                "please verify", "human verification", "security check",
                "unusual traffic", "automated requests", "challenge"
            ]
            
            print(f"\n🚫 Blocking indicators:")
            found_blocking = []
            for indicator in blocking_indicators:
                if indicator in html_lower:
                    found_blocking.append(indicator)
                    start = html_lower.find(indicator)
                    context = result.html[max(0, start-50):start+150]
                    print(f"  ⚠️ Found '{indicator}': ...{context}...")
            
            if not found_blocking:
                print("  ✅ No blocking indicators found!")
            
            # Check for restaurant selectors
            print(f"\n🔍 Selector analysis:")
            soup = BeautifulSoup(result.html, 'html.parser')
            
            selectors = [
                '.restaurant-item',
                '.venue-item', 
                '.card-listing',
                '.venue-list-item',
                '.venue-item-link',
                '.captcha',
                '.no-results'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                print(f"  {selector}: {len(elements)} elements")
                
                if 0 < len(elements) <= 3:
                    for i, elem in enumerate(elements):
                        text = elem.get_text(strip=True)[:80]
                        print(f"    [{i+1}] {text}...")
            
            # Look for any content that might indicate the page structure
            print(f"\n📋 Page analysis:")
            title = soup.find('title')
            if title:
                print(f"  Title: {title.get_text(strip=True)}")
            
            # Look for main content areas
            main_areas = soup.select('main, .main, #main, .content, #content')
            print(f"  Main content areas: {len(main_areas)}")
            
            # Look for any div with lots of content
            divs = soup.find_all('div')
            content_divs = [div for div in divs if len(div.get_text(strip=True)) > 100]
            print(f"  Content divs (>100 chars): {len(content_divs)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_raw_html()) 