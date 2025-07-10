import asyncio
import os
import random
from dotenv import load_dotenv
from scraper import HappyCowScraper, StealthConfig
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# Load environment variables
load_dotenv()

class VisibleHappyCowScraper(HappyCowScraper):
    """HappyCow scraper that runs with visible browser window for debugging"""
    
    async def _create_crawler_with_stealth(self, proxy_url=None):
        """Override to create visible crawler"""
        print("🌐 Creating VISIBLE browser window...")
        
        # Use provided proxy or get random proxy
        proxy = proxy_url or StealthConfig.get_random_proxy()
        
        # Enhanced browser arguments for stealth (same as parent but visible)
        browser_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            
            # Anti-detection flags
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-extensions",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            
            # Make it look like a real browser
            "--window-size=1920,1080",
            "--start-maximized",
            "--disable-infobars",
            "--disable-notifications",
            "--disable-popup-blocking",
            "--disable-save-password-bubble",
            
            # Add realistic browser flags
            "--enable-automation=false",
            "--disable-browser-side-navigation",
            "--no-zygote",
            "--single-process",
        ]
        
        # Add proxy if available
        if proxy:
            print(f"🌐 Using proxy: {proxy}")
            browser_args.append(f"--proxy-server={proxy}")
            
            # For authenticated proxies like Decodo, we need to handle auth differently
            if "@" in proxy:
                # Format: http://username:password@host:port
                print("🔐 Using authenticated proxy")
        
        # Store configuration for use in arun() calls (same as parent)
        self.stealth_config = CrawlerRunConfig(
            user_agent=random.choice(StealthConfig.USER_AGENTS),
            wait_for="css:.card-listing, .city-results, .venue-list-item",
            delay_before_return_html=random.uniform(2.0, 5.0),
            js_code="""
                // Remove ALL automation indicators
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                
                // Add realistic browser properties
                window.chrome = {runtime: {}};
                Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
                
                // Simulate human mouse and scroll behavior
                let mouseX = Math.random() * window.innerWidth;
                let mouseY = Math.random() * window.innerHeight;
                
                // Add mouse movement event listeners
                document.addEventListener('mousemove', (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                });
                
                // Random human-like scrolling
                function humanScroll() {
                    const scrollAmount = Math.random() * 200 + 100;
                    const scrollDelay = Math.random() * 1000 + 500;
                    
                    setTimeout(() => {
                        window.scrollBy(0, scrollAmount);
                        if (Math.random() > 0.7) humanScroll(); // 30% chance to scroll again
                    }, scrollDelay);
                }
                
                // Start human behavior after page load
                setTimeout(() => {
                    humanScroll();
                    
                    // Simulate reading time
                    setTimeout(() => {
                        if (Math.random() > 0.5) {
                            window.scrollTo(0, 0); // Sometimes scroll back to top
                        }
                    }, Math.random() * 3000 + 2000);
                }, Math.random() * 2000 + 1000);
                
                // Add realistic timing
                const originalSetTimeout = window.setTimeout;
                window.setTimeout = function(fn, delay) {
                    return originalSetTimeout(fn, delay + Math.random() * 100);
                };
            """,
            css_selector="body",
            screenshot=False,
            verbose=False
        )
        
        # Create crawler with browser arguments - THE KEY DIFFERENCE: headless=False
        print("👀 Browser window should be opening now...")
        return AsyncWebCrawler(
            headless=False,  # THIS IS THE KEY CHANGE!
            browser_type="chromium", 
            chrome_args=browser_args
        )

async def test_visible_scraping():
    """Test scraping with visible browser for debugging"""
    print("🔍 Testing scraper with VISIBLE browser window...")
    
    # Get Supabase config from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set in .env file")
        return
    
    # Create our VISIBLE scraper instance
    scraper = VisibleHappyCowScraper(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        use_local_llm=True,
        max_restaurants=1
    )
    
    try:
        async with scraper:
            print("🏙️ Starting visible scrape for Dallas, Texas...")
            print("👀 You should see a browser window open!")
            print("⏱️ The browser will pause on pages so you can inspect them...")
            
            # Test city lookup first
            city_path = scraper._get_city_path("dallas_texas")
            print(f"📍 City path: {city_path}")
            
            # Test scraping with visible browser
            result = await scraper.scrape_city_complete(
                city_name="dallas_texas", 
                max_restaurants=1, 
                city_path=city_path
            )
            
            print("\n📊 RESULTS:")
            print(f"Success: {result.get('success', False)}")
            print(f"Error: {result.get('error', 'None')}")
            print(f"Listings found: {result.get('listings_found', 0)}")
            print(f"Restaurants scraped: {result.get('restaurants_scraped', 0)}")
            print(f"Restaurants saved: {result.get('restaurants_saved', 0)}")
            
    except Exception as e:
        print(f"❌ Error during visible scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting VISIBLE browser test...")
    print("📝 This will open a browser window so you can see what's happening!")
    print("💡 You'll be able to inspect the page, see what selectors exist, etc.")
    input("Press Enter to continue...")
    
    asyncio.run(test_visible_scraping()) 