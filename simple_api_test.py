#!/usr/bin/env python3
"""
Simple test to verify Amazon PAAPI library usage.
"""

import os
import sys
from amazon_paapi import AmazonApi
from dotenv import load_dotenv

load_dotenv()

def test_simple():
    """Simple test of the library."""
    print("Simple Amazon PAAPI Test")
    print("=" * 30)
    
    try:
        # Get credentials
        access_key = os.getenv('AMZ_ACCESS_KEY')
        secret_key = os.getenv('AMZ_SECRET_KEY')
        partner_tag = os.getenv('AMZ_PARTNER_TAG')
        
        print(f"Access Key: {access_key[:8]}...{access_key[-4:]}")
        print(f"Partner Tag: {partner_tag}")
        print()
        
        # Initialize API with correct parameters
        amazon_api = AmazonApi(
            key=access_key,
            secret=secret_key,
            tag=partner_tag,
            country="CA"
        )
        
        # Simple search test instead of get_items
        print("Testing search_items instead...")
        result = amazon_api.search_items(
            keywords="echo dot",
            search_index="All"
        )
        
        print(f"Search result type: {type(result)}")
        if result:
            print("Search successful!")
            if hasattr(result, 'search_result'):
                items = getattr(result.search_result, 'items', [])
                print(f"Found {len(items)} items")
                if items:
                    item = items[0]
                    print(f"First item ASIN: {getattr(item, 'asin', 'N/A')}")
            else:
                print("No search_result attribute")
        else:
            print("Search returned None")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)