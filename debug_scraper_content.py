import asyncio
import os
from dotenv import load_dotenv
from scraper import HappyCowScraper

# Load environment variables
load_dotenv()

async def debug_scraper_content():
    """Debug what HTML content the scraper is actually receiving"""
    print("🔍 Debugging scraper content vs manual browser...")
    
    # Get Supabase config from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    # Create scraper instance
    scraper = HappyCowScraper(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        use_local_llm=True,
        max_restaurants=1
    )
    
    async with scraper:
        try:
            # Get the city data like the scraper does
            result = scraper.supabase.table('city_queue').select('url, city, state').eq('full_path', 'dallas_texas').execute()
            if not result.data:
                print("❌ No city found for dallas_texas")
                return
            
            city_data = result.data[0]
            full_url = city_data['url']
            
            # Extract path like CLI does
            if full_url.startswith('https://www.happycow.net/'):
                city_path = full_url.replace('https://www.happycow.net/', '').rstrip('/')
                city_url = f"https://www.happycow.net/{city_path}/"
            else:
                city_url = full_url
            
            print(f"🔗 Scraper will use URL: {city_url}")
            
            # Now let's see what the scraper actually gets
            print("🤖 Using scraper's method to fetch the page...")
            
            # Call the same method the scraper uses
            listings = await scraper.scrape_city_listings("dallas_texas", city_path)
            
            print(f"📊 Scraper result: {len(listings)} listings found")
            
            # Let's also get the raw HTML that was fetched
            print("💾 Attempting to save the HTML content that caused blocking detection...")
            
            # Try to get the last fetched content from the scraper
            # We'll need to modify the scraper method to capture this
            
        except Exception as e:
            print(f"❌ Error during scraper test: {e}")
            
            # Since the method failed, let's manually recreate what it does
            print("🔍 Manually recreating the scraper's fetch process...")
            
            try:
                from crawl4ai import CrawlerRunConfig, CacheMode
                import random
                from scraper import StealthConfig
                
                # Use the exact same config as the scraper
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=30000,
                    delay_before_return_html=3.0,
                    user_agent=random.choice(StealthConfig.USER_AGENTS),
                    wait_for="css:.venue-item, .card-listing, .no-results, .captcha",
                    js_code=scraper.stealth_config.js_code,
                    css_selector="body",
                    screenshot=False,
                    verbose=False
                )
                
                city_url = "https://www.happycow.net/north_america/usa/texas/dallas/"
                print(f"🌐 Fetching: {city_url}")
                result = await scraper.crawler.arun(url=city_url, config=config)
                
                print(f"📄 Raw crawler result:")
                print(f"  Success: {result.success}")
                print(f"  HTML length: {len(result.html)} chars")
                
                # Save the HTML for inspection
                with open("debug_scraper_output.html", "w", encoding="utf-8") as f:
                    f.write(result.html)
                print("💾 Saved HTML content to debug_scraper_output.html")
                
                # Check for blocking indicators
                html_lower = result.html.lower()
                blocking_indicators = [
                    "captcha", "blocked", "access denied", "rate limit", 
                    "too many requests", "forbidden", "cloudflare",
                    "please verify", "human verification", "security check",
                    "unusual traffic", "automated requests"
                ]
                
                print(f"🚫 Blocking indicators found:")
                found_any = False
                for indicator in blocking_indicators:
                    if indicator in html_lower:
                        found_any = True
                        print(f"  ⚠️ Found: '{indicator}'")
                        # Show context around the indicator
                        start = html_lower.find(indicator)
                        context = result.html[max(0, start-50):start+150]
                        print(f"     Context: ...{context}...")
                
                if not found_any:
                    print("  ✅ No blocking indicators found!")
                
                # Check for restaurant selectors
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(result.html, 'html.parser')
                
                selectors_to_check = [
                    '.restaurant-item',
                    '.venue-item', 
                    '.card-listing',
                    '.venue-list-item',
                    '.venue-item-link',
                    '.captcha',
                    '.no-results'
                ]
                
                print(f"\n🔍 Selector analysis:")
                for selector in selectors_to_check:
                    elements = soup.select(selector)
                    print(f"  {selector}: {len(elements)} elements")
                    
                    if len(elements) > 0 and len(elements) < 5:
                        for i, elem in enumerate(elements):
                            text = elem.get_text(strip=True)[:100]
                            print(f"    [{i+1}] {text}")
                
            except Exception as e2:
                print(f"❌ Error during manual crawler test: {e2}")

if __name__ == "__main__":
    print("🔍 Debugging what the scraper actually receives...")
    print("📝 This will compare scraper results vs manual browser")
    
    asyncio.run(debug_scraper_content()) 