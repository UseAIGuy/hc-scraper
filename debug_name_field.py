#!/usr/bin/env python3

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_extraction_engine import EnhancedExtractionEngine

async def debug_name_field():
    """Debug what the extraction engine returns for the name field"""
    
    # Test with a real restaurant page
    test_file = 'html_analysis/sample_5.html'
    
    if not os.path.exists(test_file):
        print(f"❌ {test_file} not found")
        return
    
    with open(test_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print("🔍 DEBUGGING NAME FIELD EXTRACTION")
    print("=" * 60)
    print(f"📄 Testing with: {test_file}")
    
    # Create extraction engine
    engine = EnhancedExtractionEngine()
    
    # Extract data
    try:
        extracted_data = await engine.extract_restaurant_data(html_content)
        
        print(f"\n✅ Extraction completed successfully")
        print(f"📊 Total fields extracted: {len(extracted_data)}")
        
        # Focus on the name field
        name_value = extracted_data.get('name')
        print(f"\n🎯 NAME FIELD ANALYSIS:")
        print(f"   Value: {repr(name_value)}")
        print(f"   Type: {type(name_value)}")
        print(f"   Is None: {name_value is None}")
        print(f"   Is empty string: {name_value == ''}")
        print(f"   Is just whitespace: {name_value.strip() == '' if isinstance(name_value, str) else 'N/A'}")
        
        # Show all extracted fields
        print(f"\n📋 ALL EXTRACTED FIELDS:")
        for key, value in extracted_data.items():
            print(f"   {key}: {repr(value)}")
            
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_name_field()) 