#!/usr/bin/env python3
"""
Test Enhanced Scraper with Review Extraction

This script tests the complete workflow:
1. Restaurant data extraction
2. Review extraction and pagination
3. Database saving for both restaurants and reviews
"""

import asyncio
import os
import json
from dotenv import load_dotenv
from scraper import HappyCowScraper

# Load environment variables
load_dotenv()

async def test_enhanced_scraper_with_reviews():
    """Test the enhanced scraper with review extraction"""
    
    print("🧪 Testing Enhanced Scraper with Review Extraction")
    print("=" * 60)
    
    # Test with a small city that likely has few restaurants
    test_city = "Bend, Oregon"  # Small city, likely 5-10 restaurants
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials in .env file")
        print("Please ensure SUPABASE_URL and SUPABASE_KEY are set")
        return
    
    # Initialize scraper
    scraper = HappyCowScraper(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        max_restaurants=3,  # Limit to 3 restaurants for testing
        min_delay=1.0,      # Faster for testing
        max_delay=2.0
    )
    
    try:
        async with scraper:
            print(f"🏙️  Testing with city: {test_city}")
            print(f"📊 Limiting to 3 restaurants for testing")
            print()
            
            # Run complete scraping for the test city
            result = await scraper.scrape_city_complete(test_city, max_restaurants=3)
            
            print("\\n🎉 Test Results:")
            print("=" * 40)
            print(f"City: {result['city']}")
            print(f"Success: {result['success']}")
            print(f"Listings Found: {result['listings_found']}")
            print(f"Restaurants Scraped: {result['restaurants_scraped']}")
            print(f"Restaurants Saved: {result['restaurants_saved']}")
            print(f"Restaurants Skipped: {result['restaurants_skipped']}")
            
            if result['success'] and result['restaurants_saved'] > 0:
                print("\\n✅ Test PASSED!")
                print("📝 Enhanced scraper successfully extracted restaurant data and reviews")
                
                # Check if reviews were saved
                try:
                    review_check = scraper.supabase.table('reviews').select('*').limit(5).execute()
                    if review_check.data:
                        print(f"📚 Found {len(review_check.data)} reviews in database")
                        print("\\nSample review:")
                        sample_review = review_check.data[0]
                        print(f"  Author: {sample_review.get('author_username', 'Unknown')}")
                        print(f"  Rating: {sample_review.get('rating', 'N/A')}/5")
                        print(f"  Title: {sample_review.get('title', 'No title')}")
                        print(f"  Content: {sample_review.get('content', 'No content')[:100]}...")
                    else:
                        print("📝 No reviews found in database")
                except Exception as e:
                    print(f"⚠️  Error checking reviews: {e}")
                
            else:
                print("\\n⚠️  Test completed but no restaurants were saved")
                print("This might be due to existing data or extraction issues")
            
    except Exception as e:
        print(f"\\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()

async def test_review_extraction_only():
    """Test only the review extraction with sample HTML files"""
    
    print("\\n🔍 Testing Review Extraction with Sample Files")
    print("=" * 50)
    
    from review_extraction_engine import ReviewExtractionEngine
    
    sample_files = [
        "html_analysis/sample_2.html",
        "html_analysis/sample_3.html", 
        "html_analysis/sample_5.html"
    ]
    
    review_engine = ReviewExtractionEngine()
    
    for sample_file in sample_files:
        if os.path.exists(sample_file):
            print(f"\\n📄 Testing {sample_file}")
            
            with open(sample_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            reviews = await review_engine.extract_reviews_from_html(html_content, "https://test.com")
            
            if reviews:
                print(f"  ✅ Extracted {len(reviews)} reviews")
                print(f"  📊 Average rating: {sum(r.rating for r in reviews) / len(reviews):.1f}/5")
                print(f"  👥 Authors: {', '.join(r.author.username for r in reviews[:3])}...")
            else:
                print(f"  ❌ No reviews extracted")
        else:
            print(f"  ⚠️  File not found: {sample_file}")

if __name__ == "__main__":
    print("🚀 Starting Enhanced Scraper Tests")
    print()
    
    # Test review extraction first
    asyncio.run(test_review_extraction_only())
    
    print("\\n" + "="*60)
    
    # Test full scraper with reviews
    asyncio.run(test_enhanced_scraper_with_reviews()) 