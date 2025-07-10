import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Try to load environment variables from multiple locations
current_dir = Path(__file__).parent
root_dir = current_dir.parent

# Try loading from root directory first, then current directory
env_paths = [
    root_dir / ".env",  # Root directory
    current_dir / ".env",  # Backend directory
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=str(env_path))
        print(f"Loaded environment from: {env_path}")
        break
else:
    print("No .env file found, using system environment variables")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_KEY")  # Use the actual variable name from .env

# Debug: Print what we found (remove in production)
print(f"SUPABASE_URL found: {'Yes' if SUPABASE_URL else 'No'}")
print(f"SUPABASE_KEY found: {'Yes' if SUPABASE_SERVICE_KEY else 'No'}")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase configuration. Please set SUPABASE_URL and SUPABASE_KEY in .env file")

# Create Supabase client with service role key (full access)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def get_supabase_client() -> Client:
    """Get the Supabase client instance"""
    return supabase 