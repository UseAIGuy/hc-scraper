#!/usr/bin/env python3
"""
Test Live Field Extraction

Test that the enhanced extraction engine correctly extracts vegan_status and cuisine_types
from a live HappyCow restaurant page.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from enhanced_extraction_engine import EnhancedExtractionEngine
from restaurant_field_mapping import RESTAURANT_FIELD_MAPPINGS

async def test_live_extraction():
    """Test extraction of fields from a live restaurant page"""
    
    # Test URL - a known restaurant page
    test_url = "https://www.happycow.net/reviews/nunos-tacos-vegmex-grill-dallas-174703"
    
    print(f"🌐 TESTING LIVE EXTRACTION: {test_url}")
    print("=" * 80)
    
    # Fetch the live page
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    print(f"✅ Successfully fetched page (status: {response.status})")
                else:
                    print(f"❌ Failed to fetch page (status: {response.status})")
                    return
        except Exception as e:
            print(f"❌ Error fetching page: {e}")
            return
    
    # Initialize extraction engine and parse HTML
    engine = EnhancedExtractionEngine()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\n🔍 EXTRACTION RESULTS:")
    print("-" * 40)
    
    # Test key fields
    fields_to_test = ["name", "vegan_status", "cuisine_types", "rating", "phone", "website"]
    
    for field_name in fields_to_test:
        if field_name in RESTAURANT_FIELD_MAPPINGS:
            field_mapping = RESTAURANT_FIELD_MAPPINGS[field_name]
            try:
                result = await engine._extract_field(soup, field_mapping, html_content, test_url)
                status = "✅" if result and result != "Unknown" else "❌"
                print(f"{status} {field_name:<15}: {result}")
            except Exception as e:
                print(f"❌ {field_name:<15}: Error - {e}")
    
    print("\n🎯 DETAILED ANALYSIS:")
    print("-" * 40)
    
    # Check for specific elements we expect
    print("📍 Looking for specific elements:")
    
    # Check for title
    title_element = soup.find('h1', attrs={'itemprop': 'name'}) or soup.find('h1', class_='header-title')
    if title_element:
        print(f"✅ Title element found: {title_element.get_text(strip=True)}")
    else:
        print("❌ No title element found")
    
    # Check for vegan status badges
    print("\n📱 Vegan status badges:")
    vegan_badges = soup.select('.label.bg-vegan')
    vegetarian_badges = soup.select('.label.bg-vegetarian')
    print(f"Vegan badges found: {len(vegan_badges)}")
    print(f"Vegetarian badges found: {len(vegetarian_badges)}")
    
    # Check for cuisine elements
    print("\n🍽️ Cuisine elements:")
    cuisine_elements = soup.select('.bg-health-food-store, [class*="bg-"][class*="food"], [class*="category-"]')
    print(f"Cuisine elements found: {len(cuisine_elements)}")
    for i, elem in enumerate(cuisine_elements[:3]):
        text = elem.get_text(strip=True)
        classes = elem.get('class') or []
        print(f"  [{i}] Text: '{text}' Classes: {classes}")
    
    # Check for structured data
    print("\n📊 Structured data:")
    rating_meta = soup.find('meta', attrs={'itemprop': 'ratingValue'})
    if rating_meta:
        print(f"✅ Rating meta found: {rating_meta.get('content')}")
    else:
        print("❌ No rating meta found")
    
    review_count_meta = soup.find('meta', attrs={'itemprop': 'reviewCount'})
    if review_count_meta:
        print(f"✅ Review count meta found: {review_count_meta.get('content')}")
    else:
        print("❌ No review count meta found")
    
    # Check for phone
    phone_elements = soup.select('a[href^="tel:"]')
    print(f"Phone elements found: {len(phone_elements)}")

if __name__ == "__main__":
    asyncio.run(test_live_extraction()) 