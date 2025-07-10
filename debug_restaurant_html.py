import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
import random
from bs4 import BeautifulSoup

async def get_restaurant_page_html():
    """Fetch actual restaurant page HTML to analyze structure"""
    
    url = 'https://www.happycow.net/reviews/dvegan-dallas-28073'
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=30000,
        delay_before_return_html=3.0,
        user_agent=random.choice(user_agents),
        wait_for='css:.venue, .content, .venue-info, .title, .main',
        js_code="""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """,
        verbose=False
    )
    
    print(f"🔍 Fetching restaurant page: {url}")
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        
        if result.success:
            print(f"✅ Success: {result.success}")
            print(f"📄 HTML Length: {len(result.cleaned_html):,}")
            
            # Save full HTML for analysis
            with open('restaurant_page_full.html', 'w', encoding='utf-8') as f:
                f.write(result.cleaned_html)
            
            # Parse and analyze structure
            soup = BeautifulSoup(result.cleaned_html, 'html.parser')
            
            print(f"\n🔍 ANALYZING HTML STRUCTURE:")
            
            # Look for restaurant name patterns
            print(f"\n📍 RESTAURANT NAME PATTERNS:")
            
            # Check h1 tags
            h1_tags = soup.find_all('h1')
            print(f"   Found {len(h1_tags)} h1 tags:")
            for i, h1 in enumerate(h1_tags[:5]):  # Show first 5
                text = h1.get_text(strip=True)
                classes = h1.get('class', [])
                print(f"     H1 #{i+1}: class={classes} text='{text[:60]}'")
            
            # Check title meta tag
            title_meta = soup.find("meta", property="og:title")
            if title_meta:
                print(f"   og:title meta: '{title_meta.get('content', '')}'")
            
            # Check page title
            title_tag = soup.find("title")
            if title_tag:
                print(f"   page title: '{title_tag.get_text(strip=True)}'")
            
            # Check specific selectors from field mapping
            selectors = [
                "h1.header-title",
                "h1[itemprop='name']", 
                ".venue-title",
                ".venue-name",
                ".restaurant-name",
                ".title",
                "[data-testid='venue-name']"
            ]
            
            print(f"\n🎯 TESTING FIELD MAPPING SELECTORS:")
            for selector in selectors:
                elements = soup.select(selector)
                print(f"   {selector}: {len(elements)} found")
                for elem in elements[:2]:  # Show first 2
                    text = elem.get_text(strip=True)
                    print(f"     Text: '{text[:60]}'")
            
            # Look for any element containing "D'Vegan"
            print(f"\n🔍 SEARCHING FOR 'D'Vegan' TEXT:")
            dvegan_elements = soup.find_all(text=lambda t: t and "D'Vegan" in str(t))
            for i, elem in enumerate(dvegan_elements[:5]):
                parent = elem.parent if elem.parent else None
                parent_tag = parent.name if parent else "None"
                parent_class = parent.get('class', []) if parent else []
                print(f"     Match #{i+1}: '{elem.strip()[:60]}' in <{parent_tag} class={parent_class}>")
            
            print(f"\n📁 Full HTML saved to: restaurant_page_full.html")
            
        else:
            print(f"❌ Failed: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(get_restaurant_page_html()) 