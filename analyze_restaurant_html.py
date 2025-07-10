#!/usr/bin/env python3
"""
HappyCow Restaurant Page HTML Analysis Script

This script fetches sample restaurant listing pages from HappyCow
and analyzes their HTML structure to identify all extractable data fields.
"""

import requests
import os
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Set
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

class HappyCowHTMLAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Create output directory
        self.output_dir = "html_analysis"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Sample restaurant URLs (you can add more)
        self.sample_urls = [
            "https://www.happycow.net/reviews/verdura-lavender-bay-3906",
            "https://www.happycow.net/reviews/ginger-elizabeth-chocolates-sacramento-27816",
            "https://www.happycow.net/reviews/crossroads-kitchen-west-hollywood-23965",
            "https://www.happycow.net/reviews/plant-food-and-wine-venice-34567",
            "https://www.happycow.net/reviews/shojin-little-tokyo-los-angeles-6033"
        ]
        
    def fetch_and_save_html(self, url: str, filename: str) -> bool:
        """Fetch HTML from URL and save to file"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Save raw HTML
            html_path = os.path.join(self.output_dir, f"{filename}.html")
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"Saved HTML to: {html_path}")
            return True
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return False
    
    def analyze_html_structure(self, html_path: str) -> Dict:
        """Analyze HTML structure and extract potential data fields"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            analysis = {
                'url': html_path,
                'title': soup.title.string if soup.title else None,
                'meta_tags': {},
                'structured_data': [],
                'potential_fields': {},
                'css_classes': set(),
                'ids': set(),
                'text_patterns': {}
            }
            
            # Extract meta tags
            for meta in soup.find_all('meta'):
                if hasattr(meta, 'attrs'):
                    if 'property' in meta.attrs:
                        analysis['meta_tags'][meta.attrs['property']] = meta.attrs.get('content', '')
                    elif 'name' in meta.attrs:
                        analysis['meta_tags'][meta.attrs['name']] = meta.attrs.get('content', '')
            
            # Extract structured data (JSON-LD)
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    analysis['structured_data'].append(data)
                except:
                    pass
            
            # Collect all CSS classes and IDs
            for element in soup.find_all(True):
                if element.get('class'):
                    analysis['css_classes'].update(element['class'])
                if element.get('id'):
                    analysis['ids'].add(element['id'])
            
            # Look for common restaurant data patterns
            self._find_restaurant_patterns(soup, analysis)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing {html_path}: {e}")
            return {}
    
    def _find_restaurant_patterns(self, soup: BeautifulSoup, analysis: Dict):
        """Find common restaurant data patterns in HTML"""
        
        # Common patterns to look for
        patterns = {
            'name': ['h1', 'h2', '.restaurant-name', '.venue-name', '.title'],
            'address': ['.address', '.location', '.venue-address', '[itemprop="address"]'],
            'phone': ['.phone', '.telephone', '[itemprop="telephone"]', 'a[href^="tel:"]'],
            'website': ['.website', '.url', '[itemprop="url"]', 'a[href^="http"]'],
            'rating': ['.rating', '.stars', '.score', '[itemprop="ratingValue"]'],
            'reviews': ['.reviews', '.review-count', '[itemprop="reviewCount"]'],
            'cuisine': ['.cuisine', '.category', '.tags', '[itemprop="servesCuisine"]'],
            'hours': ['.hours', '.opening-hours', '[itemprop="openingHours"]'],
            'price': ['.price', '.price-range', '[itemprop="priceRange"]'],
            'description': ['.description', '.about', '[itemprop="description"]'],
            'social_media': ['a[href*="facebook"]', 'a[href*="instagram"]', 'a[href*="twitter"]']
        }
        
        for field, selectors in patterns.items():
            analysis['potential_fields'][field] = []
            
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True) if element else ""
                        if text:
                            analysis['potential_fields'][field].append({
                                'selector': selector,
                                'text': text[:200],  # Truncate for readability
                                'tag': element.name,
                                'classes': element.get('class', []),
                                'id': element.get('id', ''),
                                'href': element.get('href', '') if element.name == 'a' else ''
                            })
                except:
                    pass
        
        # Look for text patterns
        page_text = soup.get_text()
        
        # Phone patterns
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, page_text)
        if phones:
            analysis['text_patterns']['phones'] = phones
        
        # Email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_text)
        if emails:
            analysis['text_patterns']['emails'] = emails
        
        # Hours patterns
        hours_pattern = r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)\b'
        hours = re.findall(hours_pattern, page_text)
        if hours:
            analysis['text_patterns']['hours'] = hours
    
    def run_analysis(self):
        """Run complete analysis on sample URLs"""
        print("Starting HappyCow HTML Analysis...")
        
        analyses = []
        
        for i, url in enumerate(self.sample_urls):
            filename = f"sample_{i+1}"
            
            # Fetch and save HTML
            if self.fetch_and_save_html(url, filename):
                # Wait between requests
                time.sleep(2)
                
                # Analyze HTML structure
                html_path = os.path.join(self.output_dir, f"{filename}.html")
                analysis = self.analyze_html_structure(html_path)
                if analysis:
                    analyses.append(analysis)
        
        # Save combined analysis
        analysis_path = os.path.join(self.output_dir, "combined_analysis.json")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analyses, f, indent=2, default=str)
        
        print(f"Analysis complete! Results saved to: {analysis_path}")
        
        # Generate summary report
        self._generate_summary_report(analyses)
    
    def _generate_summary_report(self, analyses: List[Dict]):
        """Generate a human-readable summary report"""
        report_path = os.path.join(self.output_dir, "analysis_summary.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("HappyCow Restaurant Page Analysis Summary\n")
            f.write("=" * 50 + "\n\n")
            
            # Common CSS classes across all pages
            all_classes = set()
            all_ids = set()
            common_fields = {}
            
            for analysis in analyses:
                all_classes.update(analysis.get('css_classes', set()))
                all_ids.update(analysis.get('ids', set()))
                
                for field, data in analysis.get('potential_fields', {}).items():
                    if field not in common_fields:
                        common_fields[field] = []
                    common_fields[field].extend(data)
            
            f.write(f"Analyzed {len(analyses)} restaurant pages\n\n")
            
            f.write("COMMON CSS CLASSES:\n")
            f.write("-" * 20 + "\n")
            for cls in sorted(all_classes):
                f.write(f"  .{cls}\n")
            
            f.write(f"\nCOMMON IDS:\n")
            f.write("-" * 20 + "\n")
            for id_name in sorted(all_ids):
                f.write(f"  #{id_name}\n")
            
            f.write(f"\nPOTENTIAL DATA FIELDS:\n")
            f.write("-" * 20 + "\n")
            for field, data in common_fields.items():
                f.write(f"\n{field.upper()}:\n")
                unique_selectors = set()
                for item in data:
                    if item.get('selector'):
                        unique_selectors.add(item['selector'])
                
                for selector in sorted(unique_selectors):
                    f.write(f"  {selector}\n")
            
            f.write(f"\nSTRUCTURED DATA FOUND:\n")
            f.write("-" * 20 + "\n")
            for analysis in analyses:
                for data in analysis.get('structured_data', []):
                    f.write(f"  Type: {data.get('@type', 'Unknown')}\n")
                    if '@context' in data:
                        f.write(f"  Context: {data['@context']}\n")
        
        print(f"Summary report saved to: {report_path}")

async def analyze_both_page_types():
    """Analyze both city listing pages and individual restaurant pages"""
    
    async with AsyncWebCrawler(headless=True) as crawler:
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            screenshot=False,
            verbose=False
        )
        
        print("🔍 Analyzing HappyCow page types...")
        
        # Test city listing page
        print("\n📍 CITY LISTING PAGE:")
        print("=" * 50)
        city_url = 'https://www.happycow.net/north_america/usa/texas/dallas/'
        city_result = await crawler.arun(url=city_url, config=config)
        
        if city_result.success:
            print(f"✅ City page loaded successfully ({len(city_result.html)} chars)")
            
            # Look for specific patterns
            patterns_to_check = [
                ('restaurant-item', r'class="[^"]*restaurant-item[^"]*"'),
                ('venue-item', r'class="[^"]*venue-item[^"]*"'),
                ('card-listing', r'class="[^"]*card-listing[^"]*"'),
                ('venue-list-item', r'class="[^"]*venue-list-item[^"]*"'),
                ('city-results', r'class="[^"]*city-results[^"]*"'),
                ('no-results', r'class="[^"]*no-results[^"]*"'),
                ('captcha', r'class="[^"]*captcha[^"]*"'),
                ('venue-item-link', r'class="[^"]*venue-item-link[^"]*"')
            ]
            
            print("CSS Classes found:")
            for name, pattern in patterns_to_check:
                matches = re.findall(pattern, city_result.html)
                print(f"  .{name}: {len(matches)} matches")
            
            # Save sample for inspection
            with open('city_page_sample.html', 'w', encoding='utf-8') as f:
                f.write(city_result.html[:5000])  # First 5000 chars
                
        else:
            print("❌ Failed to load city page")
            
        # Test individual restaurant page
        print("\n🍽️ INDIVIDUAL RESTAURANT PAGE:")
        print("=" * 50)
        
        # Get a restaurant URL from the city page first
        restaurant_url = None
        if city_result.success:
            # Look for restaurant links
            restaurant_links = re.findall(r'href="(/north_america/usa/texas/dallas/[^"]+)"', city_result.html)
            if restaurant_links:
                restaurant_url = f"https://www.happycow.net{restaurant_links[0]}"
                print(f"Testing restaurant: {restaurant_url}")
                
                restaurant_result = await crawler.arun(url=restaurant_url, config=config)
                
                if restaurant_result.success:
                    print(f"✅ Restaurant page loaded successfully ({len(restaurant_result.html)} chars)")
                    
                    print("CSS Classes found:")
                    for name, pattern in patterns_to_check:
                        matches = re.findall(pattern, restaurant_result.html)
                        print(f"  .{name}: {len(matches)} matches")
                    
                    # Save sample
                    with open('restaurant_page_sample.html', 'w', encoding='utf-8') as f:
                        f.write(restaurant_result.html[:5000])
                        
                else:
                    print("❌ Failed to load restaurant page")
            else:
                print("❌ No restaurant links found in city page")
                
        print("\n🔍 ANALYSIS COMPLETE")
        print("Check city_page_sample.html and restaurant_page_sample.html for details")

if __name__ == "__main__":
    asyncio.run(analyze_both_page_types()) 