#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup

def test_website_selectors():
    """Test what elements the website CSS selectors are finding"""
    
    # Test with a real restaurant page
    test_file = 'html_analysis/sample_5.html'
    
    if not os.path.exists(test_file):
        print(f"❌ {test_file} not found")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("🔍 TESTING WEBSITE CSS SELECTORS")
    print("=" * 60)
    print(f"📄 Testing with: {test_file}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Test each website selector
    website_selectors = [
        "a[title='Visit their website'][href]",
        "a[data-analytics='default-website'][href]", 
        "a[title*='website'][href]:not([href*='happycow.net'])",
        "a[rel*='nofollow'][href^='http']:not([href*='happycow.net']):not([href*='facebook']):not([href*='instagram']):not([href*='twitter'])"
    ]
    
    for i, selector in enumerate(website_selectors, 1):
        print(f"\n{i}️⃣ TESTING SELECTOR: {selector}")
        print("-" * 50)
        
        try:
            elements = soup.select(selector)
            print(f"   Found {len(elements)} elements")
            
            for j, element in enumerate(elements[:3], 1):  # Show first 3
                href = element.get('href', 'NO_HREF')
                text = element.get_text(strip=True)
                title = element.get('title', 'NO_TITLE')
                analytics = element.get('data-analytics', 'NO_ANALYTICS')
                
                print(f"   Element {j}:")
                print(f"     href: {href}")
                print(f"     text: {text[:50]}...")
                print(f"     title: {title}")
                print(f"     data-analytics: {analytics}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Also test what the current selectors find
    print(f"\n🔍 TESTING CURRENT LOGIC")
    print("-" * 50)
    
    # Test the actual website link we know exists
    actual_website_link = soup.find('a', href='http://www.aliveandwellinmaui.com')
    if actual_website_link:
        print("✅ Found the actual website link:")
        print(f"   href: {actual_website_link.get('href')}")
        print(f"   text: {actual_website_link.get_text(strip=True)}")
        print(f"   title: {actual_website_link.get('title')}")
        print(f"   data-analytics: {actual_website_link.get('data-analytics')}")
        print(f"   class: {actual_website_link.get('class')}")
        print(f"   rel: {actual_website_link.get('rel')}")
    else:
        print("❌ Could not find the actual website link")

if __name__ == "__main__":
    test_website_selectors() 