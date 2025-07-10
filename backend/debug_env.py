import os
from pathlib import Path
from dotenv import load_dotenv

print("=== Environment Debug ===")

# Show current working directory
print(f"Current working directory: {os.getcwd()}")

# Show file locations
current_dir = Path(__file__).parent
root_dir = current_dir.parent
print(f"Backend directory: {current_dir}")
print(f"Root directory: {root_dir}")

# Check for .env files
env_paths = [
    root_dir / ".env",
    current_dir / ".env",
    Path(".env"),  # Current working directory
    Path("../.env"),  # Parent directory
]

print("\n=== Checking .env file locations ===")
for env_path in env_paths:
    exists = env_path.exists()
    print(f"{env_path}: {'EXISTS' if exists else 'NOT FOUND'}")
    if exists:
        print(f"  Absolute path: {env_path.absolute()}")

# Try loading from each location
print("\n=== Testing environment loading ===")
for env_path in env_paths:
    if env_path.exists():
        print(f"\nTrying to load from: {env_path}")
        load_dotenv(dotenv_path=str(env_path), override=True)
        
        url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_KEY")
        anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        print(f"  SUPABASE_URL: {'Found' if url else 'NOT FOUND'}")
        print(f"  SUPABASE_SERVICE_KEY: {'Found' if service_key else 'NOT FOUND'}")
        print(f"  SUPABASE_ANON_KEY: {'Found' if anon_key else 'NOT FOUND'}")
        
        if url:
            print(f"  URL starts with: {url[:20]}...")
        if service_key:
            print(f"  Service key starts with: {service_key[:20]}...")
        break

print("\n=== Final environment check ===")
print(f"SUPABASE_URL: {'Set' if os.getenv('SUPABASE_URL') else 'NOT SET'}")
print(f"SUPABASE_SERVICE_KEY: {'Set' if os.getenv('SUPABASE_SERVICE_KEY') else 'NOT SET'}") 