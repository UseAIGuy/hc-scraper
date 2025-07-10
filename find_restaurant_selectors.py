import asyncio
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def find_restaurant_selectors():
    """Find the exact CSS selectors used for restaurant listings on HappyCow"""
    print("🔍 Analyzing HappyCow Dallas page for restaurant selectors...")
    
    async with AsyncWebCrawler(headless=True) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            screenshot=False,
            verbose=False
        )
        
        url = 'https://www.happycow.net/north_america/usa/texas/dallas/'
        result = await crawler.arun(url=url, config=config)
        
        if not result.success:
            print(f"❌ Failed to load page")
            return
        
        html = result.html
        print(f"✅ Page loaded successfully ({len(html)} chars)")
        
        # Test different potential selectors
        test_selectors = [
            '.card-listing',
            '.venue-list-item', 
            '.venue-item-link',
            '.city-results',
            '[class*="venue"]',
            '[class*="listing"]',
            '[class*="card"]',
            'a[href*="/venues/"]',
            'a[href*="/restaurants/"]'
        ]
        
        print("\n🎯 Testing potential CSS selectors...")
        
        for selector in test_selectors:
            # Simulate what crawl4ai would find with this selector
            if selector == '.card-listing':
                pattern = r'<[^>]*class="[^"]*card-listing[^"]*"[^>]*>'
            elif selector == '.venue-list-item':
                pattern = r'<[^>]*class="[^"]*venue-list-item[^"]*"[^>]*>'
            elif selector == '.venue-item-link':
                pattern = r'<[^>]*class="[^"]*venue-item-link[^"]*"[^>]*>'
            elif selector == '.city-results':
                pattern = r'<[^>]*class="[^"]*city-results[^"]*"[^>]*>'
            elif selector == '[class*="venue"]':
                pattern = r'<[^>]*class="[^"]*venue[^"]*"[^>]*>'
            elif selector == '[class*="listing"]':
                pattern = r'<[^>]*class="[^"]*listing[^"]*"[^>]*>'
            elif selector == '[class*="card"]':
                pattern = r'<[^>]*class="[^"]*card[^"]*"[^>]*>'
            elif selector == 'a[href*="/venues/"]':
                pattern = r'<a[^>]*href="[^"]*\/venues\/[^"]*"[^>]*>'
            elif selector == 'a[href*="/restaurants/"]':
                pattern = r'<a[^>]*href="[^"]*\/restaurants\/[^"]*"[^>]*>'
            else:
                continue
                
            matches = re.findall(pattern, html)
            print(f"  {selector}: {len(matches)} matches")
            
            if matches and len(matches) > 0:
                print(f"    📝 Sample: {matches[0][:120]}...")
        
        # Look for restaurant/venue links specifically
        print("\n🔗 Looking for restaurant/venue links...")
        venue_links = re.findall(r'<a[^>]*href="([^"]*(?:venue|restaurant)[^"]*)"[^>]*>', html)
        print(f"Found {len(venue_links)} venue/restaurant links")
        if venue_links:
            for i, link in enumerate(venue_links[:5]):
                print(f"  {i+1}. {link}")
        
        # Look for the specific structure used by HappyCow
        print("\n📋 Looking for listing structures...")
        
        # Search for div elements that might contain restaurant data
        div_patterns = [
            r'<div[^>]*class="[^"]*(?:card|venue|listing|restaurant)[^"]*"[^>]*>.*?</div>',
            r'<article[^>]*class="[^"]*(?:card|venue|listing|restaurant)[^"]*"[^>]*>.*?</article>',
            r'<li[^>]*class="[^"]*(?:card|venue|listing|restaurant)[^"]*"[^>]*>.*?</li>'
        ]
        
        for i, pattern in enumerate(div_patterns):
            matches = re.findall(pattern, html, re.DOTALL)
            print(f"  Pattern {i+1}: {len(matches)} matches")
            if matches:
                # Show first match truncated
                sample = matches[0][:300] + "..." if len(matches[0]) > 300 else matches[0]
                print(f"    📝 Sample: {sample}")
        
        # Save the full HTML for manual inspection
        with open('full_dallas_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n💾 Saved full HTML to 'full_dallas_page.html' ({len(html)} chars)")

if __name__ == "__main__":
    asyncio.run(find_restaurant_selectors()) 