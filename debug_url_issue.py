import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def debug_url_issue():
    """Debug what's actually stored in the database for dallas_texas"""
    print("🔍 Debugging URL construction issue...")
    
    # Get Supabase config from environment
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    try:
        # Get the raw data
        result = supabase.table('city_queue').select('*').eq('full_path', 'dallas_texas').execute()
        
        if not result.data:
            print("❌ No city found for dallas_texas")
            return
        
        city_data = result.data[0]
        
        print("📊 Raw database data:")
        for key, value in city_data.items():
            print(f"  {key}: '{value}'")
        
        print(f"\n🔗 URL field specifically:")
        url_field = city_data.get('url', 'NOT_FOUND')
        print(f"  Raw value: '{url_field}'")
        print(f"  Type: {type(url_field)}")
        print(f"  Length: {len(str(url_field))}")
        
        print(f"\n🏗️ URL construction:")
        base_url = "https://www.happycow.net"
        constructed_url = f"{base_url}{url_field}"
        print(f"  Base: '{base_url}'")
        print(f"  URL field: '{url_field}'")
        print(f"  Constructed: '{constructed_url}'")
        
        # Check if URL field already contains full URL
        if url_field.startswith('http'):
            print(f"  ⚠️ URL field already contains full URL!")
            print(f"  Should use: '{url_field}' directly")
        else:
            print(f"  ✅ URL field is relative path as expected")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_url_issue() 