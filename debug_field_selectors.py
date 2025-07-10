#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from restaurant_field_mapping import RESTAURANT_FIELD_MAPPINGS

def test_field_selectors():
    """Test individual CSS selectors against the restaurant page"""
    
    # Test with a real restaurant page
    test_file = 'html_analysis/sample_5.html'
    
    if not os.path.exists(test_file):
        print(f"❌ {test_file} not found")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("🔍 TESTING INDIVIDUAL CSS SELECTORS")
    print("=" * 60)
    print(f"📄 Testing with: {test_file}")
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Test name field selectors specifically
    name_mapping = RESTAURANT_FIELD_MAPPINGS["name"]
    print(f"\n🏷️ TESTING NAME FIELD SELECTORS:")
    print("-" * 40)
    
    for i, selector in enumerate(name_mapping.css_selectors):
        print(f"\n{i+1}. Testing selector: {selector}")
        elements = soup.select(selector)
        print(f"   Found {len(elements)} elements")
        
        for j, element in enumerate(elements):
            text = element.get_text(strip=True)
            print(f"   Element {j+1}: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            if hasattr(element, 'attrs'):
                print(f"   Attributes: {element.attrs}")
    
    # Test a few other key fields
    test_fields = ["rating", "address", "phone", "website"]
    
    for field_name in test_fields:
        if field_name in RESTAURANT_FIELD_MAPPINGS:
            mapping = RESTAURANT_FIELD_MAPPINGS[field_name]
            print(f"\n🔍 TESTING {field_name.upper()} FIELD:")
            print("-" * 40)
            
            for i, selector in enumerate(mapping.css_selectors[:3]):  # Test first 3 selectors
                print(f"\n{i+1}. Testing selector: {selector}")
                elements = soup.select(selector)
                print(f"   Found {len(elements)} elements")
                
                for j, element in enumerate(elements[:2]):  # Show first 2 matches
                    text = element.get_text(strip=True)
                    print(f"   Element {j+1}: '{text[:50]}{'...' if len(text) > 50 else ''}'")

if __name__ == "__main__":
    test_field_selectors() 