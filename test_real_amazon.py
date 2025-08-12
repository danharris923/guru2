#!/usr/bin/env python3
"""
Test what's actually happening with Amazon links - check if ASINs exist.
"""

import asyncio
import httpx

async def check_amazon_product(asin, marketplace="ca"):
    """Check if an ASIN exists on Amazon."""
    urls = {
        "ca": f"https://www.amazon.ca/dp/{asin}",
        "com": f"https://www.amazon.com/dp/{asin}"
    }
    
    print(f"\nChecking ASIN: {asin}")
    
    for market, url in urls.items():
        if market != marketplace and marketplace != "both":
            continue
            
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                # Add headers to appear more like a browser
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    # Check if it's actually a product page
                    content = response.text[:5000]  # Check first 5000 chars
                    
                    if "Currently unavailable" in content:
                        print(f"  {market.upper()}: Product exists but unavailable")
                    elif "productTitle" in content or "product-title" in content:
                        print(f"  {market.upper()}: Product found!")
                        
                        # Try to extract title
                        if "<title>" in content:
                            start = content.find("<title>") + 7
                            end = content.find("</title>", start)
                            if end > start:
                                title = content[start:end][:50]
                                print(f"    Title snippet: {title}...")
                    else:
                        print(f"  {market.upper()}: Page loaded but might not be a product")
                        
                elif response.status_code == 404:
                    print(f"  {market.upper()}: ASIN not found (404)")
                else:
                    print(f"  {market.upper()}: Status {response.status_code}")
                    
        except Exception as e:
            print(f"  {market.upper()}: Error - {e}")

async def main():
    """Test our sample ASINs."""
    print("Testing Amazon ASINs from sample data")
    print("=" * 40)
    
    # ASINs from our sample deals
    test_asins = [
        "B08N5WRWNW",  # Echo Dot (5th Gen)
        "B0B7BP6CJN",  # AirPods Pro 2nd Gen
        "B09B8RRQX1",  # Resistance Bands
        "B098WDG2ZT",  # LEGO Creator
        "B07HGJKTSZ",  # 7 Habits book
        "B07QR73T66",  # Under Armour shirt
        "B08C1W5N87",  # CeraVe cleanser
        "B09JQMJSXY",  # Instant Vortex
    ]
    
    print("\nChecking on Amazon.ca (Canadian marketplace):")
    for asin in test_asins:
        await check_amazon_product(asin, "ca")
        await asyncio.sleep(2)  # Be nice to Amazon
    
    print("\n" + "=" * 40)
    print("If most ASINs are not found on .ca:")
    print("  These might be US-only ASINs")
    print("  Need to scrape actual Canadian deals")
    print("  Or use Canadian-specific ASINs")

if __name__ == "__main__":
    asyncio.run(main())