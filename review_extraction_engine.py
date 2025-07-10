#!/usr/bin/env python3
"""
HappyCow Review Extraction Engine

Extracts comprehensive review data from restaurant pages including:
- Individual review details (rating, date, author, content)
- Review pagination handling
- Author information and dietary preferences
- Review metadata (points, review ID, etc.)
"""

import re
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dataclasses import dataclass
import aiohttp

logger = logging.getLogger(__name__)

@dataclass
class ReviewAuthor:
    """Review author information"""
    username: str
    profile_url: str
    avatar_url: str
    points: int
    dietary_preference: str  # vegan, vegetarian, etc.
    is_ambassador: bool = False

@dataclass
class RestaurantReview:
    """Individual restaurant review"""
    review_id: str
    author: ReviewAuthor
    rating: int  # 1-5 stars
    date: str  # formatted date
    date_timestamp: int  # unix timestamp
    title: str
    content: str
    language: str = "en"
    helpful_count: int = 0
    
class ReviewExtractionEngine:
    """Extracts reviews from HappyCow restaurant pages"""
    
    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        self.session = session
        self.base_url = "https://www.happycow.net"
        
    async def extract_all_reviews(self, restaurant_url: str, max_pages: int = 10) -> List[RestaurantReview]:
        """
        Extract all reviews from a restaurant page, handling pagination
        
        Args:
            restaurant_url: Full URL to restaurant page
            max_pages: Maximum number of review pages to scrape
            
        Returns:
            List of RestaurantReview objects
        """
        all_reviews = []
        current_page = 1
        
        while current_page <= max_pages:
            logger.info(f"Extracting reviews from page {current_page}")
            
            # Construct URL for specific page
            if current_page == 1:
                page_url = restaurant_url
            else:
                page_url = f"{restaurant_url}?page={current_page}"
            
            try:
                # Fetch page content
                if self.session:
                    async with self.session.get(page_url) as response:
                        if response.status != 200:
                            logger.warning(f"Failed to fetch page {current_page}: {response.status}")
                            break
                        html_content = await response.text()
                else:
                    # Fallback to requests if no session provided
                    import requests
                    response = requests.get(page_url)
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch page {current_page}: {response.status_code}")
                        break
                    html_content = response.text
                
                # Extract reviews from this page
                page_reviews = self.extract_reviews_from_html(html_content)
                
                if not page_reviews:
                    logger.info(f"No reviews found on page {current_page}, stopping")
                    break
                
                all_reviews.extend(page_reviews)
                logger.info(f"Extracted {len(page_reviews)} reviews from page {current_page}")
                
                # Check if there's a next page
                if not self.has_next_page(html_content, current_page):
                    logger.info("No more pages available")
                    break
                
                current_page += 1
                
                # Add delay between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error extracting reviews from page {current_page}: {e}")
                break
        
        logger.info(f"Extracted total of {len(all_reviews)} reviews from {current_page-1} pages")
        return all_reviews
    
    def extract_reviews_from_html(self, html_content: str) -> List[RestaurantReview]:
        """Extract reviews from a single page's HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        reviews = []
        
        # Find all review containers
        review_containers = soup.find_all('div', class_='comment-item')
        
        for container in review_containers:
            try:
                review = self.extract_single_review(container)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.warning(f"Failed to extract review: {e}")
                continue
        
        return reviews
    
    def extract_single_review(self, container: Tag) -> Optional[RestaurantReview]:
        """Extract a single review from its container"""
        try:
            # Extract review ID and metadata
            review_id = container.get('id', '')
            rating = int(container.get('data-rating', 0))
            date_timestamp = int(container.get('data-date', 0))
            
            # Extract author information
            author = self.extract_author_info(container)
            if not author:
                return None
            
            # Extract review content
            title_elem = container.find('h4', itemprop='headline')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Remove "Edit" link from title if present
            title = re.sub(r'\s*-\s*Edit\s*$', '', title)
            
            # Extract review body
            body_elem = container.find('p', itemprop='reviewBody')
            content = ""
            if body_elem:
                # Get text content, preserving line breaks
                content = body_elem.get_text(separator='\n', strip=True)
                # Clean up extra whitespace
                content = re.sub(r'\n+', '\n', content).strip()
            
            # Extract language
            language = "en"
            if body_elem and body_elem.get('lang'):
                language = body_elem.get('lang')
            
            # Format date
            date_str = ""
            if date_timestamp > 0:
                try:
                    date_obj = datetime.fromtimestamp(date_timestamp)
                    date_str = date_obj.strftime('%Y-%m-%d')
                except:
                    date_str = ""
            
            # Extract helpful count (if available)
            helpful_count = 0
            # This would need to be implemented if HappyCow has helpful votes
            
            return RestaurantReview(
                review_id=review_id,
                author=author,
                rating=rating,
                date=date_str,
                date_timestamp=date_timestamp,
                title=title,
                content=content,
                language=language,
                helpful_count=helpful_count
            )
            
        except Exception as e:
            logger.warning(f"Error extracting review: {e}")
            return None
    
    def extract_author_info(self, container: Tag) -> Optional[ReviewAuthor]:
        """Extract author information from review container"""
        try:
            # Find author name
            author_elem = container.find('span', itemprop='author')
            if not author_elem:
                return None
            
            username_meta = author_elem.find('meta', itemprop='name')
            if not username_meta:
                return None
            
            username = username_meta.get('content', '').strip()
            if not username:
                return None
            
            # Extract profile URL
            profile_link = container.find('a', href=re.compile(r'/members/profile/'))
            profile_url = ""
            if profile_link:
                profile_url = urljoin(self.base_url, profile_link.get('href', ''))
            
            # Extract avatar URL
            avatar_img = container.find('img', class_='p-avatar')
            avatar_url = ""
            if avatar_img:
                avatar_url = avatar_img.get('data-src') or avatar_img.get('src', '')
                if avatar_url and not avatar_url.startswith('http'):
                    avatar_url = urljoin(self.base_url, avatar_url)
            
            # Extract points
            points = 0
            points_elem = container.find('p', string=re.compile(r'Points \+\d+'))
            if points_elem:
                points_match = re.search(r'Points \+(\d+)', points_elem.get_text())
                if points_match:
                    points = int(points_match.group(1))
            
            # Extract dietary preference
            dietary_preference = ""
            label_elem = container.find('div', class_='label')
            if label_elem:
                dietary_preference = label_elem.get_text(strip=True).lower()
            
            # Check if ambassador
            is_ambassador = bool(container.find(class_='ambassador'))
            
            return ReviewAuthor(
                username=username,
                profile_url=profile_url,
                avatar_url=avatar_url,
                points=points,
                dietary_preference=dietary_preference,
                is_ambassador=is_ambassador
            )
            
        except Exception as e:
            logger.warning(f"Error extracting author info: {e}")
            return None
    
    def has_next_page(self, html_content: str, current_page: int) -> bool:
        """Check if there's a next page of reviews"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for pagination
        pagination = soup.find('ul', class_='pagination')
        if not pagination:
            return False
        
        # Check for "Next" link
        next_link = pagination.find('a', attrs={'aria-label': 'Next'})
        if next_link and 'pointer-events-none' not in next_link.get('class', []):
            return True
        
        # Alternative: check for page numbers higher than current
        page_links = pagination.find_all('a', class_='pagination-link')
        for link in page_links:
            try:
                page_num = int(link.get_text(strip=True))
                if page_num > current_page:
                    return True
            except (ValueError, TypeError):
                continue
        
        return False
    
    def get_review_summary(self, reviews: List[RestaurantReview]) -> Dict[str, Any]:
        """Generate summary statistics for reviews"""
        if not reviews:
            return {}
        
        total_reviews = len(reviews)
        ratings = [r.rating for r in reviews if r.rating > 0]
        
        summary = {
            'total_reviews': total_reviews,
            'average_rating': round(sum(ratings) / len(ratings), 2) if ratings else 0,
            'rating_distribution': {
                '5_star': len([r for r in ratings if r == 5]),
                '4_star': len([r for r in ratings if r == 4]),
                '3_star': len([r for r in ratings if r == 3]),
                '2_star': len([r for r in ratings if r == 2]),
                '1_star': len([r for r in ratings if r == 1])
            },
            'dietary_preferences': {},
            'recent_reviews': len([r for r in reviews if r.date_timestamp > 0 and 
                                 (datetime.now().timestamp() - r.date_timestamp) < (365 * 24 * 3600)]),
            'has_ambassador_reviews': any(r.author.is_ambassador for r in reviews)
        }
        
        # Count dietary preferences
        for review in reviews:
            pref = review.author.dietary_preference
            if pref:
                summary['dietary_preferences'][pref] = summary['dietary_preferences'].get(pref, 0) + 1
        
        return summary


# Test function
async def test_review_extraction():
    """Test the review extraction with sample HTML files"""
    engine = ReviewExtractionEngine()
    
    # Test with sample HTML files
    sample_files = [
        "html_analysis/sample_2.html",
        "html_analysis/sample_3.html", 
        "html_analysis/sample_5.html"
    ]
    
    for sample_file in sample_files:
        try:
            print(f"\n=== Testing {sample_file} ===")
            
            with open(sample_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            reviews = engine.extract_reviews_from_html(html_content)
            print(f"Extracted {len(reviews)} reviews")
            
            for i, review in enumerate(reviews[:2]):  # Show first 2 reviews
                print(f"\nReview {i+1}:")
                print(f"  ID: {review.review_id}")
                print(f"  Author: {review.author.username} ({review.author.dietary_preference})")
                print(f"  Rating: {review.rating}/5")
                print(f"  Date: {review.date}")
                print(f"  Title: {review.title}")
                print(f"  Content: {review.content[:100]}...")
                print(f"  Points: {review.author.points}")
            
            # Generate summary
            summary = engine.get_review_summary(reviews)
            print(f"\nSummary: {summary}")
            
        except Exception as e:
            print(f"Error testing {sample_file}: {e}")


if __name__ == "__main__":
    asyncio.run(test_review_extraction()) 