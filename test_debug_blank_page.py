import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables
load_dotenv()

async def debug_blank_page():
    """Debug why we're seeing a blank page on HappyCow"""
    print("🔍 Debugging blank page issue...")
    
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
        full_url = city_data['url']
        
        # Extract path correctly
        if full_url.startswith('https://www.happycow.net/'):
            city_path = full_url.replace('https://www.happycow.net/', '').rstrip('/')
            city_url = f"https://www.happycow.net/{city_path}/"
        else:
            city_url = full_url
        
        print(f"🔗 Testing URL: {city_url}")
        
    except Exception as e:
        print(f"❌ Error getting city data: {e}")
        return
    
    async with async_playwright() as p:
        print("🌐 Launching visible Chrome browser...")
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--disable-infobars"
            ]
        )
        
        # Create context with more realistic settings
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        # Enable console logging to see any JavaScript errors
        page.on("console", lambda msg: print(f"🖥️ Console: {msg.text}"))
        page.on("pageerror", lambda error: print(f"❌ Page Error: {error}"))
        
        print("👀 Browser window should be visible now!")
        
        try:
            print(f"🔍 Step 1: Navigating to {city_url}")
            response = await page.goto(city_url, wait_until='load', timeout=30000)
            
            if response:
                print(f"📊 Response status: {response.status}")
                print(f"📊 Response URL: {response.url}")
            else:
                print("⚠️ No response received")
            
            # Wait a bit for any JavaScript to load
            print("⏳ Waiting 5 seconds for JavaScript to load...")
            await asyncio.sleep(5)
            
            # Check if page has content
            html_content = await page.content()
            print(f"📄 Page HTML length: {len(html_content)} characters")
            
            # Get page title
            title = await page.title()
            print(f"📰 Page title: '{title}'")
            
            # Check if body has any visible text
            body_text = await page.evaluate("document.body.innerText")
            print(f"📝 Body text length: {len(body_text)} characters")
            
            if len(body_text) < 100:
                print(f"📝 Body text preview: '{body_text}'")
            else:
                print(f"📝 Body text preview: '{body_text[:200]}...'")
            
            # Try scrolling to trigger lazy loading
            print("📜 Scrolling to trigger lazy loading...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            
            # Try clicking or interacting to trigger content
            print("🖱️ Trying to trigger content loading...")
            await page.evaluate("window.scrollTo(0, 0)")
            await asyncio.sleep(2)
            
            # Check for common loading indicators
            loading_selectors = [
                '.loading',
                '.spinner',
                '[data-loading]',
                '.skeleton'
            ]
            
            print("🔄 Checking for loading indicators:")
            for selector in loading_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        print(f"  ⏳ Found loading indicator: {selector} ({len(elements)} elements)")
                except:
                    pass
            
            # Check network activity
            print("🌐 Checking if there are pending network requests...")
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Final content check
            final_html = await page.content()
            final_body_text = await page.evaluate("document.body.innerText")
            
            print(f"📄 Final HTML length: {len(final_html)} characters")
            print(f"📝 Final body text length: {len(final_body_text)} characters")
            
            # Check for specific HappyCow elements
            hc_selectors = [
                'body',
                'main',
                '.container',
                '#app',
                '.content',
                '[data-react]',
                'script'
            ]
            
            print("\n🔍 Checking for basic page structure:")
            for selector in hc_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"  {selector}: {len(elements)} elements")
                except Exception as e:
                    print(f"  {selector}: Error - {e}")
            
            # Check if it's a SPA (Single Page Application)
            scripts = await page.query_selector_all('script[src]')
            print(f"\n📜 Found {len(scripts)} external scripts")
            for i, script in enumerate(scripts[:5]):  # Show first 5
                src = await script.get_attribute('src')
                print(f"  [{i+1}] {src}")
            
            print(f"\n🕐 Keeping browser open for 60 seconds for manual inspection...")
            print("💡 You can:")
            print("   - Check the developer console (F12)")
            print("   - Look at the Network tab")
            print("   - Try refreshing the page manually")
            print("   - Check if there are any JavaScript errors")
            
            await asyncio.sleep(60)
            
        except Exception as e:
            print(f"❌ Error during page interaction: {e}")
            print("🕐 Keeping browser open for 30 seconds...")
            await asyncio.sleep(30)
        
        finally:
            print("🔚 Closing browser...")
            await browser.close()

if __name__ == "__main__":
    print("🔍 Debugging blank page issue...")
    print("📝 This will help us understand why the page appears blank")
    input("Press Enter to start...")
    
    asyncio.run(debug_blank_page()) 