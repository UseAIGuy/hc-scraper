#!/usr/bin/env python3
"""
Debug the complete extraction flow to find where names are getting lost
"""

import asyncio
from crawl4ai import AsyncWebCrawler
from enhanced_extraction_engine import EnhancedExtractionEngine
from restaurant_field_mapping import RESTAURANT_FIELD_MAPPINGS

async def debug_extraction_flow():
    url = "https://www.happycow.net/reviews/iconic-vegan-cafe-dallas-359899"
    
    print("🔍 DEBUGGING COMPLETE EXTRACTION FLOW")
    print("=" * 50)
    print(f"URL: {url}")
    
    # Step 1: Get HTML
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=url)
        html_content = result.html
    
    print(f"✅ Got HTML content: {len(html_content):,} characters")
    
    # Step 2: Test Enhanced Extraction Engine
    print("\n🔍 TESTING ENHANCED EXTRACTION ENGINE:")
    print("-" * 50)
    
    engine = EnhancedExtractionEngine()
    
    # Test the extraction with both URL and HTML content
    extracted_data = await engine.extract_restaurant_data(url, html_content)
    
    print(f"📊 Extraction result:")
    print(f"   Name: {extracted_data.get('name', 'NOT FOUND')}")
    print(f"   All fields: {list(extracted_data.keys())}")
    
    # Step 3: Test specific name extraction
    print("\n🔍 TESTING NAME FIELD MAPPING:")
    print("-" * 50)
    
    name_mapping = RESTAURANT_FIELD_MAPPINGS['name']
    print(f"Name CSS selectors: {name_mapping.css_selectors}")
    
    # Test each selector manually
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for i, selector in enumerate(name_mapping.css_selectors):
        elements = soup.select(selector)
        if elements:
            print(f"✅ Selector {i+1}: '{selector}' -> '{elements[0].get_text().strip()}'")
        else:
            print(f"❌ Selector {i+1}: '{selector}' -> No matches")
    
    # Step 4: Debug the actual extraction method
    print("\n🔍 DEBUGGING EXTRACTION METHOD:")
    print("-" * 50)
    
    # Check what the engine's _extract_field method returns for name
    try:
        name_result = await engine._extract_field(soup, name_mapping, html_content, url)
        print(f"_extract_field('name') returned: {name_result}")
    except Exception as e:
        print(f"❌ _extract_field failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Test CSS selector extraction directly
    print("\n🔍 TESTING CSS SELECTOR EXTRACTION:")
    print("-" * 50)
    
    css_result = engine._extract_css_selector(soup, name_mapping.css_selectors)
    print(f"_extract_css_selector returned: {css_result}")
    
    # Step 6: Test structured data extraction
    print("\n🔍 TESTING STRUCTURED DATA EXTRACTION:")
    print("-" * 50)
    
    structured_result = engine._extract_structured_data(soup, name_mapping.structured_data_paths)
    print(f"_extract_structured_data returned: {structured_result}")
    
    # Step 7: Test field value processing
    print("\n🔍 TESTING FIELD VALUE PROCESSING:")
    print("-" * 50)
    
    if css_result:
        processed_result = engine._process_field_value(css_result, name_mapping)
        print(f"_process_field_value('{css_result}') returned: {processed_result}")

if __name__ == "__main__":
    asyncio.run(debug_extraction_flow()) 