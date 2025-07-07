"""
Configuration management for HappyCow scraper
"""
import os
from typing import Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ScrapingConfig:
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Scraping behavior
    test_mode: bool = False
    max_restaurants_per_city: Optional[int] = None
    max_concurrency: int = 3
    human_delay_range: tuple = (2, 5)
    
    # Queue-based scraping
    queue_mode: bool = False  # Use city_queue table instead of manual cities
    max_cities_per_run: int = 1  # How many cities to process in one run
    resume_city: bool = True  # Resume within a city if partially scraped
    min_entries_threshold: int = 50  # Skip cities with fewer than this many restaurants
    max_entries_threshold: int = 1500  # Skip cities with more than this (too big for single run)
    
    # City selection
    target_states: Optional[List[str]] = None  # Filter to specific states
    skip_running_cities: bool = True  # Skip cities with trigger_status='running'
    
    # Resume behavior
    resume_from_page: int = 1  # Which page to start from within a city
    max_pages_per_city: Optional[int] = None  # Limit pages per city (for testing)
    
    # Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"
    
    # Rate limiting
    request_delay: float = 1.0
    error_delay: float = 5.0
    max_retries: int = 3

def load_config() -> ScrapingConfig:
    return ScrapingConfig(
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_key=os.getenv("SUPABASE_KEY", ""),
        ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama2"),
    )

# Global config instance
config = load_config() 