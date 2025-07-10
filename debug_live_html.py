#!/usr/bin/env python3
"""
Debug Live HTML

Check what HTML structure we actually get from a live HappyCow page
to understand why our selectors aren't working.
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def debug_live_html():
    """Debug what HTML we get from a live page"""
    
    # Test URL
    test_url = "https://www.happycow.net/reviews/nunos-tacos-vegmex-grill-dallas-174703"
    
    print(f"🌐 FETCHING: {test_url}")
    print("=" * 80)
    
    # Fetch the live page
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    print(f"✅ Successfully fetched page (status: {response.status})")
                    print(f"📏 Content length: {len(html_content)} characters")
                else:
                    print(f"❌ Failed to fetch page (status: {response.status})")
                    return
        except Exception as e:
            print(f"❌ Error fetching page: {e}")
            return
    
    # Parse and analyze
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\n🔍 HTML STRUCTURE ANALYSIS:")
    print("-" * 40)
    
    # Check title
    title = soup.find('title')
    if title:
        print(f"📄 Page title: {title.get_text(strip=True)}")
    else:
        print("❌ No title found")
    
    # Check if page has JavaScript requirement
    noscript = soup.find('noscript')
    if noscript:
        print(f"⚠️  NoScript content found: {noscript.get_text(strip=True)[:100]}...")
    
    # Look for common elements
    print("\n🔍 LOOKING FOR COMMON ELEMENTS:")
    print("-" * 40)
    
    # Check for h1 elements
    h1_elements = soup.find_all('h1')
    print(f"📍 H1 elements found: {len(h1_elements)}")
    for i, h1 in enumerate(h1_elements[:3]):
        print(f"  [{i}] {h1.get_text(strip=True)}")
    
    # Check for any elements with itemprop
    itemprop_elements = soup.find_all(attrs={'itemprop': True})
    print(f"📊 Elements with itemprop: {len(itemprop_elements)}")
    for i, elem in enumerate(itemprop_elements[:5]):
        itemprop = elem.get('itemprop')
        text = elem.get_text(strip=True)[:50]
        print(f"  [{i}] itemprop='{itemprop}': {text}")
    
    # Check for any elements with class containing 'label'
    label_elements = soup.find_all(class_=lambda x: x and 'label' in ' '.join(x))
    print(f"🏷️  Elements with 'label' class: {len(label_elements)}")
    for i, elem in enumerate(label_elements[:3]):
        classes = elem.get('class', [])
        text = elem.get_text(strip=True)
        print(f"  [{i}] Classes: {classes}, Text: '{text}'")
    
    # Check for any elements with class containing 'bg-'
    bg_elements = soup.find_all(class_=lambda x: x and any('bg-' in cls for cls in x))
    print(f"🎨 Elements with 'bg-' classes: {len(bg_elements)}")
    for i, elem in enumerate(bg_elements[:5]):
        classes = elem.get('class', [])
        bg_classes = [cls for cls in classes if 'bg-' in cls]
        text = elem.get_text(strip=True)[:30]
        print(f"  [{i}] BG classes: {bg_classes}, Text: '{text}'")
    
    # Check body class
    body = soup.find('body')
    if body:
        body_classes = body.get('class', [])
        print(f"📄 Body classes: {body_classes}")
    
    # Save a sample for inspection
    print(f"\n💾 SAVING SAMPLE HTML...")
    with open('live_page_sample.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("✅ Saved to 'live_page_sample.html'")
    
    # Show first 500 chars of actual content
    print(f"\n📝 FIRST 500 CHARACTERS:")
    print("-" * 40)
    print(html_content[:500])

if __name__ == "__main__":
    asyncio.run(debug_live_html()) 