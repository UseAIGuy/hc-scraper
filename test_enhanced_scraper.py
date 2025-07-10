#!/usr/bin/env python3
"""
Test script for enhanced scraper integration

This script tests the enhanced extraction engine with the main scraper
to ensure the integration works correctly.
"""

import asyncio
import os
from enhanced_extraction_engine import EnhancedExtractionEngine
from scraper import RestaurantListing

async def test_enhanced_extraction():
    """Test the enhanced extraction engine with sample HTML files"""
    
    # Test with our sample HTML files
    sample_files = [
        "html_analysis/sample_2.html",
        "html_analysis/sample_3.html", 
        "html_analysis/sample_5.html"
    ]
    
    extraction_engine = EnhancedExtractionEngine()
    
    for sample_file in sample_files:
        if os.path.exists(sample_file):
            print(f"\n=== Testing {sample_file} ===")
            
            # Read the HTML file
            with open(sample_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Test extraction
            try:
                extracted_data = await extraction_engine.extract_restaurant_data(
                    "test_url", html_content
                )
                
                if extracted_data:
                    print(f"✅ Successfully extracted data:")
                    for key, value in extracted_data.items():
                        if value:  # Only show non-empty values
                            print(f"  {key}: {value}")
                else:
                    print(f"❌ No data extracted")
                    
            except Exception as e:
                print(f"❌ Error during extraction: {e}")
        else:
            print(f"⚠️  Sample file not found: {sample_file}")

def test_listing_conversion():
    """Test converting extracted data to RestaurantListing model"""
    print("\n=== Testing RestaurantListing Creation ===")
    
    # Test creating a RestaurantListing
    try:
        listing = RestaurantListing(
            name="Test Restaurant",
            url="/reviews/12345-test-restaurant",
            city="Austin",
            listing_type="vegan",
            is_featured=False,
            is_new=False
        )
        print(f"✅ RestaurantListing created successfully: {listing.name}")
        print(f"  URL: {listing.url}")
        print(f"  City: {listing.city}")
        print(f"  Type: {listing.listing_type}")
        return listing
    except Exception as e:
        print(f"❌ Error creating RestaurantListing: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Testing Enhanced Scraper Integration")
    
    # Test basic model creation
    test_listing = test_listing_conversion()
    
    # Test enhanced extraction
    asyncio.run(test_enhanced_extraction())
    
    print("\n🎉 Integration test completed!")
 