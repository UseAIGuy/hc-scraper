#!/usr/bin/env python3
"""
Quick script to check what CSS selectors actually exist on Dallas HappyCow page
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from bs4 import BeautifulSoup

async def check_dallas_selectors():
    """Check what selectors actually exist on Dallas page"""
    
    print("🔍 CHECKING DALLAS PAGE SELECTORS")
    print("=" * 50)
    
    async with AsyncWebCrawler(headless=True) as crawler:
        # Load Dallas page with basic body selector
        print("📄 Loading Dallas page...")
        result = await crawler.arun(
            url='https://www.happycow.net/north_america/usa/texas/dallas/',
            config=CrawlerRunConfig(wait_for='css:body', page_timeout=15000)
        )
        
        if not result.success:
            print(f"❌ Failed to load page: {result.error_message}")
            return
        
        soup = BeautifulSoup(result.html, 'html.parser')
        print(f"✅ Page loaded successfully ({len(result.html):,} chars)")
        
        # Check our current problematic selectors
        print("\n🎯 CURRENT SELECTORS (causing timeout):")
        current_selectors = [
            '.card-listing',
            '.venue-list-item', 
            '.no-results'
        ]
        
        for selector in current_selectors:
            count = len(soup.select(selector))
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {selector}: {count} found")
        
        # Check alternative selectors
        print("\n🔍 ALTERNATIVE SELECTORS:")
        alt_selectors = [
            '.venue-item',
            '.listing-item',
            '.venue',
            '.listing',
            '.restaurant',
            '.content',
            '.main-content',
            '.search-results',
            '.results'
        ]
        
        working_selectors = []
        for selector in alt_selectors:
            count = len(soup.select(selector))
            status = "✅" if count > 0 else "❌"
            print(f"  {status} {selector}: {count} found")
            if count > 0:
                working_selectors.append(selector)
        
        # Check for restaurant links (the actual content we need)
        print("\n🍽️ RESTAURANT LINKS:")
        review_links = soup.find_all('a', href=lambda x: x and '/reviews/' in x)
        print(f"  Restaurant links found: {len(review_links)}")
        
        if review_links:
            print(f"  First few restaurants:")
            for i, link in enumerate(review_links[:3]):
                name = link.get_text(strip=True)
                href = link.get('href')
                print(f"    {i+1}. {name} -> {href}")
        
        # Find what classes contain the restaurant links
        print("\n📦 PARENT CONTAINERS OF RESTAURANT LINKS:")
        if review_links:
            parent_classes = set()
            for link in review_links:
                parent = link.parent
                while parent and parent.name != 'body':
                    classes = parent.get('class', [])
                    if classes:
                        parent_classes.update(classes)
                    parent = parent.parent
            
            # Test these classes as potential selectors
            print("  Testing parent classes as selectors:")
            for cls in sorted(parent_classes)[:10]:  # Top 10 most common
                selector = f'.{cls}'
                count = len(soup.select(selector))
                if count > 0:
                    print(f"    ✅ {selector}: {count} found")
        
        # Recommend working selectors
        print("\n💡 RECOMMENDED WORKING SELECTORS:")
        if working_selectors:
            recommended = ', '.join(working_selectors[:3])  # Top 3
            print(f"  {recommended}")
        else:
            print("  body (fallback - always works)")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(check_dallas_selectors()) 