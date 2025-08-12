#!/usr/bin/env python3
"""
Test affiliate link behavior to understand redirect issues.
"""

import asyncio
import httpx
from urllib.parse import urlparse, parse_qs

async def test_affiliate_link(url, description=""):
    """Test an affiliate link to see where it redirects."""
    print(f"\nTesting: {description}")
    print(f"URL: {url}")
    
    try:
        async with httpx.AsyncClient(follow_redirects=False, timeout=10) as client:
            response = await client.get(url)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('location', 'No location header')
                print(f"Redirects to: {redirect_url}")
                
                # Parse the redirect URL to understand it
                parsed = urlparse(redirect_url)
                if 'amazon' in parsed.netloc:
                    print("SUCCESS: Redirects to Amazon (good)")
                    
                    # Check if it preserves our tag
                    query_params = parse_qs(parsed.query)
                    if 'tag' in query_params:
                        tag = query_params['tag'][0]
                        if tag == 'savingsgurucc-20':
                            print("SUCCESS: Preserves our affiliate tag")
                        else:
                            print(f"WARNING: Changes tag to: {tag}")
                    else:
                        print("ERROR: Affiliate tag missing in redirect")
                else:
                    print("ERROR: Redirects away from Amazon")
                    
            elif response.status_code == 200:
                print("SUCCESS: Direct load (no redirect)")
            else:
                print(f"ERROR: Unexpected status: {response.status_code}")
                
    except Exception as e:
        print(f"ERROR testing link: {e}")

async def main():
    """Test all affiliate links from our deals."""
    print("Affiliate Link Redirect Test")
    print("=" * 40)
    
    # Test the specific AirPods link that's causing issues
    test_links = [
        ("https://www.amazon.ca/dp/B0B7BP6CJN?tag=savingsgurucc-20", "AirPods Pro (the problem one)"),
        ("https://www.amazon.ca/dp/B08N5WRWNW?tag=savingsgurucc-20", "Echo Dot"),
        ("https://www.amazon.ca/dp/B09B8RRQX1?tag=savingsgurucc-20", "Resistance Bands"),
        # Test without our tag to see baseline behavior
        ("https://www.amazon.ca/dp/B0B7BP6CJN", "AirPods (no tag)"),
    ]
    
    for url, description in test_links:
        await test_affiliate_link(url, description)
        await asyncio.sleep(1)  # Be nice to Amazon's servers
    
    print("\n" + "=" * 40)
    print("INFO: If links redirect to wrong products:")
    print("   1. Product might be out of stock")
    print("   2. Amazon might show 'similar' products")
    print("   3. Regional availability issues")
    print("   4. Temporary Amazon catalog updates")
    
    print("\nINFO: If affiliate tags are missing:")
    print("   1. Associates account needs approval")
    print("   2. Tag might be suspended")
    print("   3. Check Amazon Associates dashboard")

if __name__ == "__main__":
    asyncio.run(main())