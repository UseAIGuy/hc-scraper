"""
CSS Selector Configuration for HappyCow Scraper

This module defines page-type-specific CSS selectors for different HappyCow page types.
Based on investigation, city listing pages and restaurant pages have different DOM structures
and require different selectors for successful crawling.
"""

from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass
from page_type_detector import PageType


@dataclass
class SelectorConfig:
    """Configuration for CSS selectors and wait conditions for a specific page type."""
    
    # Primary selectors to wait for (crawl4ai will wait for ANY of these)
    wait_for_selectors: List[str]
    
    # Selectors for extracting restaurant data
    restaurant_selectors: Dict[str, str]
    
    # Selectors for detecting page state/errors
    state_selectors: Dict[str, str]
    
    # Additional crawl4ai configuration
    wait_timeout: int = 30
    js_code: str = ""
    
    def get_wait_for_selector_string(self) -> str:
        """Get comma-separated string of selectors for crawl4ai wait_for parameter."""
        return ", ".join(self.wait_for_selectors)


class CSSConfigManager:
    """Manages CSS selector configurations for different HappyCow page types."""
    
    # City listing page configuration
    CITY_LISTING_CONFIG = SelectorConfig(
        wait_for_selectors=[
            ".card-listing",      # Main restaurant cards (81 matches found)
            ".venue-list-item",   # Alternative venue items (27 matches found)  
            ".no-results"         # No results message
        ],
        restaurant_selectors={
            "restaurant_cards": ".card-listing",
            "venue_items": ".venue-list-item", 
            "venue_links": ".venue-item-link",  # Links to restaurant pages (54 matches found)
            "restaurant_names": ".card-listing .venue-name, .venue-list-item .venue-name",
            "restaurant_links": ".card-listing a[href*='/reviews/'], .venue-list-item a[href*='/reviews/']",
            "addresses": ".card-listing .address, .venue-list-item .address",
            "ratings": ".card-listing .rating, .venue-list-item .rating",
            "categories": ".card-listing .category, .venue-list-item .category"
        },
        state_selectors={
            "no_results": ".no-results",
            "captcha": ".captcha",      # Keep for detection, not waiting
            "loading": ".loading, .spinner",
            "error": ".error-message"
        },
        wait_timeout=30,
        js_code=""
    )
    
    # Restaurant page selectors - UPDATED based on actual investigation
    RESTAURANT_PAGE = SelectorConfig(
        # Use selectors that actually exist on restaurant pages and don't timeout!
        wait_for_selectors=[
            ".venue",                # 30 matches - venue-related content  
            ".content",              # 12 matches - main content area
            ".venue-info",           # 2 matches - venue information (works reliably)
            ".title",                # 6 matches - various titles (works reliably)
            ".main"                  # 1 match - main container
        ],
        
        # Selectors for extracting restaurant data (more generic)
        restaurant_selectors={
            "name": "h1, .title, .venue-name",  # Keep h1 for extraction, just not waiting
            "description": ".description, .venue-info, .content",
            "address": ".address, .venue-info",
            "phone": ".phone, .contact",
            "website": "a[href*='http']",
            "hours": ".hours, .venue-hours",
            "rating": ".rating, .stars",
            "reviews": ".review, .review-item"
        },
        
        # State selectors for detecting page conditions
        state_selectors={
            "captcha": ".captcha",      # Keep for detection, not waiting
            "loading": ".loading, .spinner",
            "error": ".error-message"
        },
        
        wait_timeout=30,  # Reduced timeout since these are common elements
        js_code=""
    )
    
    # Unknown/fallback page configuration
    UNKNOWN_PAGE_CONFIG = SelectorConfig(
        wait_for_selectors=[
            "body",               # Basic fallback - wait for page body
            ".captcha"            # Always check for captcha
        ],
        restaurant_selectors={},
        state_selectors={
            "captcha": ".captcha",
            "loading": ".loading, .spinner", 
            "error": ".error-message"
        },
        wait_timeout=20,
        js_code=""
    )
    
    @classmethod
    def get_config_for_page_type(cls, page_type: PageType) -> SelectorConfig:
        """Get the appropriate selector configuration for a given page type."""
        config_map = {
            PageType.CITY_LISTING: cls.CITY_LISTING_CONFIG,
            PageType.RESTAURANT_PAGE: cls.RESTAURANT_PAGE,
            PageType.UNKNOWN: cls.UNKNOWN_PAGE_CONFIG
        }
        return config_map.get(page_type, cls.UNKNOWN_PAGE_CONFIG)
    
    @classmethod
    def get_crawl_config_for_page_type(cls, page_type: PageType) -> Dict[str, Any]:
        """Get crawl4ai configuration dictionary for a given page type."""
        config = cls.get_config_for_page_type(page_type)
        
        return {
            "wait_for": config.get_wait_for_selector_string(),
            "timeout": config.wait_timeout,
            "js_code": config.js_code if config.js_code else None
        }
    
    @classmethod
    def get_restaurant_selectors(cls, page_type: PageType) -> Dict[str, str]:
        """Get restaurant data extraction selectors for a given page type."""
        config = cls.get_config_for_page_type(page_type)
        return config.restaurant_selectors
    
    @classmethod
    def get_state_selectors(cls, page_type: PageType) -> Dict[str, str]:
        """Get page state detection selectors for a given page type."""
        config = cls.get_config_for_page_type(page_type)
        return config.state_selectors


def test_css_config():
    """Test the CSS configuration system."""
    print("🧪 Testing CSS Selector Configuration:")
    print("=" * 60)
    
    for page_type in PageType:
        print(f"\n📄 {page_type.value.upper()} Configuration:")
        print("-" * 40)
        
        config = CSSConfigManager.get_config_for_page_type(page_type)
        crawl_config = CSSConfigManager.get_crawl_config_for_page_type(page_type)
        
        print(f"Wait for selectors: {config.get_wait_for_selector_string()}")
        print(f"Timeout: {config.wait_timeout}s")
        print(f"Restaurant selectors: {len(config.restaurant_selectors)} defined")
        print(f"State selectors: {len(config.state_selectors)} defined")
        print(f"Crawl4ai config: {crawl_config}")


if __name__ == "__main__":
    test_css_config() 