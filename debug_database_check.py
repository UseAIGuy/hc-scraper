#!/usr/bin/env python3
"""
Debug script to check what's in the restaurants database
"""

import asyncio
from supabase import create_client
from config import load_config

async def check_database():
    """Check what's actually in the restaurants database"""
    config = load_config()
    supabase = create_client(config.supabase_url, config.supabase_key)
    
    print("🔍 CHECKING RESTAURANTS DATABASE")
    print("=" * 50)
    
    # Check total restaurants in database
    result = supabase.table('restaurants').select('id, name, happycow_url').execute()
    print(f'📊 Total restaurants in database: {len(result.data)}')
    
    if len(result.data) == 0:
        print("✅ Database is completely empty - restaurants should be scraped")
        return
    
    # Check for specific Dallas restaurants
    dallas_restaurants = supabase.table('restaurants').select('id, name, happycow_url').ilike('happycow_url', '%dallas%').execute()
    print(f'🏙️  Dallas restaurants in database: {len(dallas_restaurants.data)}')
    
    if dallas_restaurants.data:
        print('\n📋 Dallas restaurants found:')
        for r in dallas_restaurants.data:
            print(f'  - {r["name"]}: {r["happycow_url"]}')
    
    # Check for specific Austin restaurants
    austin_restaurants = supabase.table('restaurants').select('id, name, happycow_url').ilike('happycow_url', '%austin%').execute()
    print(f'\n🏙️  Austin restaurants in database: {len(austin_restaurants.data)}')
    
    if austin_restaurants.data:
        print('\n📋 Austin restaurants found:')
        for r in austin_restaurants.data[:5]:  # Show first 5
            print(f'  - {r["name"]}: {r["happycow_url"]}')
        if len(austin_restaurants.data) > 5:
            print(f'  ... and {len(austin_restaurants.data) - 5} more')
    
    # Test the exact check that scraper is doing
    print(f'\n🧪 TESTING SCRAPER CHECK LOGIC')
    print("-" * 30)
    
    # Test a specific Dallas restaurant URL
    test_url = "https://www.happycow.net/reviews/community-beer-co-dallas-251394"
    result = supabase.table('restaurants').select('id').eq('happycow_url', test_url).execute()
    exists = len(result.data) > 0
    print(f'Test URL: {test_url}')
    print(f'Exists in DB: {exists}')
    print(f'Result: {result.data}')

if __name__ == "__main__":
    asyncio.run(check_database()) 