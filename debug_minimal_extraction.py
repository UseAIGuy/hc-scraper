#!/usr/bin/env python3
"""
Minimal test to isolate Crawl4AI + Ollama LLM extraction issue
"""
import asyncio
import json
import logging
import os
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler, LLMConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set environment variables for LiteLLM
os.environ["CRAWL4AI_ENABLE_LLM"] = "1"

class SimpleRestaurant(BaseModel):
    name: str
    url: str

async def test_minimal_extraction():
    """Test minimal LLM extraction with correct Crawl4AI 0.6.3 config"""
    
    # For Crawl4AI 0.6.3 with LiteLLM backend, use this format:
    llm_config = LLMConfig(
        provider="ollama/llama2",  # LiteLLM format for Ollama
        base_url="http://localhost:11434",  # Remove /v1 suffix
        api_token="dummy"  # LiteLLM requires some token
    )
    
    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        instruction="Extract restaurant names and URLs from this HappyCow page. Return JSON array with 'name' and 'url' fields.",
        schema={"type": "array", "items": SimpleRestaurant.model_json_schema()},
        extraction_type="schema",
        extra_args={"temperature": 0.1}
    )
    
    # CRITICAL: Use CrawlerRunConfig for Crawl4AI 0.6.3
    crawl_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        cache_mode=CacheMode.BYPASS,
        wait_for="css:.venue-list-item,.listing-item",
        page_timeout=60000
    )
    
    print("🔧 Testing Crawl4AI 0.6.3 + CrawlerRunConfig + LiteLLM + Ollama...")
    print(f"LLM Provider: {llm_config.provider}")
    print(f"Base URL: {llm_config.base_url}")
    print(f"CRAWL4AI_ENABLE_LLM: {os.getenv('CRAWL4AI_ENABLE_LLM')}")
    
    async with AsyncWebCrawler(
        headless=True,
        verbose=True,
        browser_type="chromium"
    ) as crawler:
        
        print("🌐 Crawling HappyCow Austin page with CrawlerRunConfig...")
        
        result = await crawler.arun(
            url="https://www.happycow.net/north_america/usa/texas/austin/",
            config=crawl_config
        )
        
        print(f"✅ Crawl success: {result.success}")
        print(f"📄 HTML length: {len(result.html) if result.html else 0}")
        print(f"🔍 Extracted content: {result.extracted_content}")
        print(f"❌ Error message: {result.error_message}")
        
        # Check for additional result attributes
        for attr in ['traceback', 'llm_response', 'extraction_logs', 'session_id']:
            if hasattr(result, attr):
                value = getattr(result, attr)
                if value:
                    print(f"🔍 {attr}: {value}")
        
        if result.extracted_content:
            try:
                data = json.loads(result.extracted_content)
                print(f"🎯 SUCCESS! Parsed {len(data)} restaurants")
                for i, restaurant in enumerate(data[:3]):  # Show first 3
                    print(f"  {i+1}. {restaurant}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
        else:
            print("❌ No extracted content - LLM still not called!")

if __name__ == "__main__":
    asyncio.run(test_minimal_extraction()) 