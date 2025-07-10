import asyncio
from crawl4ai import AsyncWebCrawler

async def test_simple_visible():
    """Test if crawl4ai can open a visible browser at all"""
    print("🧪 Testing basic visible browser functionality...")
    
    # Try different approaches to make browser visible
    approaches = [
        {
            "name": "Basic headless=False",
            "config": {"headless": False, "browser_type": "chromium"}
        },
        {
            "name": "With verbose and no extra args",
            "config": {"headless": False, "browser_type": "chromium", "verbose": True}
        },
        {
            "name": "With window args",
            "config": {
                "headless": False, 
                "browser_type": "chromium",
                "chrome_args": ["--start-maximized", "--disable-infobars"]
            }
        }
    ]
    
    for i, approach in enumerate(approaches):
        print(f"\n🧪 Approach {i+1}: {approach['name']}")
        
        try:
            crawler = AsyncWebCrawler(**approach['config'])
            
            async with crawler:
                print("🌐 Browser should be opening now...")
                print("👀 Look for a Chrome window!")
                
                # Give time to see the browser
                await asyncio.sleep(3)
                
                print("🔍 Navigating to Google...")
                result = await crawler.arun(url="https://www.google.com")
                
                # Check if we got a result and it has content
                if result and hasattr(result, 'success') and result.success:
                    if hasattr(result, 'html') and result.html:
                        print(f"✅ Success! Got {len(result.html)} characters")
                        print("🕐 Keeping browser open for 5 seconds so you can see it...")
                        await asyncio.sleep(5)
                        break  # If this works, stop trying other approaches
                    else:
                        print("❌ Success but no HTML content received")
                else:
                    print("❌ Request failed or no result")
                    
        except Exception as e:
            print(f"❌ Error with approach {i+1}: {e}")
            continue
    
    print("\n🤔 If you didn't see any browser windows, crawl4ai might have an issue with visible mode on your system")

if __name__ == "__main__":
    print("🚀 Testing if crawl4ai can show a visible browser...")
    print("📝 This will try multiple approaches to make the browser visible")
    input("Press Enter to start...")
    
    asyncio.run(test_simple_visible()) 