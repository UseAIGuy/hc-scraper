"""
Debug script to investigate what CSS selectors actually exist on HappyCow restaurant pages
"""

import asyncio
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def investigate_restaurant_page_selectors():
    """Investigate what selectors actually exist on a restaurant page"""
    
    restaurant_url = "https://www.happycow.net/reviews/tane-vegan-izakaya-los-angeles-467122/"
    
    print("🔍 Investigating Restaurant Page Selectors")
    print("=" * 60)
    print(f"🍽️  URL: {restaurant_url}")
    
    async with AsyncWebCrawler(verbose=False) as crawler:
        # First, try to get the page without any wait conditions
        config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            page_timeout=30000,
            delay_before_return_html=3.0,
            # NO wait_for - just get whatever loads
            css_selector="body",
            screenshot=False,
            verbose=False
        )
        
        print("\n🚀 Step 1: Getting page content without wait conditions...")
        
        result = await crawler.arun(url=restaurant_url, config=config)
        
        if result.success:
            print(f"✅ SUCCESS! Got HTML content: {len(result.html)} characters")
            
            # Analyze the HTML to find common selectors
            html = result.html
            
            print("\n🔍 Step 2: Analyzing HTML structure...")
            
            # Check for various selector patterns
            selectors_to_check = [
                # Our current restaurant selectors
                ".restaurant-header", ".venue-header", ".restaurant-details", ".venue-details", 
                ".reviews-section", ".no-restaurant", ".captcha",
                
                # Original city listing selectors (should NOT exist)
                ".card-listing", ".venue-list-item", ".no-results",
                
                # Common HappyCow patterns we found before
                ".venue-item", ".venue-item-link",
                
                # Generic selectors that might exist
                "h1", "h2", "h3", ".title", ".name", ".restaurant", ".venue",
                ".content", ".main", ".page", ".container", ".wrapper",
                ".review", ".rating", ".address", ".phone", ".hours",
                ".description", ".details", ".info", ".header", ".footer",
                
                # Specific HappyCow patterns to look for
                ".venue-info", ".venue-name", ".venue-title", ".restaurant-info",
                ".restaurant-name", ".restaurant-title", ".listing", ".profile",
                ".venue-profile", ".restaurant-profile"
            ]
            
            found_selectors = []
            missing_selectors = []
            
            for selector in selectors_to_check:
                # Count occurrences of this selector in the HTML
                if selector.startswith('.'):
                    # Class selector
                    class_name = selector[1:]  # Remove the dot
                    pattern = rf'class="[^"]*\b{re.escape(class_name)}\b[^"]*"'
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    count = len(matches)
                else:
                    # Element selector
                    pattern = rf'<{re.escape(selector)}[\s>]'
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    count = len(matches)
                
                if count > 0:
                    found_selectors.append((selector, count))
                else:
                    missing_selectors.append(selector)
            
            print(f"\n✅ FOUND SELECTORS ({len(found_selectors)}):")
            for selector, count in found_selectors:
                print(f"   {selector}: {count} matches")
            
            print(f"\n❌ MISSING SELECTORS ({len(missing_selectors)}):")
            for selector in missing_selectors:
                print(f"   {selector}: 0 matches")
            
            # Check if this looks like a valid restaurant page
            restaurant_indicators = ["restaurant", "venue", "review", "rating", "address", "vegan"]
            found_indicators = []
            for indicator in restaurant_indicators:
                if indicator.lower() in html.lower():
                    found_indicators.append(indicator)
            
            print(f"\n📋 CONTENT INDICATORS:")
            print(f"   Found indicators: {found_indicators}")
            print(f"   Page looks like restaurant page: {'YES' if len(found_indicators) >= 3 else 'NO'}")
            
            # Look for specific HappyCow structure patterns
            print(f"\n🏗️  HAPPYCOW STRUCTURE ANALYSIS:")
            
            # Check for common HappyCow div structures
            div_classes = re.findall(r'<div[^>]*class="([^"]*)"', html, re.IGNORECASE)
            unique_classes = set()
            for class_attr in div_classes:
                for cls in class_attr.split():
                    if cls and 'venue' in cls.lower() or 'restaurant' in cls.lower():
                        unique_classes.add(cls)
            
            if unique_classes:
                print(f"   Venue/Restaurant related classes: {sorted(unique_classes)}")
            else:
                print(f"   No obvious venue/restaurant classes found")
            
            # Check for any elements that could be used as wait conditions
            print(f"\n💡 SUGGESTED WAIT CONDITIONS:")
            reliable_selectors = []
            for selector, count in found_selectors:
                if count > 0 and count < 50:  # Not too common, not too rare
                    if any(keyword in selector.lower() for keyword in ['h1', 'h2', 'title', 'main', 'content', 'container']):
                        reliable_selectors.append(selector)
            
            if reliable_selectors:
                print(f"   Potential wait selectors: {reliable_selectors[:5]}")
            else:
                print(f"   Could try: h1, .content, .main, .container")
                
            return True
            
        else:
            print(f"❌ FAILED to get page content")
            print(f"   Error: {getattr(result, 'error_message', 'Unknown error')}")
            return False

if __name__ == "__main__":
    success = asyncio.run(investigate_restaurant_page_selectors())
    
    if success:
        print(f"\n🎯 CONCLUSION:")
        print(f"   The page loads successfully without wait conditions.")
        print(f"   Our restaurant selectors may be incorrect.")
        print(f"   We need to update our CSS selector configuration.")
    else:
        print(f"\n⚠️  CONCLUSION:")
        print(f"   The page itself may be blocked or inaccessible.") 