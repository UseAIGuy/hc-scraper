#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import HappyCowScraper
from datetime import datetime, timezone

# Create a mock restaurant listing
class MockListing:
    def __init__(self):
        self.name = "Unknown Restaurant"
        self.url = "/reviews/test-restaurant-123"
        self.city = "Austin"

# Test the conversion function
def test_array_conversion():
    scraper = HappyCowScraper("fake_url", "fake_key")
    
    # Simulate extracted data with string representations of arrays
    extracted_data = {
        'name': 'Alive & Well Natural Health Emporium',
        'cuisine_types': "['Health Store']",  # String representation of list
        'features': "[]",  # Empty list as string
        'recent_reviews': "[]",  # Empty list as string
        'cuisine_tags': "['Organic', 'Supplements']",  # Multiple items
        'vegan_status': 'vegan',
        'rating': 4.0,
        'review_count': 3
    }
    
    listing = MockListing()
    city_state_data = {'city_name': 'Austin', 'state': 'Texas', 'country': 'USA'}
    
    print("🧪 TESTING FIXED ARRAY CONVERSION")
    print("=" * 50)
    print(f"Input cuisine_types: {extracted_data['cuisine_types']} (type: {type(extracted_data['cuisine_types'])})")
    print(f"Input features: {extracted_data['features']} (type: {type(extracted_data['features'])})")
    print(f"Input cuisine_tags: {extracted_data['cuisine_tags']} (type: {type(extracted_data['cuisine_tags'])})")
    
    # Test the conversion
    try:
        result = scraper._convert_extracted_data_to_model(extracted_data, listing, city_state_data)
        
        if result:
            print("\n✅ CONVERSION SUCCESSFUL!")
            print(f"✅ cuisine_types: {result.cuisine_types} (type: {type(result.cuisine_types)})")
            print(f"✅ features: {result.features} (type: {type(result.features)})")
            print(f"✅ cuisine_tags: {result.cuisine_tags} (type: {type(result.cuisine_tags)})")
            print(f"✅ recent_reviews: {result.recent_reviews} (type: {type(result.recent_reviews)})")
            
            # Verify the arrays are proper lists
            assert isinstance(result.cuisine_types, list), "cuisine_types should be a list"
            assert isinstance(result.features, list), "features should be a list"
            assert isinstance(result.cuisine_tags, list), "cuisine_tags should be a list"
            assert isinstance(result.recent_reviews, list), "recent_reviews should be a list"
            
            # Verify content
            assert result.cuisine_types == ['Health Store'], f"Expected ['Health Store'], got {result.cuisine_types}"
            assert result.features == [], f"Expected [], got {result.features}"
            assert result.cuisine_tags == ['Organic', 'Supplements'], f"Expected ['Organic', 'Supplements'], got {result.cuisine_tags}"
            assert result.recent_reviews == [], f"Expected [], got {result.recent_reviews}"
            
            print("\n🎉 ALL TESTS PASSED! Array conversion is working correctly.")
            
        else:
            print("❌ CONVERSION FAILED - returned None")
            
    except Exception as e:
        print(f"❌ ERROR during conversion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_array_conversion() 