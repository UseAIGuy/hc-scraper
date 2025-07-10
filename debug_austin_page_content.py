#!/usr/bin/env python3
"""
Debug script to analyze Austin's HappyCow page content
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
import re

async def analyze_austin_page():
    """Fetch and analyze Austin's HappyCow page to see what HTML structure it contains"""
    
    austin_url = "https://www.happycow.net/north_america/usa/texas/austin/"
    
    print("🔍 ANALYZING AUSTIN'S HAPPYCOW PAGE")
    print("=" * 50)
    print(f"URL: {austin_url}")
    
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Try to fetch the page with minimal waiting
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=60000,  # Longer timeout
            delay_before_return_html=5.0,  # Wait for content to load
            screenshot=False,
            verbose=True
        )
        
        print("\n📡 Fetching Austin page...")
        result = await crawler.arun(url=austin_url, config=config)
        
        if not result.success:
            print(f"❌ Failed to fetch page: {result.error_message}")
            return
            
        print(f"✅ Successfully fetched page: {len(result.html)} characters")
        
        # Save the raw HTML for inspection
        with open("austin_page_raw.html", "w", encoding="utf-8") as f:
            f.write(result.html)
        print("💾 Saved raw HTML to: austin_page_raw.html")
        
        # Analyze the content
        print("\n🔍 CONTENT ANALYSIS:")
        print("-" * 30)
        
        # Check for our expected selectors
        selectors_to_check = [
            ".card-listing",
            ".venue-list-item", 
            ".no-results",
            ".restaurant-item",
            ".listing-item",
            ".venue-card",
            "h4 a[href*='/reviews/']",
            "a[href*='/reviews/']"
        ]
        
        for selector in selectors_to_check:
            # Convert CSS selector to simple text search for basic analysis
            if selector == ".card-listing":
                found = "card-listing" in result.html
            elif selector == ".venue-list-item":
                found = "venue-list-item" in result.html
            elif selector == ".no-results":
                found = "no-results" in result.html
            elif selector == ".restaurant-item":
                found = "restaurant-item" in result.html
            elif selector == ".listing-item":
                found = "listing-item" in result.html
            elif selector == ".venue-card":
                found = "venue-card" in result.html
            elif selector == "h4 a[href*='/reviews/']":
                found = bool(re.search(r'<h4[^>]*>.*?<a[^>]*href="[^"]*reviews[^"]*"', result.html, re.IGNORECASE | re.DOTALL))
            elif selector == "a[href*='/reviews/']":
                found = "/reviews/" in result.html
            else:
                found = False
                
            status = "✅ FOUND" if found else "❌ NOT FOUND"
            print(f"  {status}: {selector}")
        
        # Look for restaurant links
        print(f"\n🍽️ RESTAURANT LINKS ANALYSIS:")
        review_links = re.findall(r'href="([^"]*reviews[^"]*)"', result.html, re.IGNORECASE)
        print(f"  Found {len(review_links)} links containing 'reviews'")
        
        if review_links:
            print("  First 5 review links:")
            for i, link in enumerate(review_links[:5]):
                print(f"    {i+1}. {link}")
        
        # Check for common page elements
        print(f"\n📄 PAGE STRUCTURE ANALYSIS:")
        structure_checks = [
            ("Title tag", bool(re.search(r'<title[^>]*>([^<]+)</title>', result.html, re.IGNORECASE))),
            ("Body tag", "<body" in result.html.lower()),
            ("Main content div", bool(re.search(r'<div[^>]*class="[^"]*main[^"]*"', result.html, re.IGNORECASE))),
            ("Restaurant listings", bool(re.search(r'restaurant|venue|listing', result.html, re.IGNORECASE))),
            ("JavaScript present", "<script" in result.html.lower()),
            ("CSS classes", bool(re.search(r'class="[^"]*"', result.html))),
        ]
        
        for check_name, found in structure_checks:
            status = "✅ FOUND" if found else "❌ NOT FOUND"
            print(f"  {status}: {check_name}")
        
        # Extract title if present
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', result.html, re.IGNORECASE)
        if title_match:
            print(f"\n📰 Page Title: {title_match.group(1).strip()}")
        
        # Look for error messages or redirects
        print(f"\n🚨 ERROR/REDIRECT ANALYSIS:")
        error_indicators = [
            ("404 Not Found", "404" in result.html and "not found" in result.html.lower()),
            ("403 Forbidden", "403" in result.html and "forbidden" in result.html.lower()),
            ("Redirect", "redirect" in result.html.lower()),
            ("CAPTCHA", "captcha" in result.html.lower()),
            ("Bot detection", any(term in result.html.lower() for term in ["bot", "automation", "robot"])),
            ("JavaScript required", "javascript" in result.html.lower() and "required" in result.html.lower()),
        ]
        
        for error_name, found in error_indicators:
            status = "⚠️ DETECTED" if found else "✅ CLEAR"
            print(f"  {status}: {error_name}")
        
        # Check if page is mostly empty
        text_content = re.sub(r'<[^>]+>', '', result.html)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        print(f"\n📊 Content Stats:")
        print(f"  Total HTML size: {len(result.html):,} characters")
        print(f"  Text content size: {len(text_content):,} characters")
        print(f"  HTML/Text ratio: {len(result.html)/max(len(text_content), 1):.1f}:1")
        
        if len(text_content) < 500:
            print("  ⚠️ Very little text content - page may be empty or blocked")

if __name__ == "__main__":
    asyncio.run(analyze_austin_page()) 