#!/usr/bin/env python3

import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fixed_city_extraction_regex():
    """Test the corrected regex pattern for city listing extraction"""
    
    # Load a sample city page to test against
    test_file = 'raw_html_output.html'
    
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return
    
    print(f"🔍 TESTING FIXED REGEX PATTERN ON: {test_file}")
    print("=" * 60)
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"📄 File size: {len(html_content)} characters")
    
    # OLD BROKEN PATTERN
    old_pattern = r'<a[^>]*href="(/reviews/[^"]*)"[^>]*>([^<]+)</a>'
    old_matches = re.findall(old_pattern, html_content)
    print(f"\n❌ OLD PATTERN: {old_pattern}")
    print(f"❌ OLD MATCHES: {len(old_matches)}")
    if old_matches:
        for i, (url, name) in enumerate(old_matches[:3]):
            print(f"   {i+1}. URL: {url} | Name: '{name}'")
    
    # NEW CORRECT PATTERN - Based on actual HTML structure
    # Looking for: <h4><a href="/reviews/restaurant-name-city-id">Restaurant Name</a></h4>
    new_pattern = r'<h4[^>]*><a[^>]*href="(/reviews/[^"]*)"[^>]*>([^<]+)</a></h4>'
    new_matches = re.findall(new_pattern, html_content)
    print(f"\n✅ NEW PATTERN: {new_pattern}")
    print(f"✅ NEW MATCHES: {len(new_matches)}")
    
    if new_matches:
        print(f"\n🎯 EXTRACTED RESTAURANTS:")
        print("-" * 40)
        for i, (url, name) in enumerate(new_matches):
            print(f"{i+1:2d}. {name}")
            print(f"    URL: {url}")
            if i >= 9:  # Show first 10
                print(f"    ... and {len(new_matches) - 10} more")
                break
    else:
        print("❌ No matches found with new pattern either!")
        
        # Let's try a more flexible pattern
        flexible_pattern = r'<a[^>]*href="(/reviews/[^"#]*)"[^>]*[^>]*>([^<]+)</a>'
        flexible_matches = re.findall(flexible_pattern, html_content)
        print(f"\n🔍 FLEXIBLE PATTERN: {flexible_pattern}")
        print(f"🔍 FLEXIBLE MATCHES: {len(flexible_matches)}")
        if flexible_matches:
            for i, (url, name) in enumerate(flexible_matches[:5]):
                print(f"   {i+1}. URL: {url} | Name: '{name}'")

if __name__ == "__main__":
    test_fixed_city_extraction_regex() 