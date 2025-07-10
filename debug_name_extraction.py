#!/usr/bin/env python3
"""
Debug script to analyze why name extraction is failing
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

async def debug_name_extraction():
    """Debug name extraction for a specific restaurant page"""
    
    # Test with the restaurant that's failing
    url = 'https://www.happycow.net/reviews/iconic-vegan-cafe-dallas-359899'
    
    print("🔍 DEBUGGING NAME EXTRACTION")
    print("=" * 50)
    print(f"URL: {url}")
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0
        )
        
        try:
            result = await crawler.arun(url=url, config=config)
            html_content = result.html if hasattr(result, 'html') else str(result)
            
            if not html_content:
                print("❌ Failed to get HTML content")
                return
                
            print(f"✅ Got HTML content: {len(html_content):,} characters")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            print("\n🎯 TESTING NAME SELECTORS:")
            print("-" * 30)
            
            # Test each selector from the field mapping
            selectors = [
                "h1[itemprop='name']",
                "h1.header-title", 
                ".venue h1",
                "main h1",
                ".content h1",
                ".venue-title"
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for i, el in enumerate(elements):
                        text = el.get_text(strip=True)
                        print(f"✅ {selector} [{i}] -> '{text}'")
                else:
                    print(f"❌ {selector} -> No matches")
            
            print("\n🔍 ANALYZING HTML STRUCTURE:")
            print("-" * 30)
            
            # Find all h1 tags
            h1_tags = soup.find_all('h1')
            print(f"Total h1 tags found: {len(h1_tags)}")
            
            for i, h1 in enumerate(h1_tags):
                classes = h1.get('class', [])
                itemprop = h1.get('itemprop', '')
                text = h1.get_text(strip=True)
                print(f"H1[{i}]: classes={classes}, itemprop='{itemprop}', text='{text}'")
            
            # Check for structured data
            print("\n📋 STRUCTURED DATA CHECK:")
            print("-" * 30)
            
            name_elements = soup.find_all(attrs={"itemprop": "name"})
            print(f"Elements with itemprop='name': {len(name_elements)}")
            
            for i, el in enumerate(name_elements):
                text = el.get_text(strip=True)
                content = el.get('content', '')
                tag = el.name
                print(f"Name[{i}]: <{tag}> text='{text}' content='{content}'")
            
            # Check meta tags
            print("\n🏷️ META TAGS CHECK:")
            print("-" * 30)
            
            og_title = soup.find("meta", property="og:title")
            if og_title:
                print(f"og:title: '{og_title.get('content', '')}'")
            else:
                print("❌ No og:title found")
                
            title_tag = soup.find("title")
            if title_tag:
                print(f"<title>: '{title_tag.get_text(strip=True)}'")
            else:
                print("❌ No <title> found")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_name_extraction()) 