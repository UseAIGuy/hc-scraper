#!/usr/bin/env python3
"""
Debug script to analyze Austin scraping timeout issue
"""

import asyncio
from supabase import create_client
from config import load_config

async def debug_austin_issue():
    """Analyze what's happening with Austin city scraping"""
    config = load_config()
    supabase = create_client(config.supabase_url, config.supabase_key)
    
    print("🔍 DEBUGGING AUSTIN SCRAPING ISSUE")
    print("=" * 50)
    
    # 1. Check if austin_texas exists in city_queue by full_path
    print("\n1. Checking database for 'austin_texas' by full_path:")
    result = supabase.table('city_queue').select('*').eq('full_path', 'austin_texas').execute()
    if result.data:
        austin_data = result.data[0]
        print(f"   ✅ Found: {austin_data}")
        print(f"   📍 City: {austin_data['city']}, {austin_data['state']}")
        print(f"   🔗 URL: {austin_data['url']}")
        print(f"   📊 Entries: {austin_data.get('entries', 'N/A')}")
        print(f"   📄 Status: {austin_data.get('trigger_status', 'N/A')}")
    else:
        print("   ❌ NOT FOUND by full_path")
    
    # 2. Check if Austin exists by city name
    print("\n2. Checking database for 'Austin' by city name:")
    result = supabase.table('city_queue').select('*').eq('city', 'Austin').execute()
    if result.data:
        for i, city in enumerate(result.data):
            print(f"   [{i+1}] {city['city']}, {city['state']} - {city['url']}")
    else:
        print("   ❌ NO Austin cities found")
    
    # 3. Show what URL the scraper is constructing
    print("\n3. URL Construction Analysis:")
    print("   🎯 Target URL: https://www.happycow.net/north_america/usa/texas/austin/")
    
    # 4. Check Dallas for comparison
    print("\n4. Dallas Comparison (working city):")
    result = supabase.table('city_queue').select('*').eq('full_path', 'dallas_texas').execute()
    if result.data:
        dallas_data = result.data[0]
        print(f"   ✅ Dallas URL: {dallas_data['url']}")
        print(f"   📊 Dallas Entries: {dallas_data.get('entries', 'N/A')}")
        print(f"   📄 Dallas Status: {dallas_data.get('trigger_status', 'N/A')}")
    
    # 5. Check for any Texas cities
    print("\n5. All Texas cities in database:")
    result = supabase.table('city_queue').select('city, state, url, full_path, entries').eq('state', 'Texas').execute()
    if result.data:
        for city in result.data:
            print(f"   📍 {city['city']}: {city['url']} ({city.get('entries', 0)} entries)")
    else:
        print("   ❌ No Texas cities found")
    
    print("\n" + "=" * 50)
    print("🔍 ANALYSIS COMPLETE")

if __name__ == "__main__":
    asyncio.run(debug_austin_issue()) 