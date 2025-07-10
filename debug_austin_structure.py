#!/usr/bin/env python3
"""
Debug script to analyze Austin's HTML structure and find why selectors fail
"""

import re
from bs4 import BeautifulSoup

def analyze_austin_html():
    """Analyze the saved Austin HTML to find the actual structure"""
    
    print("🔍 ANALYZING AUSTIN HTML STRUCTURE")
    print("=" * 50)
    
    try:
        with open('austin_page_raw.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print("❌ austin_page_raw.html not found - run debug_austin_page_content.py first")
        return
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print(f"📄 HTML size: {len(html_content):,} characters")
    
    # Check for our expected selectors
    print("\n🎯 CHECKING EXPECTED SELECTORS:")
    print("-" * 30)
    
    card_listings = soup.select('.card-listing')
    venue_items = soup.select('.venue-list-item') 
    no_results = soup.select('.no-results')
    
    print(f"  .card-listing: {len(card_listings)} found")
    print(f"  .venue-list-item: {len(venue_items)} found") 
    print(f"  .no-results: {len(no_results)} found")
    
    # Check for restaurant links
    print("\n🍽️ CHECKING RESTAURANT LINKS:")
    print("-" * 30)
    
    # Our current regex pattern
    current_pattern = r'<h4[^>]*><a[^>]*href="(/reviews/[^"]*)"[^>]*>([^<]+)</a></h4>'
    current_matches = re.findall(current_pattern, html_content, re.IGNORECASE)
    print(f"  Current regex pattern: {len(current_matches)} matches")
    
    # Check for any review links at all
    all_review_links = soup.find_all('a', href=re.compile(r'/reviews/'))
    print(f"  All /reviews/ links: {len(all_review_links)} found")
    
    # Analyze the structure around review links
    print("\n🔬 ANALYZING REVIEW LINK STRUCTURE:")
    print("-" * 40)
    
    if all_review_links:
        for i, link in enumerate(all_review_links[:5]):  # First 5 links
            href = link.get('href', '')
            text = link.get_text(strip=True)
            parent = link.parent
            parent_tag = parent.name if parent else 'None'
            parent_class = parent.get('class', []) if parent else []
            
            print(f"  Link {i+1}:")
            print(f"    Text: '{text}'")
            print(f"    Href: {href}")
            print(f"    Parent: <{parent_tag}> class={parent_class}")
            
            # Check grandparent too
            grandparent = parent.parent if parent else None
            if grandparent:
                gp_tag = grandparent.name
                gp_class = grandparent.get('class', [])
                print(f"    Grandparent: <{gp_tag}> class={gp_class}")
            print()
    
    # Look for common listing containers
    print("\n📦 CHECKING COMMON LISTING CONTAINERS:")
    print("-" * 40)
    
    containers_to_check = [
        '.listing', '.listings', '.restaurant-list', '.venue-list',
        '.search-results', '.results', '.content', '.main-content',
        '[class*="listing"]', '[class*="venue"]', '[class*="restaurant"]',
        '[class*="card"]', '[class*="item"]'
    ]
    
    for selector in containers_to_check:
        elements = soup.select(selector)
        if elements:
            print(f"  {selector}: {len(elements)} found")
            # Show classes of first element
            if elements[0].get('class'):
                print(f"    First element classes: {elements[0].get('class')}")
    
    # Check for JavaScript-rendered content indicators
    print("\n⚡ CHECKING FOR DYNAMIC CONTENT:")
    print("-" * 35)
    
    # Look for loading indicators
    loading_indicators = soup.find_all(text=re.compile(r'loading|Loading', re.IGNORECASE))
    print(f"  'Loading' text found: {len(loading_indicators)} times")
    
    # Look for JavaScript that might render content
    scripts = soup.find_all('script')
    js_with_listings = [s for s in scripts if s.string and ('listing' in s.string.lower() or 'restaurant' in s.string.lower())]
    print(f"  Scripts mentioning listings/restaurants: {len(js_with_listings)}")
    
    # Check for data attributes that might contain restaurant data
    print("\n📊 CHECKING FOR DATA ATTRIBUTES:")
    print("-" * 35)
    
    data_elements = soup.find_all(attrs=lambda x: x and any(k.startswith('data-') for k in x.keys()))
    data_with_restaurant = [e for e in data_elements if any('restaurant' in str(v).lower() or 'venue' in str(v).lower() for v in e.attrs.values() if isinstance(v, str))]
    print(f"  Elements with restaurant/venue data attributes: {len(data_with_restaurant)}")
    
    if data_with_restaurant:
        for i, elem in enumerate(data_with_restaurant[:3]):
            print(f"    Element {i+1}: {elem.name} {dict(elem.attrs)}")

if __name__ == "__main__":
    analyze_austin_html() 