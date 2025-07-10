import asyncio
from playwright.async_api import async_playwright

async def test_direct_playwright():
    """Test if we can open a visible browser using Playwright directly"""
    print("🧪 Testing direct Playwright visible browser...")
    
    async with async_playwright() as p:
        # Launch visible browser
        print("🌐 Launching visible Chrome browser...")
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-infobars",
                "--disable-extensions"
            ]
        )
        
        print("👀 Browser should be visible now!")
        
        # Create a page
        page = await browser.new_page()
        
        print("🔍 Navigating to Google...")
        await page.goto("https://www.google.com")
        
        print("✅ Page loaded! Keeping browser open for 10 seconds...")
        await asyncio.sleep(10)
        
        print("🔚 Closing browser...")
        await browser.close()

if __name__ == "__main__":
    print("🚀 Testing direct Playwright visible browser...")
    print("📝 This bypasses crawl4ai to test if the issue is with the system")
    input("Press Enter to start...")
    
    try:
        asyncio.run(test_direct_playwright())
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 You might need to install playwright browsers: playwright install") 