#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_extraction_engine import EnhancedExtractionEngine
from restaurant_field_mapping import RESTAURANT_FIELD_MAPPINGS
from bs4 import BeautifulSoup

async def debug_extraction_engine():
    """Debug the extraction engine step by step"""
    
    # Test with a real restaurant page
    test_file = 'html_analysis/sample_5.html'
    
    if not os.path.exists(test_file):
        print(f"❌ {test_file} not found")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("🔍 DEBUGGING EXTRACTION ENGINE STEP BY STEP")
    print("=" * 60)
    print(f"📄 Testing with: {test_file}")
    print(f"📏 HTML size: {len(html_content)} characters")
    
    # Test BeautifulSoup parsing
    soup = BeautifulSoup(html_content, 'html.parser')
    print(f"✅ BeautifulSoup parsed successfully")
    
    # Create extraction engine
    engine = EnhancedExtractionEngine()
    
    # Test name field extraction step by step
    print(f"\n🏷️ TESTING NAME FIELD EXTRACTION STEP BY STEP:")
    print("-" * 50)
    
    name_mapping = RESTAURANT_FIELD_MAPPINGS["name"]
    print(f"Field mapping: {name_mapping.field_name}")
    print(f"CSS selectors: {name_mapping.css_selectors}")
    print(f"Structured data paths: {name_mapping.structured_data_paths}")
    print(f"Meta tags: {name_mapping.meta_tags}")
    
    # Test each extraction method individually
    print(f"\n1️⃣ Testing structured data extraction:")
    structured_result = engine._extract_structured_data(soup, name_mapping.structured_data_paths)
    print(f"   Result: {structured_result}")
    
    print(f"\n2️⃣ Testing CSS selector extraction:")
    css_result = engine._extract_css_selector(soup, name_mapping.css_selectors)
    print(f"   Result: {css_result}")
    
    print(f"\n3️⃣ Testing meta tag extraction:")
    meta_result = engine._extract_meta_tags(soup, name_mapping.meta_tags)
    print(f"   Result: {meta_result}")
    
    print(f"\n4️⃣ Testing the full _extract_field method:")
    field_result = await engine._extract_field(soup, name_mapping, html_content, "test-url")
    print(f"   Result: {field_result}")
    
    # Now test the full extraction
    print(f"\n🔄 TESTING FULL EXTRACTION:")
    print("-" * 50)
    
    try:
        extracted_data = await engine.extract_restaurant_data("test-url", html_content)
        print(f"✅ Extraction completed successfully")
        print(f"📊 Total fields extracted: {len(extracted_data)}")
        
        if extracted_data:
            print(f"\n📋 EXTRACTED DATA:")
            for field, value in extracted_data.items():
                print(f"   {field}: {value}")
        else:
            print(f"❌ No data extracted - engine returned empty dict")
            
    except Exception as e:
        print(f"❌ Extraction failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_extraction_engine()) 