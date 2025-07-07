#!/usr/bin/env python3
"""
Debug script to inspect HappyCow HTML structure and find actual restaurant listings
"""
import asyncio
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def inspect_happycow_html():
    """Inspect the actual HTML structure to find restaurant listings"""
    
    async with AsyncWebCrawler(headless=True, verbose=True) as crawler:
        
        print("🔍 Fetching HappyCow Austin page...")
        result = await crawler.arun(
            url="https://www.happycow.net/north_america/usa/texas/austin/",
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=30000,
                delay_before_return_html=2.0
            )
        )
        
        if not result.success:
            print(f"❌ Failed to fetch page: {result.error_message}")
            return
        
        html = result.html
        print(f"✅ Fetched {len(html)} characters of HTML")
        
        # Look for common patterns that might contain restaurant data
        patterns_to_check = [
            (r'href="[^"]*reviews[^"]*"[^>]*>([^<]+)', "Review links"),
            (r'<a[^>]*href="(/[^"]*)"[^>]*>([^<]*(?:restaurant|cafe|kitchen|grill|bar|food)[^<]*)</a>', "Food-related links"),
            (r'<div[^>]*class="[^"]*venue[^"]*"[^>]*>(.*?)</div>', "Venue divs"),
            (r'<div[^>]*class="[^"]*listing[^"]*"[^>]*>(.*?)</div>', "Listing divs"),
            (r'data-venue-id="([^"]*)"', "Venue IDs"),
            (r'<h\d[^>]*>([^<]*(?:restaurant|cafe|kitchen|grill|bar)[^<]*)</h\d>', "Restaurant headings"),
        ]
        
        print("\n" + "="*60)
        print("🔍 ANALYZING HTML PATTERNS")
        print("="*60)
        
        for pattern, description in patterns_to_check:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            print(f"\n📋 {description}: Found {len(matches)} matches")
            
            # Show first few matches
            for i, match in enumerate(matches[:5]):
                if isinstance(match, tuple):
                    print(f"  {i+1}. {match}")
                else:
                    print(f"  {i+1}. {match[:100]}{'...' if len(match) > 100 else ''}")
        
        # Look for specific HappyCow structure
        print(f"\n" + "="*60)
        print("🎯 LOOKING FOR HAPPYCOW-SPECIFIC PATTERNS")
        print("="*60)
        
        # Check for venue cards/items
        venue_patterns = [
            r'<div[^>]*data-venue[^>]*>(.*?)</div>',
            r'<article[^>]*>(.*?)</article>',
            r'<li[^>]*class="[^"]*venue[^"]*"[^>]*>(.*?)</li>',
            r'<div[^>]*class="[^"]*card[^"]*"[^>]*>(.*?)</div>',
        ]
        
        for pattern in venue_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            if matches:
                print(f"\n🎯 Found {len(matches)} potential venue containers with pattern: {pattern}")
                # Show first match in detail
                if matches:
                    first_match = matches[0][:500]
                    print(f"First match preview:\n{first_match}...")
                    break
        
        # Save a sample of the HTML for manual inspection
        sample_html = html[:50000]  # First 50KB
        with open("sample_happycow.html", "w", encoding="utf-8") as f:
            f.write(sample_html)
        print(f"\n💾 Saved first 50KB of HTML to 'sample_happycow.html' for manual inspection")

if __name__ == "__main__":
    asyncio.run(inspect_happycow_html()) 