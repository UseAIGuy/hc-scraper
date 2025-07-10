import asyncio
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def test_happycow_page():
    """Test the HappyCow Dallas page to identify correct CSS selectors"""
    print("🔍 Testing HappyCow Dallas page...")
    
    async with AsyncWebCrawler(headless=True) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            screenshot=False,
            verbose=False
        )
        
        url = 'https://www.happycow.net/north_america/usa/texas/dallas/'
        print(f"📍 Testing URL: {url}")
        
        result = await crawler.arun(url=url, config=config)
        
        print(f"✅ Success: {result.success}")
        
        if result.success:
            html = result.html
            print(f"📄 HTML length: {len(html)} characters")
            
            # Look for restaurant-related class names
            classes = re.findall(r'class=["\']([^"\']+)["\']', html)
            all_classes = set()
            for class_list in classes:
                all_classes.update(class_list.split())
            
            # Filter for restaurant/venue related classes
            restaurant_classes = [c for c in all_classes if any(word in c.lower() for word in 
                                ['restaurant', 'venue', 'listing', 'card', 'item', 'result', 'place'])]
            
            print(f"🏪 Restaurant-related classes found: {sorted(restaurant_classes)}")
            
            # Look for specific patterns in the HTML
            print("\n🔍 Looking for common patterns...")
            
            # Check for restaurant links
            restaurant_links = re.findall(r'<a[^>]*href="[^"]*restaurant[^"]*"[^>]*>', html)
            print(f"🔗 Restaurant links found: {len(restaurant_links)}")
            if restaurant_links:
                print(f"📝 Sample link: {restaurant_links[0][:100]}...")
            
            # Look for venue patterns
            venue_patterns = re.findall(r'<[^>]*class="[^"]*venue[^"]*"[^>]*>', html)
            print(f"🏢 Venue elements found: {len(venue_patterns)}")
            if venue_patterns:
                print(f"📝 Sample venue: {venue_patterns[0][:100]}...")
            
            # Look for listing patterns
            listing_patterns = re.findall(r'<[^>]*class="[^"]*listing[^"]*"[^>]*>', html)
            print(f"📋 Listing elements found: {len(listing_patterns)}")
            if listing_patterns:
                print(f"📝 Sample listing: {listing_patterns[0][:100]}...")
            
            # Check for common container classes
            container_classes = [c for c in all_classes if any(word in c.lower() for word in 
                               ['container', 'wrapper', 'content', 'main', 'body'])]
            print(f"📦 Container classes: {sorted(container_classes)}")
            
            # Save a sample of the HTML for manual inspection
            with open('dallas_page_sample.html', 'w', encoding='utf-8') as f:
                f.write(html[:10000])  # First 10KB
            print("💾 Saved first 10KB of HTML to 'dallas_page_sample.html' for inspection")
            
        else:
            error_msg = getattr(result, 'error_message', 'Unknown error')
            print(f"❌ Failed to load page: {error_msg}")

if __name__ == "__main__":
    asyncio.run(test_happycow_page()) 