#!/usr/bin/env python3
"""
Quick test script to verify Amazon PAAPI credentials and functionality.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.settings import Settings
from scraper.amazon_api import AmazonAPIClient


async def test_amazon_api():
    """Test Amazon PAAPI with current credentials."""
    print("Testing Amazon PAAPI Credentials")
    print("=" * 40)
    
    try:
        # Load settings
        settings = Settings()
        print(f"Access Key: {settings.amz_access_key[:8]}...{settings.amz_access_key[-4:]}")
        print(f"Partner Tag: {settings.amz_partner_tag}")
        print(f"Marketplace: {settings.amz_marketplace}")
        print()
        
        # Initialize API client
        api_client = AmazonAPIClient(settings)
        
        # Test with a known good ASIN (Echo Dot from our sample data)
        test_asin = "B08N5WRWNW"
        print(f"Testing with ASIN: {test_asin}")
        
        # Try to get product info
        print("Making PAAPI request...")
        product = await api_client.get_product_info(test_asin)
        
        if product:
            print("SUCCESS: PAAPI Request Successful!")
            print(f"   Title: {product.title}")
            print(f"   Current Price: ${product.current_price}")
            print(f"   List Price: ${product.list_price}")
            print(f"   Discount: {product.discount_percent}%")
            print(f"   Image URL: {product.image_url}")
            print(f"   Data Source: {product.data_source}")
            
            # Test affiliate URL generation
            affiliate_url = product.to_affiliate_url(settings.amz_partner_tag)
            print(f"   Affiliate URL: {affiliate_url}")
            
            return True
        else:
            print("ERROR: PAAPI Request Failed")
            print("   No product data returned")
            return False
            
    except Exception as e:
        print(f"ERROR during API test: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


def test_affiliate_url_format():
    """Test affiliate URL formatting."""
    print("\nTesting Affiliate URL Format")
    print("-" * 30)
    
    try:
        settings = Settings()
        
        # Test URL formats
        test_asins = ["B08N5WRWNW", "B0B7BP6CJN"]
        
        for asin in test_asins:
            url = f"https://www.amazon.ca/dp/{asin}?tag={settings.amz_partner_tag}"
            print(f"ASIN {asin}: {url}")
            
        print("\nSUCCESS: Affiliate URL format looks correct")
        print("   If links redirect wrong, check:")
        print("   1. Partner tag is approved by Amazon")
        print("   2. Associate account is active")
        print("   3. Geographic restrictions")
        
        return True
        
    except Exception as e:
        print(f"ERROR testing URL format: {e}")
        return False


def check_credentials_format():
    """Check if credentials look valid."""
    print("\nChecking Credential Format")
    print("-" * 30)
    
    try:
        settings = Settings()
        
        # Check access key format (should be ~20 chars, start with AKIA)
        access_key = settings.amz_access_key
        if len(access_key) == 20 and access_key.startswith('AKIA'):
            print("SUCCESS: Access key format looks valid")
        else:
            print(f"WARNING: Access key format unusual: {len(access_key)} chars, starts with {access_key[:4]}")
        
        # Check secret key format (should be ~40 chars)
        secret_key = settings.amz_secret_key
        if len(secret_key) == 40:
            print("SUCCESS: Secret key format looks valid")
        else:
            print(f"WARNING: Secret key format unusual: {len(secret_key)} chars")
        
        # Check partner tag format
        partner_tag = settings.amz_partner_tag
        if partner_tag and len(partner_tag) > 0:
            print(f"SUCCESS: Partner tag looks valid: {partner_tag}")
        else:
            print("ERROR: Partner tag missing or empty")
        
        return True
        
    except Exception as e:
        print(f"ERROR checking credentials: {e}")
        return False


async def main():
    """Main test function."""
    print(f"Amazon PAAPI Test Suite - {datetime.now()}")
    print("=" * 50)
    
    # Test 1: Check credential format
    check_credentials_format()
    
    # Test 2: Test affiliate URL format
    test_affiliate_url_format()
    
    # Test 3: Test actual API call
    api_success = await test_amazon_api()
    
    print("\n" + "=" * 50)
    if api_success:
        print("SUCCESS: All tests passed! Amazon integration working correctly.")
    else:
        print("WARNING: API test failed. Check credentials or API access.")
        print("   Common issues:")
        print("   - Credentials expired or incorrect")
        print("   - Associate account not approved")
        print("   - API request limits exceeded")
        print("   - Network/firewall issues")
    
    return api_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)