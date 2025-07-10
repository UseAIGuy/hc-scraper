#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup

def debug_structured_data():
    """Debug what structured data (microdata) exists on the restaurant page"""
    
    # Test with a real restaurant page
    test_file = 'html_analysis/sample_5.html'
    
    if not os.path.exists(test_file):
        print(f"❌ {test_file} not found")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("🔍 DEBUGGING STRUCTURED DATA (MICRODATA)")
    print("=" * 60)
    print(f"📄 Testing with: {test_file}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all elements with itemprop
    print("\n🏷️ ALL ITEMPROP ELEMENTS:")
    print("-" * 40)
    itemprop_elements = soup.find_all(attrs={"itemprop": True})
    for i, elem in enumerate(itemprop_elements[:20], 1):  # Limit to first 20
        itemprop = elem.get('itemprop')
        content = elem.get('content', elem.get_text(strip=True)[:100])
        href = elem.get('href', '')
        print(f"   {i:2d}. itemprop='{itemprop}' content='{content}' href='{href}'")
    
    # Specifically look for 'url' itemprop
    print("\n🎯 LOOKING FOR 'url' ITEMPROP (THE CULPRIT):")
    print("-" * 50)
    url_elements = soup.find_all(attrs={"itemprop": "url"})
    for i, elem in enumerate(url_elements, 1):
        content = elem.get('content', '')
        href = elem.get('href', '')
        text = elem.get_text(strip=True)
        tag = elem.name
        print(f"   {i}. <{tag} itemprop='url' content='{content}' href='{href}'>{text}</{tag}>")
    
    # Check for other structured data schemas
    print("\n📋 ITEMTYPE SCHEMAS:")
    print("-" * 30)
    itemtype_elements = soup.find_all(attrs={"itemtype": True})
    for elem in itemtype_elements:
        itemtype = elem.get('itemtype')
        print(f"   Found schema: {itemtype}")

if __name__ == "__main__":
    debug_structured_data() 