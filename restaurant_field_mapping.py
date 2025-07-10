#!/usr/bin/env python3
"""
HappyCow Restaurant Field Mapping

Based on HTML analysis of sample restaurant pages, this module defines
all extractable fields and their corresponding CSS selectors, regex patterns,
and structured data paths.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class ExtractionMethod(Enum):
    CSS_SELECTOR = "css"
    REGEX = "regex"
    STRUCTURED_DATA = "structured"
    META_TAG = "meta"
    ATTRIBUTE = "attribute"

@dataclass
class FieldMapping:
    """Defines how to extract a specific field from a restaurant page"""
    field_name: str
    css_selectors: List[str]
    regex_patterns: List[str]
    structured_data_paths: List[str]
    meta_tags: List[str]
    data_type: str
    required: bool = False
    default_value: Optional[Union[str, int, float, list]] = None
    validation_regex: Optional[str] = None
    cleanup_function: Optional[str] = None

# Core restaurant information fields
RESTAURANT_FIELD_MAPPINGS = {
    "name": FieldMapping(
        field_name="name",
        css_selectors=[
            "h1[itemprop='name']",  # ✅ Most specific - Schema.org marked restaurant name
            "h1.header-title",      # ✅ HappyCow's specific class for restaurant titles
            ".venue h1",            # ✅ h1 inside venue content area
            "main h1",              # ✅ h1 in main content area (avoid navigation)
            ".content h1",          # ✅ h1 in content area
            ".venue-title"          # ✅ Fallback venue title class
        ],
        regex_patterns=[
            r'<h1[^>]*class="header-title"[^>]*>([^<]+)</h1>',
            r"itemprop=['\"]name['\"][^>]*>([^<]+)<",
        ],
        structured_data_paths=[],  # ✅ FIXED: Remove microdata extraction that was returning URL
        meta_tags=["og:title"],
        data_type="str",
        required=True,
        cleanup_function="clean_restaurant_name"
    ),
    
    "rating": FieldMapping(
        field_name="rating",
        css_selectors=[
            "[itemprop='ratingValue']",
            ".venue-rating-container [itemprop='ratingValue']",
            ".rating-value"
        ],
        regex_patterns=[
            r'itemprop=["\']ratingValue["\']\s+content=["\']([0-9.]+)["\']',
            r'<meta\s+itemprop=["\']ratingValue["\']\s+content=["\']([0-9.]+)["\']'
        ],
        structured_data_paths=["aggregateRating.ratingValue"],
        meta_tags=[],
        data_type="float",
        validation_regex=r'^[0-5](\.[0-9])?$'
    ),
    
    "review_count": FieldMapping(
        field_name="review_count",
        css_selectors=[
            ".rating-reviews",
            "[itemprop='reviewCount']",
            ".venue-rating-container .rating-reviews"
        ],
        regex_patterns=[
            r'rating-reviews[^>]*>\s*\(\s*(\d+)\s*\)',
            r'itemprop=["\']reviewCount["\']\s+content=["\'](\d+)["\']'
        ],
        structured_data_paths=["aggregateRating.reviewCount"],
        meta_tags=[],
        data_type="int",
        validation_regex=r'^\d+$'
    ),
    
    "address": FieldMapping(
        field_name="address",
        css_selectors=[
            "[itemprop='address']",
            ".venue-address",
            "p[itemprop='address']",
            ".address"
        ],
        regex_patterns=[
            r'itemprop=["\']address["\'][^>]*>([^<]+)<',
            r'<p[^>]*itemprop=["\']address["\'][^>]*>([^<]+)</p>'
        ],
        structured_data_paths=["address"],
        meta_tags=[],
        data_type="str",
        cleanup_function="clean_address"
    ),
    
    "street_address": FieldMapping(
        field_name="street_address",
        css_selectors=[
            "[itemprop='streetAddress']",
            ".street-address"
        ],
        regex_patterns=[
            r'itemprop=["\']streetAddress["\'][^>]*>([^<]+)<'
        ],
        structured_data_paths=["address.streetAddress"],
        meta_tags=[],
        data_type="str"
    ),
    
    "phone": FieldMapping(
        field_name="phone",
        css_selectors=[
            "[itemprop='telephone']",
            "a[href^='tel:']",
            ".venue-phone",
            ".phone"
        ],
        regex_patterns=[
            r'itemprop=["\']telephone["\'][^>]*>([^<]+)<',
            r'href=["\']tel:([^"\']+)["\']',
            r'(?:Phone|Tel|Call):\s*([+\d\s\-\(\)]+)'
        ],
        structured_data_paths=["telephone"],
        meta_tags=[],
        data_type="str",
        validation_regex=r'^[\+\d\s\-\(\)]+$',
        cleanup_function="clean_phone"
    ),
    
    "website": FieldMapping(
        field_name="website",
        css_selectors=[
            "a[title='Visit their website'][href]",
            "a[data-analytics='default-website'][href]", 
            "a[title*='website'][href]:not([href*='happycow.net'])",
            "a[rel*='nofollow'][href^='http']:not([href*='happycow.net']):not([href*='facebook']):not([href*='instagram']):not([href*='twitter'])"
        ],
        regex_patterns=[
            r'title=["\']Visit their website["\'][^>]*href=["\']([^"\']+)["\']',
            r'Website</a>[^<]*<a[^>]*href=["\']([^"\']+)["\']'
        ],
        structured_data_paths=[],  # 🔧 FIXED: Removed ["url"] to prevent extracting HappyCow's own URL
        meta_tags=[],
        data_type="str",
        validation_regex=r'^https?://.+',
        cleanup_function="clean_url"
    ),
    
    "hours": FieldMapping(
        field_name="hours",
        css_selectors=[
            ".venue-hours-info-container",
            ".listing-hours",
            ".hours-summary",
            ".venue-hours"
        ],
        regex_patterns=[
            r'hours-summary["\'][^>]*>([^<]+)<',
            r'(?:Open|Hours):\s*([^<\n]+)'
        ],
        structured_data_paths=["openingHours"],
        meta_tags=[],
        data_type="str",
        cleanup_function="parse_hours"
    ),
    
    "description": FieldMapping(
        field_name="description",
        css_selectors=[
            "[itemprop='description']",
            ".venue-description",
            ".description"
        ],
        regex_patterns=[
            r'itemprop=["\']description["\'][^>]*content=["\']([^"\']+)["\']'
        ],
        structured_data_paths=["description"],
        meta_tags=["description", "og:description"],
        data_type="str",
        cleanup_function="clean_description"
    ),
    
    "cuisine_types": FieldMapping(
        field_name="cuisine_types",
        css_selectors=[
            # Actual cuisine type tags - specific gray badges (fixed CSS selector)
            "div.bg-gray-100.inline-flex.items-center.text-sm.font-bold.leading-none.rounded-md",
            # More specific with height class
            "div.bg-gray-100.inline-flex.h-6",
            # Fallback for similar badge patterns
            "div.bg-gray-100.inline-flex[class*='rounded-md']",
            # Legacy fallbacks (much more specific than before)
            ".venue-info .bg-gray-100",
            # Last resort - but only within venue info section
            ".venue-info-container .bg-gray-100"
        ],
        regex_patterns=[
            r'cuisine["\'][^>]*>([^<]+)<'
        ],
        structured_data_paths=["servesCuisine"],
        meta_tags=[],
        data_type="list",
        cleanup_function="parse_cuisine_list"
    ),
    
    "price_range": FieldMapping(
        field_name="price_range",
        css_selectors=[
            "[itemprop='priceRange']",
            ".price-range",
            ".price"
        ],
        regex_patterns=[
            r'itemprop=["\']priceRange["\'][^>]*content=["\']([^"\']+)["\']',
            r'Price:\s*([\$]+)'
        ],
        structured_data_paths=["priceRange"],
        meta_tags=[],
        data_type="str",
        validation_regex=r'^[\$]{1,4}$'
    ),
    
    "instagram": FieldMapping(
        field_name="instagram",
        css_selectors=[
            "a[href*='instagram.com']:not([href*='happycow'])",
            "#sitelink-profile-instagram",
            ".social-instagram a"
        ],
        regex_patterns=[
            r'href=["\']([^"\']*instagram\.com(?!/happycow)[^"\']*)["\']'
        ],
        structured_data_paths=[],
        meta_tags=[],
        data_type="str",
        cleanup_function="clean_social_url"
    ),
    
    "facebook": FieldMapping(
        field_name="facebook",
        css_selectors=[
            "a[href*='facebook.com']:not([href*='HappyCow'])",
            "#sitelink-profile-facebook",
            ".social-facebook a"
        ],
        regex_patterns=[
            r'href=["\']([^"\']*facebook\.com(?!/HappyCow)[^"\']*)["\']'
        ],
        structured_data_paths=[],
        meta_tags=[],
        data_type="str",
        cleanup_function="clean_social_url"
    ),
    
    "twitter": FieldMapping(
        field_name="twitter",
        css_selectors=[
            "a[href*='twitter.com']:not([href*='HappyCow'])",
            "a[href*='x.com']:not([href*='HappyCow'])",
            "#sitelink-profile-twitter-x",
            ".social-twitter a"
        ],
        regex_patterns=[
            r'href=["\']([^"\']*(?:twitter|x)\.com(?!/HappyCow)[^"\']*)["\']'
        ],
        structured_data_paths=[],
        meta_tags=[],
        data_type="str",
        cleanup_function="clean_social_url"
    ),
    
    "happycow_id": FieldMapping(
        field_name="happycow_id",
        css_selectors=[
            "[data-id]",
            ".header-title[data-id]"
        ],
        regex_patterns=[
            r'data-id=["\'](\d+)["\']',
            r'/reviews/[^/]+-(\d+)/?'
        ],
        structured_data_paths=[],
        meta_tags=[],
        data_type="str",
        validation_regex=r'^\d+$'
    ),
    
    "vegan_status": FieldMapping(
        field_name="vegan_status",
        css_selectors=[
            ".label.bg-vegan",           # Vegan badge
            ".label.bg-vegetarian",      # Vegetarian badge  
            ".label.bg-omnivore",        # Omnivore badge (if exists)
            ".vegan-status",             # Fallback
            ".restaurant-type"           # Fallback
        ],
        regex_patterns=[
            r'category-(\w+)',
            r'class=["\'][^"\']*category-([^"\'\\s]+)'
        ],
        structured_data_paths=[],
        meta_tags=[],
        data_type="str",
        cleanup_function="normalize_vegan_status"
    ),
    
    "features": FieldMapping(
        field_name="features",
        css_selectors=[
            ".features",
            ".amenities",
            ".venue-features"
        ],
        regex_patterns=[],
        structured_data_paths=[],
        meta_tags=[],
        data_type="list",
        cleanup_function="parse_features_list"
    ),
    
    "recent_reviews": FieldMapping(
        field_name="recent_reviews",
        css_selectors=[
            "[itemprop='review']",
            ".review-content",
            ".comment-body"
        ],
        regex_patterns=[],
        structured_data_paths=["review"],
        meta_tags=[],
        data_type="list",
        cleanup_function="extract_review_excerpts"
    )
}

# Cleanup and validation functions
def clean_restaurant_name(name: str) -> str:
    """Clean restaurant name by removing 'CLOSED:' prefix and extra whitespace"""
    if not name:
        return ""
    name = name.strip()
    if name.startswith("CLOSED:"):
        name = name[7:].strip()
    return name

def clean_address(address: str) -> str:
    """Clean address by removing extra whitespace and formatting"""
    if not address:
        return ""
    # Remove extra whitespace and normalize
    address = " ".join(address.split())
    return address

def clean_phone(phone: str) -> str:
    """Clean phone number by removing extra characters"""
    if not phone:
        return ""
    # Remove common prefixes and clean
    phone = phone.replace("tel:", "").strip()
    return phone

def clean_url(url: str) -> str:
    """Clean URL by ensuring proper format"""
    if not url:
        return ""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url

def clean_social_url(url: str) -> str:
    """Clean social media URL"""
    if not url:
        return ""
    url = url.strip()
    # Remove tracking parameters
    if "?" in url:
        url = url.split("?")[0]
    return url

def parse_hours(hours_text: str) -> str:
    """Parse and normalize hours text"""
    if not hours_text:
        return ""
    # Basic cleanup - more sophisticated parsing can be added
    return hours_text.strip()

def clean_description(description: str) -> str:
    """Clean description text"""
    if not description:
        return ""
    # Remove HTML entities and normalize whitespace
    description = description.replace("&#39;", "'").replace("&quot;", '"')
    return " ".join(description.split())

def parse_cuisine_list(cuisine_text: str) -> List[str]:
    """Parse cuisine types from text"""
    if not cuisine_text:
        return []
    # Split by common delimiters
    cuisines = []
    for delimiter in [",", ";", "|", "/"]:
        if delimiter in cuisine_text:
            cuisines = [c.strip() for c in cuisine_text.split(delimiter)]
            break
    else:
        cuisines = [cuisine_text.strip()]
    
    return [c for c in cuisines if c]

def normalize_vegan_status(status: str) -> str:
    """Normalize vegan status to standard values"""
    if not status:
        return ""
    
    status = status.lower().strip()
    if "vegan" in status:
        return "vegan"
    elif "vegetarian" in status:
        return "vegetarian"
    elif "options" in status or "friendly" in status:
        return "veg-options"
    return status

def parse_features_list(features_text: str) -> List[str]:
    """Parse features/amenities list"""
    if not features_text:
        return []
    # Implementation depends on how features are presented in HTML
    return [f.strip() for f in features_text.split(",") if f.strip()]

def extract_review_excerpts(reviews_html: str) -> List[Dict[str, str]]:
    """Extract review excerpts from review HTML"""
    # This would need BeautifulSoup parsing - placeholder for now
    return []

# CSS selector priority order (most specific to least specific)
CSS_SELECTOR_PRIORITY = [
    "structured_data_paths",  # Schema.org microdata
    "css_selectors",          # CSS selectors
    "meta_tags",              # Meta tag content
    "regex_patterns"          # Regex fallback
]

# Database field mapping to ensure compatibility
DATABASE_FIELD_MAPPING = {
    "name": "name",
    "rating": "rating",
    "review_count": "review_count",
    "address": "address",
    "phone": "phone",
    "website": "website",
    "instagram": "instagram",
    "facebook": "facebook",
    "hours": "hours",
    "description": "description",
    "cuisine_types": "cuisine_types",
    "cuisine_tags": "cuisine_tags",  # Alternative field
    "price_range": "price_range",
    "vegan_status": "vegan_status",
    "features": "features",
    "recent_reviews": "recent_reviews",
    "happycow_id": "happycow_id",
    "street_address": "address",  # Can be combined with main address
} 