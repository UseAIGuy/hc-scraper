import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

async def test_visible_happycow():
    """Test scraping HappyCow with visible browser using direct Playwright"""
    print("🧪 Testing HappyCow scraping with VISIBLE browser...")
    
    # Get Supabase config from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    # Get city info from Supabase
    from supabase import create_client
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        result = supabase.table('city_queue').select('url, city, state').eq('full_path', 'dallas_texas').execute()
        if not result.data:
            print("❌ No city found for dallas_texas")
            return
        
        city_data = result.data[0]
        
        # Extract the path correctly like the CLI does
        # URL format: https://www.happycow.net/north_america/usa/state/city/
        full_url = city_data['url']
        print(f"🔗 Database URL: {full_url}")
        
        # Extract just the path part (remove the base URL)
        if full_url.startswith('https://www.happycow.net/'):
            city_path = full_url.replace('https://www.happycow.net/', '').rstrip('/')
            city_url = f"https://www.happycow.net/{city_path}/"
        else:
            # Fallback if URL doesn't have the expected format
            city_url = full_url
        
        print(f"🏙️ Found city: {city_data['city']}, {city_data['state']}")
        print(f"📍 Extracted path: {city_path}")
        print(f"🔗 Final URL: {city_url}")
        
    except Exception as e:
        print(f"❌ Error getting city data: {e}")
        return
    
    async with async_playwright() as p:
        print("🌐 Launching visible Chrome browser...")
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-infobars",
                "--disable-extensions",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )
        
        print("👀 Browser window should be visible now!")
        
        # Create a page with stealth settings
        page = await browser.new_page()
        
        # Set user agent
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        print(f"🔍 Navigating to: {city_url}")
        print("👀 Watch the browser window to see what happens...")
        
        try:
            # Navigate to the page
            await page.goto(city_url, wait_until='networkidle', timeout=30000)
            
            print("✅ Page loaded! Let's inspect what we see...")
            
            # Get page content
            html_content = await page.content()
            print(f"📄 Page size: {len(html_content)} characters")
            
            # Check for various selectors
            selectors_to_check = [
                '.restaurant-item',
                '.venue-item', 
                '.card-listing',
                '.venue-list-item',
                '.venue-item-link',
                '.captcha',
                '.no-results'
            ]
            
            print("\n🔍 Checking selectors:")
            for selector in selectors_to_check:
                try:
                    elements = await page.query_selector_all(selector)
                    count = len(elements)
                    print(f"  {selector}: {count} elements")
                    
                    if count > 0 and count < 10:  # Show details for reasonable counts
                        for i, element in enumerate(elements[:3]):  # Show first 3
                            text = await element.text_content()
                            if text:
                                text = text.strip()[:100]  # First 100 chars
                                print(f"    [{i+1}] {text}")
                except Exception as e:
                    print(f"  {selector}: Error - {e}")
            
            # Check for blocking indicators
            blocking_indicators = ['captcha', 'blocked', 'robot', 'verify', 'cloudflare']
            page_text = html_content.lower()
            
            print("\n🚫 Checking for blocking indicators:")
            for indicator in blocking_indicators:
                if indicator in page_text:
                    print(f"  ⚠️ Found '{indicator}' in page content")
                else:
                    print(f"  ✅ No '{indicator}' found")
            
            print(f"\n🕐 Keeping browser open for 30 seconds so you can inspect the page...")
            print("💡 You can manually inspect elements, check the developer tools, etc.")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"❌ Error during navigation: {e}")
            print("🕐 Keeping browser open for 10 seconds so you can see the error...")
            await asyncio.sleep(10)
        
        finally:
            print("🔚 Closing browser...")
            await browser.close()

if __name__ == "__main__":
    print("🚀 Testing HappyCow with visible browser...")
    print("📝 This will show you exactly what the scraper sees")
    print("👀 You'll be able to inspect the page manually")
    input("Press Enter to start...")
    
    asyncio.run(test_visible_happycow()) 