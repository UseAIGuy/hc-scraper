#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test the actual data flow
def debug_model_conversion():
    """Debug what happens during model conversion"""
    
    # Simulate the data that would come from extraction
    print("🔍 DEBUGGING MODEL CONVERSION PROCESS")
    print("=" * 60)
    
    # This is what the extraction engine should return
    extracted_data = {
        'name': 'Primavega Restaurant - Ghost Kitchen',  # Correctly extracted
        'description': 'Some description...',
        'vegan_status': 'vegan',
        'cuisine_types': "['Health Store']",  # String that needs conversion
        'features': "[]",
        'recent_reviews': "[]"
    }
    
    # This is what the listing object contains (from city extraction)
    class MockListing:
        def __init__(self, name, url, city):
            self.name = name
            self.url = url
            self.city = city
    
    # OLD: listing with "Unknown Restaurant" (before regex fix)
    old_listing = MockListing("Unknown Restaurant", "/reviews/primavega-restaurant-dallas-330924", "Dallas")
    
    # NEW: listing with correct name (after regex fix)
    new_listing = MockListing("Primavega Restaurant - Ghost Kitchen", "/reviews/primavega-restaurant-dallas-330924", "Dallas")
    
    city_state_data = {
        'state': 'Texas',
        'city_path': 'dallas',
        'full_path': 'dallas_texas'
    }
    
    print("\n📊 SCENARIO 1: Extracted name exists (should work)")
    print("-" * 50)
    model_data = extracted_data.copy()
    model_data['name'] = model_data.get('name') or old_listing.name
    print(f"extracted_data.get('name'): {extracted_data.get('name')}")
    print(f"old_listing.name: {old_listing.name}")
    print(f"Final name: {model_data['name']}")
    print(f"✅ Expected: 'Primavega Restaurant - Ghost Kitchen'")
    
    print("\n📊 SCENARIO 2: Extracted name is empty (fallback to listing)")
    print("-" * 50)
    empty_extracted_data = {'name': '', 'description': 'test'}
    model_data = empty_extracted_data.copy()
    model_data['name'] = model_data.get('name') or old_listing.name
    print(f"extracted_data.get('name'): '{empty_extracted_data.get('name')}'")
    print(f"old_listing.name: {old_listing.name}")
    print(f"Final name: {model_data['name']}")
    print(f"❌ Problem: Falls back to 'Unknown Restaurant'")
    
    print("\n📊 SCENARIO 3: Extracted name is None (fallback to listing)")
    print("-" * 50)
    none_extracted_data = {'description': 'test'}  # No 'name' key
    model_data = none_extracted_data.copy()
    model_data['name'] = model_data.get('name') or old_listing.name
    print(f"extracted_data.get('name'): {none_extracted_data.get('name')}")
    print(f"old_listing.name: {old_listing.name}")
    print(f"Final name: {model_data['name']}")
    print(f"❌ Problem: Falls back to 'Unknown Restaurant'")
    
    print("\n📊 SCENARIO 4: With FIXED listing (after regex fix)")
    print("-" * 50)
    model_data = none_extracted_data.copy()
    model_data['name'] = model_data.get('name') or new_listing.name
    print(f"extracted_data.get('name'): {none_extracted_data.get('name')}")
    print(f"new_listing.name: {new_listing.name}")
    print(f"Final name: {model_data['name']}")
    print(f"✅ Should work: 'Primavega Restaurant - Ghost Kitchen'")
    
    print("\n🎯 CONCLUSION:")
    print("=" * 60)
    print("The issue is likely that:")
    print("1. ✅ Individual page extraction IS working (gets correct name)")
    print("2. ❌ BUT extraction is returning empty/None name for some reason")
    print("3. ❌ So it falls back to listing.name")
    print("4. ✅ City extraction regex is now fixed")
    print("5. ❓ Need to check WHY individual extraction returns empty name")

if __name__ == "__main__":
    debug_model_conversion() 