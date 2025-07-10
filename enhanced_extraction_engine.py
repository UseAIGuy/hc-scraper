#!/usr/bin/env python3
"""
Enhanced Restaurant Data Extraction Engine

Uses the field mapping to extract comprehensive data from HappyCow restaurant pages
with multiple extraction strategies and fallback methods.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Union
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
from restaurant_field_mapping import (
    RESTAURANT_FIELD_MAPPINGS, 
    FieldMapping,
    CSS_SELECTOR_PRIORITY,
    DATABASE_FIELD_MAPPING,
    clean_restaurant_name,
    clean_address,
    clean_phone,
    clean_url,
    clean_social_url,
    parse_hours,
    clean_description,
    parse_cuisine_list,
    normalize_vegan_status,
    parse_features_list,
    extract_review_excerpts
)

# Mapping of cleanup function names to actual functions
CLEANUP_FUNCTIONS = {
    "clean_restaurant_name": clean_restaurant_name,
    "clean_address": clean_address,
    "clean_phone": clean_phone,
    "clean_url": clean_url,
    "clean_social_url": clean_social_url,
    "parse_hours": parse_hours,
    "clean_description": clean_description,
    "parse_cuisine_list": parse_cuisine_list,
    "normalize_vegan_status": normalize_vegan_status,
    "parse_features_list": parse_features_list,
    "extract_review_excerpts": extract_review_excerpts
}

class EnhancedExtractionEngine:
    """Enhanced extraction engine for comprehensive restaurant data extraction"""
    
    def __init__(self, session: aiohttp.ClientSession = None):
        self.session = session
        self.logger = logging.getLogger(__name__)
        
    async def extract_restaurant_data(self, url: str, html_content: str = None) -> Dict[str, Any]:
        """
        Extract comprehensive restaurant data from a HappyCow restaurant page
        
        Args:
            url: Restaurant page URL
            html_content: Optional pre-fetched HTML content
            
        Returns:
            Dictionary containing extracted restaurant data
        """
        if html_content is None:
            html_content = await self._fetch_page(url)
        
        if not html_content:
            self.logger.error(f"Failed to fetch content for {url}")
            return {}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        extracted_data = {}
        
        # 🔧 FIX: Extract name first with dedicated method to prevent overwriting
        restaurant_name = await self._extract_restaurant_name(soup, url)
        if restaurant_name:
            extracted_data['name'] = restaurant_name
            self.logger.info(f"✅ Restaurant name successfully extracted: '{restaurant_name}'")
        
        # 🔧 FIX: Add cache to prevent re-extraction of successful fields
        extraction_cache = {}
        
        # If name was successfully extracted, cache it to skip in main loop
        if 'name' in extracted_data:
            extraction_cache['name'] = extracted_data['name']
        
        # Extract data for each mapped field
        for field_name, field_mapping in RESTAURANT_FIELD_MAPPINGS.items():
            try:
                # Check cache first
                if field_name in extraction_cache:
                    self.logger.debug(f"Using cached value for {field_name}")
                    extracted_data[field_name] = extraction_cache[field_name]
                    continue
                    
                value = await self._extract_field(field_name, field_mapping, soup)
                if value is not None:
                    extracted_data[field_name] = value
                    # Cache successful extractions
                    extraction_cache[field_name] = value
            except Exception as e:
                self.logger.warning(f"Failed to extract {field_name} from {url}: {e}")
                
        # Add URL and derived fields
        extracted_data['happycow_url'] = url
        extracted_data['venue_id'] = self._extract_venue_id(url)
        
        # Post-process and validate data
        extracted_data = self._post_process_data(extracted_data)
        
        return extracted_data
    
    async def _extract_field(self, field_name: str, field_mapping: FieldMapping, soup: BeautifulSoup) -> Any:
        """Extract a single field using its mapping configuration"""
        try:
            # Special handling for cuisine_types using custom extraction
            if field_name == 'cuisine_types':
                return await self._extract_cuisine_types(soup)
            
            # Try CSS selectors first
            if field_mapping.css_selectors:
                for selector in field_mapping.css_selectors:
                    try:
                        result = self._extract_css_selector(soup, selector, field_name)
                        if result:
                            processed_result = self._process_field_value(result, field_mapping)
                            if processed_result:
                                self.logger.info(f"{field_name.title()} field extracted successfully: '{processed_result}'")
                                return processed_result
                    except Exception as e:
                        self.logger.debug(f"CSS selector '{selector}' failed for {field_name}: {e}")
                        continue

            # Try regex patterns if CSS selectors didn't work
            if field_mapping.regex_patterns:
                html_text = str(soup)
                for pattern in field_mapping.regex_patterns:
                    try:
                        matches = re.findall(pattern, html_text, re.IGNORECASE | re.DOTALL)
                        if matches:
                            # Take the first match, or join multiple matches
                            result = matches[0] if len(matches) == 1 else ' '.join(matches)
                            processed_result = self._process_field_value(result, field_mapping)
                            if processed_result:
                                self.logger.info(f"{field_name.title()} field extracted via regex: '{processed_result}'")
                                return processed_result
                    except Exception as e:
                        self.logger.debug(f"Regex pattern '{pattern}' failed for {field_name}: {e}")
                        continue

            # Field not found
            self.logger.warning(f"{field_name.title()} field is empty or missing, using default")
            return field_mapping.default_value

        except Exception as e:
            self.logger.error(f"Error extracting {field_name}: {e}")
            return field_mapping.default_value
    
    def _extract_structured_data(self, soup: BeautifulSoup, paths: List[str]) -> Optional[str]:
        """Extract data from Schema.org microdata"""
        for path in paths:
            # Handle nested paths like "aggregateRating.ratingValue"
            if "." in path:
                parts = path.split(".")
                elements = soup.find_all(attrs={"itemprop": parts[0]})
                for element in elements:
                    nested = element.find(attrs={"itemprop": parts[1]})
                    if nested:
                        return nested.get("content") or nested.get_text(strip=True)
            else:
                element = soup.find(attrs={"itemprop": path})
                if element:
                    return element.get("content") or element.get_text(strip=True)
        return None
    
    def _extract_css_selector(self, soup: BeautifulSoup, selector: str, field_name: str) -> Optional[str]:
        """Extract data using CSS selectors"""
        try:
            elements = soup.select(selector)
            for element in elements:
                if element:
                    # Handle different types of content
                    if element.name == "meta":
                        return element.get("content")
                    elif selector.endswith("[href]") or "href=" in selector:
                        # Only extract href if the selector specifically asks for it (e.g., a[href])
                        return element.get("href")
                    else:
                        # Always extract text content for all other cases
                        text = element.get_text(strip=True)
                        if text:
                            return text
        except Exception as e:
            self.logger.debug(f"CSS selector failed: {selector} - {e}")
            return None
    
    def _extract_meta_tags(self, soup: BeautifulSoup, meta_names: List[str]) -> Optional[str]:
        """Extract data from meta tags"""
        for meta_name in meta_names:
            # Try property attribute (og: tags)
            meta = soup.find("meta", property=meta_name)
            if meta:
                return meta.get("content")
            
            # Try name attribute
            meta = soup.find("meta", attrs={"name": meta_name})
            if meta:
                return meta.get("content")
        return None
    
    def _extract_regex(self, html_content: str, patterns: List[str]) -> Optional[str]:
        """Extract data using regex patterns"""
        for pattern in patterns:
            try:
                match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
            except Exception as e:
                self.logger.debug(f"Regex pattern failed: {pattern} - {e}")
                continue
        return None
    
    def _process_field_value(self, value: Any, field_mapping) -> Any:
        """Process and validate field value"""
        if value is None:
            return field_mapping.default_value
        
        # Convert to string for processing
        if not isinstance(value, str):
            value = str(value)
        
        # Apply cleanup function if specified
        if field_mapping.cleanup_function and field_mapping.cleanup_function in CLEANUP_FUNCTIONS:
            cleanup_func = CLEANUP_FUNCTIONS[field_mapping.cleanup_function]
            try:
                value = cleanup_func(value)
            except Exception as e:
                self.logger.warning(f"Cleanup function failed for {field_mapping.field_name}: {e}")
        
        # Validate with regex if specified
        if field_mapping.validation_regex and isinstance(value, str):
            if not re.match(field_mapping.validation_regex, value):
                self.logger.warning(f"Validation failed for {field_mapping.field_name}: {value}")
                return field_mapping.default_value
        
        # Convert to appropriate data type
        try:
            if field_mapping.data_type == "int":
                # Extract numbers from text like "(123)"
                if isinstance(value, str):
                    numbers = re.findall(r'\d+', value)
                    if numbers:
                        return int(numbers[0])
                return int(value) if value else 0
            elif field_mapping.data_type == "float":
                return float(value) if value else 0.0
            elif field_mapping.data_type == "list":
                if isinstance(value, list):
                    return value
                elif isinstance(value, str):
                    # Apply list parsing if cleanup function returns a list
                    if field_mapping.cleanup_function in CLEANUP_FUNCTIONS:
                        cleanup_func = CLEANUP_FUNCTIONS[field_mapping.cleanup_function]
                        if cleanup_func.__name__.startswith("parse_") and "_list" in cleanup_func.__name__:
                            return cleanup_func(value)
                    return [value] if value else []
                return []
            else:  # string
                return str(value) if value else ""
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Type conversion failed for {field_mapping.field_name}: {e}")
            return field_mapping.default_value
    
    def _extract_venue_id(self, url: str) -> Optional[str]:
        """Extract venue ID from URL"""
        # Pattern: /reviews/restaurant-name-city-ID
        match = re.search(r'/reviews/[^/]+-(\d+)/?', url)
        if match:
            return match.group(1)
        return None
    
    def _post_process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process extracted data for consistency and completeness"""
        processed = {}
        
        # Map to database field names
        for extracted_field, value in data.items():
            db_field = DATABASE_FIELD_MAPPING.get(extracted_field, extracted_field)
            processed[db_field] = value
        
        # 🔧 FIX: Only set default name if truly missing or empty
        name_value = processed.get("name")
        if not name_value or (isinstance(name_value, str) and name_value.strip() == ""):
            self.logger.warning("Name field is empty or missing, using default")
            processed["name"] = "Unknown Restaurant"
        else:
            self.logger.info(f"Name field extracted successfully: '{name_value}'")
        
        # Normalize vegan status
        if processed.get("vegan_status"):
            processed["vegan_status"] = normalize_vegan_status(processed["vegan_status"])
        
        # Ensure arrays are properly formatted
        for field in ["cuisine_types", "cuisine_tags", "features"]:
            if field in processed and not isinstance(processed[field], list):
                if processed[field]:
                    processed[field] = [processed[field]]
                else:
                    processed[field] = []
        
        # Set default values for missing fields
        defaults = {
            "rating": 0.0,
            "review_count": 0,
            "cuisine_types": [],
            "cuisine_tags": [],
            "features": [],
            "recent_reviews": []
        }
        
        for field, default_value in defaults.items():
            if field not in processed:
                processed[field] = default_value
        
        return processed
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content if session is available"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
        
        return None
    
    async def _extract_cuisine_types(self, soup):
        """Extract cuisine types using direct HTML parsing between venue-info containers"""
        try:
            # Find the venue-info container
            venue_info = soup.find('div', class_='venue-info relative')
            if not venue_info:
                self.logger.warning("venue-info container not found")
                return []
            
            # Find the venue-info-container (end boundary)
            venue_info_container = soup.find('div', class_=lambda x: x and 'venue-info-container' in x and 'relative' in x and 'overflow-hidden' in x)
            
            cuisine_types = []
            
            # Loop through all divs in venue-info until we hit venue-info-container
            current = venue_info
            while current:
                # Look for the specific cuisine type divs
                divs = current.find_all('div', class_=lambda x: x and 'mt-1' in x and 'bg-gray-100' in x and 'inline-flex' in x)
                
                for div in divs:
                    text = div.get_text(strip=True)
                    if text and len(text) < 50:  # Reasonable length for cuisine types
                        cuisine_types.append(text)
                
                # Move to next sibling, stop if we hit venue-info-container
                current = current.find_next_sibling()
                if current and current.get('class'):
                    classes = ' '.join(current.get('class', []))
                    if 'venue-info-container' in classes:
                        break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_cuisine_types = []
            for item in cuisine_types:
                if item not in seen:
                    seen.add(item)
                    unique_cuisine_types.append(item)
            
            self.logger.info(f"Extracted {len(unique_cuisine_types)} cuisine types: {unique_cuisine_types}")
            return unique_cuisine_types
            
        except Exception as e:
            self.logger.error(f"Error extracting cuisine types: {e}")
            return []
    
    async def _extract_restaurant_name(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Extract restaurant name with priority-based fallback to prevent overwriting issues
        
        Args:
            soup: BeautifulSoup object of the restaurant page
            url: Restaurant page URL for logging
            
        Returns:
            Extracted restaurant name or None if not found
        """
        # Priority-ordered selectors (most reliable first)
        name_selectors = [
            "h1[itemprop='name']",      # Schema.org marked - most specific
            "h1.header-title",          # HappyCow specific class
            ".venue h1",                # h1 inside venue content area
            "main h1",                  # h1 in main content area
            ".content h1",              # h1 in content area
            ".venue-title"              # Fallback venue title class
        ]
        
        for selector in name_selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    name = element.get_text(strip=True)
                    # Validate the extracted name
                    if name and name != "Unknown Restaurant" and len(name) > 1 and not name.startswith("http"):
                        # Apply cleanup function
                        from restaurant_field_mapping import clean_restaurant_name
                        cleaned_name = clean_restaurant_name(name)
                        if cleaned_name and cleaned_name != "Unknown Restaurant":
                            self.logger.info(f"Name extracted via '{selector}': '{cleaned_name}'")
                            return cleaned_name
            except Exception as e:
                self.logger.debug(f"Name selector '{selector}' failed: {e}")
                continue
        
        self.logger.warning(f"No valid restaurant name found via CSS selectors for {url}")
        return None

    def extract_multiple_reviews(self, soup: BeautifulSoup, limit: int = 5) -> List[Dict[str, str]]:
        """Extract multiple recent reviews from the page"""
        reviews = []
        
        # Find review elements
        review_elements = soup.find_all(attrs={"itemprop": "review"})
        
        for review_element in review_elements[:limit]:
            review_data = {}
            
            # Extract review text
            review_body = review_element.find(class_="comment-body")
            if review_body:
                review_data["text"] = review_body.get_text(strip=True)
            
            # Extract rating if available
            rating_element = review_element.find(attrs={"itemprop": "ratingValue"})
            if rating_element:
                review_data["rating"] = rating_element.get("content") or rating_element.get_text(strip=True)
            
            # Extract date
            date_element = review_element.get("data-date")
            if date_element:
                review_data["date"] = date_element
            
            if review_data.get("text"):
                reviews.append(review_data)
        
        return reviews

# Test function for the extraction engine
async def test_extraction_engine():
    """Test the extraction engine with sample restaurant pages"""
    engine = EnhancedExtractionEngine()
    
    # Test with saved HTML files
    test_files = [
        "html_analysis/sample_2.html",
        "html_analysis/sample_3.html", 
        "html_analysis/sample_5.html"
    ]
    
    for file_path in test_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract restaurant data
            data = await engine.extract_restaurant_data("test_url", html_content)
            
            print(f"\n=== Extraction Results for {file_path} ===")
            for field, value in data.items():
                print(f"{field}: {value}")
                
        except FileNotFoundError:
            print(f"Test file not found: {file_path}")
        except Exception as e:
            print(f"Error testing {file_path}: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction_engine()) 