"""
HappyCow Page Type Detection Utility

This module provides functionality to automatically detect whether a HappyCow URL
is a city listing page or an individual restaurant page, enabling appropriate
crawling strategies for each page type.
"""

import re
from enum import Enum
from typing import Optional
from urllib.parse import urlparse


class PageType(Enum):
    """Enumeration of supported HappyCow page types"""
    CITY_LISTING = "city_listing"
    RESTAURANT_PAGE = "restaurant_page"
    UNKNOWN = "unknown"


class PageTypeDetector:
    """
    Detects HappyCow page types based on URL patterns
    
    City listing pages follow pattern: /north_america/usa/state/city/
    Restaurant pages follow pattern: /reviews/restaurant-name-id/ or /reviews/restaurant-name-id/update
    """
    
    def __init__(self):
        # Compiled regex patterns for performance
        self.city_pattern = re.compile(
            r'^/(?:[^/]+/)*(?:north_america|south_america|europe|asia|africa|oceania)/'
            r'[^/]+/[^/]+/[^/]+/?$'
        )
        
        self.restaurant_pattern = re.compile(
            r'^/reviews/[^/]+-\d+/?(?:update/?)?$'
        )
        
        # Alternative restaurant pattern for pages without numeric ID
        self.restaurant_alt_pattern = re.compile(
            r'^/reviews/[^/]+/?(?:update/?)?$'
        )
    
    def detect_page_type(self, url: str) -> PageType:
        """
        Detect the page type from a HappyCow URL
        
        Args:
            url: Full URL or path to analyze
            
        Returns:
            PageType enum indicating the detected page type
            
        Examples:
            >>> detector = PageTypeDetector()
            >>> detector.detect_page_type("https://www.happycow.net/north_america/usa/texas/dallas/")
            PageType.CITY_LISTING
            >>> detector.detect_page_type("https://www.happycow.net/reviews/la-vegan-los-angeles-14477")
            PageType.RESTAURANT_PAGE
        """
        try:
            # Extract path from URL if full URL provided
            if url.startswith('http'):
                parsed = urlparse(url)
                path = parsed.path
            else:
                path = url
            
            # Normalize path
            path = path.strip()
            if not path.startswith('/'):
                path = '/' + path
            
            # Check for restaurant page patterns first (more specific)
            if self.restaurant_pattern.match(path) or self.restaurant_alt_pattern.match(path):
                return PageType.RESTAURANT_PAGE
            
            # Check for city listing pattern
            if self.city_pattern.match(path):
                return PageType.CITY_LISTING
            
            # Unknown pattern
            return PageType.UNKNOWN
            
        except Exception:
            # Handle malformed URLs gracefully
            return PageType.UNKNOWN
    
    def is_city_listing(self, url: str) -> bool:
        """Check if URL is a city listing page"""
        return self.detect_page_type(url) == PageType.CITY_LISTING
    
    def is_restaurant_page(self, url: str) -> bool:
        """Check if URL is a restaurant page"""
        return self.detect_page_type(url) == PageType.RESTAURANT_PAGE
    
    def get_page_type_info(self, url: str) -> dict:
        """
        Get detailed information about the detected page type
        
        Returns:
            Dictionary with page type and additional metadata
        """
        page_type = self.detect_page_type(url)
        
        return {
            'url': url,
            'page_type': page_type.value,
            'is_city_listing': page_type == PageType.CITY_LISTING,
            'is_restaurant_page': page_type == PageType.RESTAURANT_PAGE,
            'is_unknown': page_type == PageType.UNKNOWN,
            'confidence': 'high' if page_type != PageType.UNKNOWN else 'low'
        }


# Global instance for easy access
detector = PageTypeDetector()

# Convenience functions
def detect_page_type(url: str) -> PageType:
    """Convenience function to detect page type"""
    return detector.detect_page_type(url)

def is_city_listing(url: str) -> bool:
    """Convenience function to check if URL is city listing"""
    return detector.is_city_listing(url)

def is_restaurant_page(url: str) -> bool:
    """Convenience function to check if URL is restaurant page"""
    return detector.is_restaurant_page(url)


if __name__ == "__main__":
    # Test with known URLs
    test_urls = [
        # City listing pages
        "https://www.happycow.net/north_america/usa/texas/dallas/",
        "/north_america/usa/california/los_angeles/",
        "https://www.happycow.net/north_america/usa/new_york/new_york/",
        
        # Restaurant pages
        "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/update",
        "https://www.happycow.net/reviews/la-vegan-los-angeles-14477",
        "https://www.happycow.net/reviews/my-vegan-los-angeles-119792",
        "/reviews/crossroads-kitchen-los-angeles-12345/",
        
        # Edge cases
        "https://www.happycow.net/reviews/some-restaurant/update/",
        "https://www.happycow.net/europe/france/paris/",
        "",
        "invalid-url",
    ]
    
    print("🧪 Testing Page Type Detection:")
    print("=" * 60)
    
    for url in test_urls:
        info = detector.get_page_type_info(url)
        print(f"URL: {url}")
        print(f"Type: {info['page_type']} (confidence: {info['confidence']})")
        print(f"City: {info['is_city_listing']}, Restaurant: {info['is_restaurant_page']}")
        print("-" * 60) 