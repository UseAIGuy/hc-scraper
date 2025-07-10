#!/usr/bin/env python3
"""
Debug script to analyze what selectors are actually present on Dallas and Austin pages
"""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
import re
import random

async def analyze_city_page(city_name, url):
    """Analyze what selectors are actually present on a city page"""
    
    print(f"\n🔍 ANALYZING {city_name.upper()} PAGE SELECTORS")
    print("=" * 60)
    print(f"URL: {url}")
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        # Use the same config as the scraper
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            css_selector="body",
            screenshot=False,
            verbose=False
        )
        
        try:
            # Use the corrected API
            result = await crawler.arun(url=url, config=config)
            
            if not result.success:
                error_msg = getattr(result, 'error_message', 'Unknown crawler error')
                print(f"❌ Failed to fetch {city_name}: {error_msg}")
                return
            
            soup = BeautifulSoup(result.html, 'html.parser')
            print(f"📄 HTML size: {len(result.html):,} characters")
            
            # Check for our expected selectors
            print(f"\n🎯 CHECKING EXPECTED SELECTORS:")
            
            # Primary selectors we're looking for
            card_listings = soup.select('.card-listing')
            venue_items = soup.select('.venue-list-item')
            no_results = soup.select('.no-results')
            
            print(f"   .card-listing: {len(card_listings)} found")
            print(f"   .venue-list-item: {len(venue_items)} found")
            print(f"   .no-results: {len(no_results)} found")
            
            # Check for restaurant links
            review_links = soup.select('a[href*="/reviews/"]')
            print(f"   a[href*='/reviews/']: {len(review_links)} found")
            
            # Check for h4 structure (Dallas format)
            h4_links = soup.select('h4 a[href*="/reviews/"]')
            print(f"   h4 a[href*='/reviews/']: {len(h4_links)} found")
            
            # Check page title and main content
            title = soup.find('title')
            if title:
                print(f"   Page title: {title.get_text().strip()}")
            
            # Look for any div with restaurant-like content
            print(f"\n🔍 ANALYZING PAGE STRUCTURE:")
            
            # Check for common container classes
            containers = [
                '.venue-list', '.restaurant-list', '.listing-container',
                '.venues', '.results', '.search-results', '.listings'
            ]
            
            for container in containers:
                elements = soup.select(container)
                if elements:
                    print(f"   {container}: {len(elements)} found")
            
            # Check for any divs with class containing 'venue' or 'restaurant'
            venue_divs = soup.find_all('div', class_=re.compile(r'(venue|restaurant|listing|card)', re.I))
            print(f"   Divs with venue/restaurant/listing/card classes: {len(venue_divs)}")
            
            # Look at the actual structure of the first few elements
            if card_listings:
                print(f"\n📋 FIRST .card-listing STRUCTURE:")
                first_card = card_listings[0]
                classes = first_card.get('class')
                print(f"   Classes: {classes if classes else []}")
                print(f"   Contains links: {len(first_card.select('a[href*=\"/reviews/\"]'))}")
                
            if venue_items:
                print(f"\n📋 FIRST .venue-list-item STRUCTURE:")
                first_venue = venue_items[0]
                classes = first_venue.get('class')
                print(f"   Classes: {classes if classes else []}")
                print(f"   Contains links: {len(first_venue.select('a[href*=\"/reviews/\"]'))}")
            
            # Check if page might be showing "no results" or different content
            body_text = soup.get_text().lower()
            if 'no results' in body_text or 'no restaurants' in body_text:
                print(f"   ⚠️  Page may contain 'no results' content")
            
            if 'loading' in body_text:
                print(f"   ⚠️  Page may still be loading content")
                
            # Check for any JavaScript that might be blocking content
            scripts = soup.find_all('script')
            js_content = ' '.join([s.get_text() for s in scripts if s.get_text()])
            if 'cloudflare' in js_content.lower() or 'challenge' in js_content.lower():
                print(f"   ⚠️  Cloudflare/challenge detected in JavaScript")
            
            # Look for error messages or redirects
            if 'error' in body_text or 'not found' in body_text:
                print(f"   ⚠️  Error or 'not found' text detected")
                
            # Save the HTML for manual inspection
            filename = f"{city_name.lower()}_page_debug.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(result.html)
            print(f"   💾 Saved HTML to {filename}")
            
        except Exception as e:
            print(f"❌ Error analyzing {city_name}: {str(e)}")

async def main():
    """Analyze both Dallas and Austin pages"""
    
    cities = [
        ("Dallas", "https://www.happycow.net/north_america/usa/texas/dallas/"),
        ("Austin", "https://www.happycow.net/north_america/usa/texas/austin/"),
        ("NYC", "https://www.happycow.net/north_america/usa/new_york/new_york_city/")  # Working example
    ]
    
    for city_name, url in cities:
        await analyze_city_page(city_name, url)
        await asyncio.sleep(2)  # Brief delay between requests

if __name__ == "__main__":
    asyncio.run(main()) 