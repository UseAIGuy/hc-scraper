#!/usr/bin/env python3
"""
Test suite for HappyCow scraper with HTML fixtures
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

# Import the scraper components
from scraper import HappyCowScraper, RestaurantListing, RestaurantDetail, StealthConfig
from config import ScraperConfig

class TestHappyCowScraper:
    """Test suite for HappyCow scraper"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        return ScraperConfig(
            supabase_url="https://test.supabase.co",
            supabase_key="test-key",
            use_local_llm=True,
            max_workers=1,
            test_mode=True
        )
    
    @pytest.fixture
    def sample_city_html(self):
        """Sample HTML for a city listings page"""
        return """
        <html>
        <head><title>Austin Vegan Restaurants - HappyCow</title></head>
        <body>
            <div class="venue-list">
                <div class="venue-list-item">
                    <h3><a href="/reviews/green-seed-vegan-austin-123456">Green Seed Vegan</a></h3>
                    <div class="venue-type">Fully Vegan</div>
                    <div class="venue-featured">Featured</div>
                </div>
                <div class="venue-list-item">
                    <h3><a href="/reviews/verdine-austin-789012">Verdine</a></h3>
                    <div class="venue-type">Vegan Options</div>
                </div>
                <div class="venue-list-item">
                    <h3><a href="/reviews/counter-culture-austin-345678">Counter Culture</a></h3>
                    <div class="venue-type">Vegan-Friendly</div>
                    <div class="venue-new">New</div>
                </div>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def sample_restaurant_html(self):
        """Sample HTML for a restaurant detail page"""
        return """
        <html>
        <head><title>Green Seed Vegan - Austin Restaurant - HappyCow</title></head>
        <body>
            <div class="venue-details">
                <h1>Green Seed Vegan</h1>
                <div class="venue-description">
                    A fully plant-based restaurant serving creative comfort food with local ingredients.
                </div>
                <div class="venue-address">
                    <span>1611 W 5th St, Austin, TX 78703</span>
                </div>
                <div class="venue-phone">
                    <span>(512) 444-5595</span>
                </div>
                <div class="venue-website">
                    <a href="https://greenseedvegan.com">greenseedvegan.com</a>
                </div>
                <div class="venue-cuisine">
                    <span>American</span>, <span>Comfort Food</span>
                </div>
                <div class="venue-rating">
                    <span class="rating-stars" data-rating="4.5">4.5 stars</span>
                    <span class="review-count">127 reviews</span>
                </div>
                <div class="venue-hours">
                    <div>Mon-Thu: 11:00 AM - 9:00 PM</div>
                    <div>Fri-Sat: 11:00 AM - 10:00 PM</div>
                    <div>Sun: 11:00 AM - 9:00 PM</div>
                </div>
                <div class="venue-features">
                    <span>Delivery</span>, <span>Takeout</span>, <span>Outdoor Seating</span>
                </div>
                <div class="venue-map" data-lat="30.2672" data-lng="-97.7431">
                    <iframe src="https://maps.google.com/maps?q=30.2672,-97.7431"></iframe>
                </div>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def expected_listings(self):
        """Expected extraction results for city listings"""
        return [
            {
                "name": "Green Seed Vegan",
                "url": "/reviews/green-seed-vegan-austin-123456",
                "listing_type": "fully vegan",
                "is_featured": True,
                "is_new": False
            },
            {
                "name": "Verdine", 
                "url": "/reviews/verdine-austin-789012",
                "listing_type": "vegan options",
                "is_featured": False,
                "is_new": False
            },
            {
                "name": "Counter Culture",
                "url": "/reviews/counter-culture-austin-345678", 
                "listing_type": "vegan-friendly",
                "is_featured": False,
                "is_new": True
            }
        ]
    
    @pytest.fixture
    def expected_detail(self):
        """Expected extraction results for restaurant details"""
        return {
            "name": "Green Seed Vegan",
            "description": "A fully plant-based restaurant serving creative comfort food with local ingredients.",
            "address": "1611 W 5th St, Austin, TX 78703",
            "phone": "(512) 444-5595",
            "website": "https://greenseedvegan.com",
            "cuisine_types": ["American", "Comfort Food"],
            "rating": 4.5,
            "review_count": 127,
            "latitude": 30.2672,
            "longitude": -97.7431,
            "features": ["Delivery", "Takeout", "Outdoor Seating"],
            "hours": {
                "monday": "11:00 AM - 9:00 PM",
                "tuesday": "11:00 AM - 9:00 PM", 
                "wednesday": "11:00 AM - 9:00 PM",
                "thursday": "11:00 AM - 9:00 PM",
                "friday": "11:00 AM - 10:00 PM",
                "saturday": "11:00 AM - 10:00 PM",
                "sunday": "11:00 AM - 9:00 PM"
            }
        }
    
    @pytest.mark.asyncio
    async def test_restaurant_listing_model(self, expected_listings):
        """Test RestaurantListing model validation"""
        for listing_data in expected_listings:
            listing_data['city'] = 'Austin'
            listing = RestaurantListing(**listing_data)
            
            assert listing.name == listing_data['name']
            assert listing.url == listing_data['url']
            assert listing.city == 'Austin'
            assert listing.listing_type == listing_data['listing_type']
            assert listing.is_featured == listing_data['is_featured']
            assert listing.is_new == listing_data['is_new']
    
    @pytest.mark.asyncio
    async def test_restaurant_detail_model(self, expected_detail):
        """Test RestaurantDetail model validation"""
        # Add required fields
        detail_data = expected_detail.copy()
        detail_data.update({
            'city': 'Austin',
            'happycow_url': 'https://happycow.net/reviews/green-seed-vegan-austin-123456',
            'vegan_status': 'fully vegan'
        })
        
        detail = RestaurantDetail(**detail_data)
        
        # Test required fields
        assert detail.name == expected_detail['name']
        assert detail.city == 'Austin'
        assert detail.happycow_url == detail_data['happycow_url']
        
        # Test optional fields
        assert detail.description == expected_detail['description']
        assert detail.address == expected_detail['address']
        assert detail.phone == expected_detail['phone']
        assert detail.website == expected_detail['website']
        assert detail.rating == expected_detail['rating']
        assert detail.latitude == expected_detail['latitude']
        assert detail.longitude == expected_detail['longitude']
        
        # Test arrays
        assert detail.cuisine_types == expected_detail['cuisine_types']
        assert detail.features == expected_detail['features']
    
    @pytest.mark.asyncio
    async def test_rating_validation(self):
        """Test rating field validation"""
        # Valid ratings
        for rating in [0, 2.5, 5.0, 4.8]:
            detail = RestaurantDetail(
                name="Test Restaurant",
                city="Austin", 
                happycow_url="https://test.com",
                rating=rating
            )
            assert detail.rating == rating
        
        # Invalid ratings should be set to None
        for rating in [-1, 6.0, 10]:
            detail = RestaurantDetail(
                name="Test Restaurant",
                city="Austin",
                happycow_url="https://test.com", 
                rating=rating
            )
            assert detail.rating is None
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, mock_config):
        """Test scraper initialization with configuration"""
        scraper = HappyCowScraper(
            mock_config.supabase_url,
            mock_config.supabase_key,
            use_local_llm=mock_config.use_local_llm,
            max_workers=mock_config.max_workers,
            min_delay=mock_config.min_delay,
            max_delay=mock_config.max_delay,
            batch_delay=mock_config.batch_delay
        )
        
        assert scraper.use_local_llm == mock_config.use_local_llm
        assert scraper.max_workers == mock_config.max_workers
        assert scraper.min_delay == mock_config.min_delay
        assert scraper.max_delay == mock_config.max_delay
        assert scraper.batch_delay == mock_config.batch_delay
        assert scraper.base_url == "https://www.happycow.net"
    
    @pytest.mark.asyncio
    async def test_human_delay_timing(self, mock_config):
        """Test human delay respects configured timing"""
        scraper = HappyCowScraper(
            mock_config.supabase_url,
            mock_config.supabase_key,
            min_delay=0.1,
            max_delay=0.2
        )
        
        import time
        start_time = time.time()
        await scraper.human_delay()
        elapsed = time.time() - start_time
        
        # Should be between min and max delay
        assert 0.1 <= elapsed <= 0.3  # Allow small buffer for execution time
    
    @pytest.mark.asyncio
    async def test_check_existing_restaurant(self, mock_config):
        """Test checking for existing restaurants in database"""
        with patch('scraper.create_client') as mock_create_client:
            mock_supabase = Mock()
            mock_create_client.return_value = mock_supabase
            
            # Mock existing restaurant
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{'id': '123'}]
            
            scraper = HappyCowScraper(mock_config.supabase_url, mock_config.supabase_key)
            
            exists = await scraper.check_existing_restaurant("https://test.com")
            assert exists is True
            
            # Mock non-existing restaurant
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            
            exists = await scraper.check_existing_restaurant("https://test2.com")
            assert exists is False
    
    @pytest.mark.asyncio
    async def test_extraction_strategy_creation(self, mock_config):
        """Test LLM extraction strategy creation"""
        scraper = HappyCowScraper(mock_config.supabase_url, mock_config.supabase_key)
        
        # Test listing extraction strategy
        listing_strategy = scraper._get_listing_extraction_strategy()
        assert listing_strategy is not None
        
        # Test detail extraction strategy  
        detail_strategy = scraper._get_detail_extraction_strategy()
        assert detail_strategy is not None
        
        # Test local LLM vs OpenAI configuration
        scraper.use_local_llm = True
        local_strategy = scraper._get_listing_extraction_strategy()
        assert "ollama" in str(local_strategy.provider).lower()
        
        scraper.use_local_llm = False
        openai_strategy = scraper._get_listing_extraction_strategy()
        assert "openai" in str(openai_strategy.provider).lower()

class TestDataValidation:
    """Test data validation and edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_fields_handling(self):
        """Test handling of empty and null fields"""
        # Test with minimal required fields
        detail = RestaurantDetail(
            name="Test Restaurant",
            city="Austin",
            happycow_url="https://test.com"
        )
        
        assert detail.name == "Test Restaurant"
        assert detail.city == "Austin"
        assert detail.description is None
        assert detail.address is None
        assert detail.cuisine_types == []
        assert detail.features == []
        assert detail.recent_reviews == []
    
    @pytest.mark.asyncio
    async def test_url_id_extraction(self):
        """Test HappyCow ID extraction from URLs"""
        test_urls = [
            ("/reviews/green-seed-vegan-austin-123456", "123456"),
            ("/reviews/verdine-austin-789012/", "789012"),
            ("/reviews/restaurant-name-city-999999?param=value", "999999"),
            ("/reviews/no-id-here", None)
        ]
        
        import re
        for url, expected_id in test_urls:
            id_match = re.search(r'-(\d+)/?$', url.split('?')[0])  # Remove query params
            actual_id = id_match.group(1) if id_match else None
            assert actual_id == expected_id
    
    @pytest.mark.asyncio
    async def test_stealth_config(self):
        """Test stealth configuration"""
        headers = StealthConfig.get_headers()
        
        # Check required headers
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        
        # Check user agent is from predefined list
        assert headers["User-Agent"] in StealthConfig.USER_AGENTS
        
        # Test delay ranges
        assert StealthConfig.MIN_DELAY > 0
        assert StealthConfig.MAX_DELAY > StealthConfig.MIN_DELAY
        assert StealthConfig.BATCH_DELAY > StealthConfig.MAX_DELAY

class TestIntegrationScenarios:
    """Integration tests for common scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_mock(self, mock_config):
        """Test complete scraping workflow with mocked components"""
        with patch('scraper.create_client') as mock_create_client, \
             patch('scraper.AsyncWebCrawler') as mock_crawler_class:
            
            # Setup mocks
            mock_supabase = Mock()
            mock_create_client.return_value = mock_supabase
            
            mock_crawler = AsyncMock()
            mock_crawler_class.return_value = mock_crawler
            
            # Mock successful extraction
            mock_result = Mock()
            mock_result.success = True
            mock_result.extracted_content = json.dumps([{
                "name": "Test Restaurant",
                "url": "/reviews/test-restaurant-123456",
                "listing_type": "fully vegan",
                "is_featured": False,
                "is_new": False
            }])
            
            mock_crawler.arun.return_value = mock_result
            
            # Mock database operations
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
            mock_supabase.table.return_value.upsert.return_value.execute.return_value = Mock()
            
            # Create and test scraper
            scraper = HappyCowScraper(mock_config.supabase_url, mock_config.supabase_key)
            
            async with scraper:
                # Test city listings
                listings = await scraper.scrape_city_listings("https://test.com", "Austin")
                assert len(listings) == 1
                assert listings[0].name == "Test Restaurant"
                
                # Test restaurant detail (mock different extraction)
                mock_result.extracted_content = json.dumps({
                    "name": "Test Restaurant",
                    "description": "A test restaurant",
                    "address": "123 Test St",
                    "rating": 4.5
                })
                
                detail = await scraper.scrape_restaurant_detail(listings[0])
                assert detail is not None
                assert detail.name == "Test Restaurant"
                assert detail.rating == 4.5
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_config):
        """Test error handling in various scenarios"""
        with patch('scraper.create_client') as mock_create_client:
            mock_supabase = Mock()
            mock_create_client.return_value = mock_supabase
            
            scraper = HappyCowScraper(mock_config.supabase_url, mock_config.supabase_key)
            
            # Test database connection error
            mock_supabase.table.side_effect = Exception("Database error")
            
            exists = await scraper.check_existing_restaurant("https://test.com")
            assert exists is False  # Should return False on error
            
            # Test invalid JSON extraction
            with patch.object(scraper, 'crawler') as mock_crawler:
                mock_result = Mock()
                mock_result.success = True
                mock_result.extracted_content = "invalid json"
                mock_crawler.arun.return_value = mock_result
                
                listings = await scraper.scrape_city_listings("https://test.com", "Austin")
                assert listings == []  # Should return empty list on JSON error

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 