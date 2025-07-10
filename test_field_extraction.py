#!/usr/bin/env python3
"""
Test Field Extraction

Test that the enhanced extraction engine correctly extracts vegan_status and cuisine_types
with the updated selectors.
"""

import asyncio
from bs4 import BeautifulSoup
from enhanced_extraction_engine import EnhancedExtractionEngine
from restaurant_field_mapping import RESTAURANT_FIELD_MAPPINGS

async def test_field_extraction():
    """Test extraction of vegan_status and cuisine_types"""
    
    # Test file
    test_file = 'html_analysis/sample_5.html'
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"❌ {test_file} not found")
        return
    
    print(f"🧪 TESTING FIELD EXTRACTION - {test_file}")
    print("=" * 60)
    
    # Initialize extraction engine and parse HTML
    engine = EnhancedExtractionEngine()
    soup = BeautifulSoup(html_content, 'html.parser')
    test_url = "https://www.happycow.net/test"
    
    # Test vegan_status
    print("\n🌱 TESTING VEGAN STATUS EXTRACTION:")
    print("-" * 40)
    
    vegan_mapping = RESTAURANT_FIELD_MAPPINGS["vegan_status"]
    vegan_result = await engine._extract_field(soup, vegan_mapping, html_content, test_url)
    
    print(f"Field: vegan_status")
    print(f"Result: {vegan_result}")
    print(f"Type: {type(vegan_result)}")
    
    # Test cuisine_types
    print("\n🍽️ TESTING CUISINE TYPES EXTRACTION:")
    print("-" * 40)
    
    cuisine_mapping = RESTAURANT_FIELD_MAPPINGS["cuisine_types"]
    cuisine_result = await engine._extract_field(soup, cuisine_mapping, html_content, test_url)
    
    print(f"Field: cuisine_types")
    print(f"Result: {cuisine_result}")
    print(f"Type: {type(cuisine_result)}")
    
    # Test name field for comparison
    print("\n📝 TESTING NAME EXTRACTION (for comparison):")
    print("-" * 40)
    
    name_mapping = RESTAURANT_FIELD_MAPPINGS["name"]
    name_result = await engine._extract_field(soup, name_mapping, html_content, test_url)
    
    print(f"Field: name")
    print(f"Result: {name_result}")
    print(f"Type: {type(name_result)}")
    
    print("\n" + "=" * 60)
    print("🎯 SUMMARY:")
    print(f"✅ Name: {name_result}")
    print(f"✅ Vegan Status: {vegan_result}")
    print(f"✅ Cuisine Types: {cuisine_result}")

if __name__ == "__main__":
    asyncio.run(test_field_extraction()) 