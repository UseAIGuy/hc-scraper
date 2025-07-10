#!/usr/bin/env python3

import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_city_extraction_regex():
    """Test the regex pattern used for city listing extraction"""
    
    # Load a sample city page to test against
    sample_files = [
        'city_page_sample.html',
        'dallas_page_sample.html', 
        'full_dallas_page.html'
    ]
    
    for sample_file in sample_files:
        if os.path.exists(sample_file):
            print(f"\n🔍 TESTING REGEX PATTERN ON: {sample_file}")
            print("=" * 60)
            
            with open(sample_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            print(f"📄 File size: {len(html_content)} characters")
            
            # The actual regex pattern from scraper.py
            review_pattern = r'<a[^>]*href="(/reviews/[^"]*)"[^>]*>([^<]+)</a>'
            matches = re.findall(review_pattern, html_content, re.IGNORECASE)
            
            print(f"🎯 Found {len(matches)} total matches")
            
            # Filter out /update URLs (as done in the actual code)
            filtered_matches = []
            for url, name in matches:
                if url.endswith('/update') or '/update/' in url:
                    print(f"🚫 Skipping update URL: {url}")
                    continue
                
                # Clean up the name
                name = re.sub(r'<[^>]+>', '', name).strip()
                if name and len(name) > 2:
                    filtered_matches.append((url, name))
            
            print(f"✅ After filtering: {len(filtered_matches)} valid restaurants")
            print("\nFirst 10 matches:")
            for i, (url, name) in enumerate(filtered_matches[:10]):
                print(f"  {i+1:2d}. {name} → {url}")
            
            if len(filtered_matches) > 10:
                print(f"     ... and {len(filtered_matches) - 10} more")
            
            # Look for specific patterns that might be causing issues
            print(f"\n🔍 DEBUGGING ANALYSIS:")
            print(f"   - Empty names: {sum(1 for _, name in matches if not name.strip())}")
            print(f"   - Names with HTML: {sum(1 for _, name in matches if '<' in name)}")
            print(f"   - Update URLs: {sum(1 for url, _ in matches if url.endswith('/update') or '/update/' in url)}")
            
            # Show some raw matches for debugging
            print(f"\n📝 Raw matches (first 5):")
            for i, (url, name) in enumerate(matches[:5]):
                print(f"  {i+1}. URL: {url}")
                print(f"     NAME: '{name}'")
                print(f"     CLEANED: '{re.sub(r'<[^>]+>', '', name).strip()}'")
                print()
            
            break
    else:
        print("❌ No sample city page files found!")
        print("Available files:", [f for f in os.listdir('.') if f.endswith('.html')])

if __name__ == "__main__":
    test_city_extraction_regex() 