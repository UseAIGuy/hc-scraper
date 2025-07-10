import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from css_selector_config import CSSConfigManager, PageType
from page_type_detector import detect_page_type
import random

class StealthConfig:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

async def test_dallas_selectors():
    """Test CSS selectors specifically for Dallas page"""
    dallas_url = "https://www.happycow.net/north_america/usa/texas/dallas/"
    
    print(f"🔍 Testing Dallas URL: {dallas_url}")
    
    # Detect page type
    page_type = detect_page_type(dallas_url)
    print(f"🎯 Detected page type: {page_type.value}")
    
    # Get CSS configuration
    crawl_config = CSSConfigManager.get_crawl_config_for_page_type(page_type)
    print(f"🔧 CSS Config: {crawl_config}")
    
    # Create crawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        print(f"📡 Crawling with wait_for: {crawl_config['wait_for']}")
        
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            user_agent=random.choice(StealthConfig.USER_AGENTS),
            wait_for=f"css:{crawl_config['wait_for']}",
            css_selector="body",
            screenshot=False,
            verbose=True
        )
        
        result = await crawler.arun(url=dallas_url, config=config)
        
        print(f"✅ Success: {result.success}")
        if result.success:
            print(f"📄 HTML Length: {len(result.html)} characters")
            
            # Check for venue-list-item elements
            if 'venue-list-item' in result.html:
                import re
                venue_count = len(re.findall(r'venue-list-item', result.html))
                print(f"🏪 Found {venue_count} venue-list-item elements")
            else:
                print("❌ No venue-list-item elements found")
                
            # Check for specific patterns
            patterns_to_check = [
                'venue-list-item',
                'card-listing', 
                '/reviews/',
                'data-id=',
                'class="venue'
            ]
            
            for pattern in patterns_to_check:
                count = result.html.count(pattern)
                print(f"🔍 Pattern '{pattern}': {count} occurrences")
                
        else:
            print(f"❌ Error: {getattr(result, 'error_message', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_dallas_selectors()) 