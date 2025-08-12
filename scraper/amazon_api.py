"""
Amazon Product Advertising API (PAAPI) integration client.
Handles real product data retrieval with proper rate limiting and error handling.
"""

import asyncio
import time
import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal

from amazon_paapi import AmazonApi
from pydantic import ValidationError

from .settings import Settings
from .models import AmazonProduct, DataSource, ScrapingResult


logger = logging.getLogger(__name__)


class AmazonAPIClient:
    """
    Amazon Product Advertising API client with Canadian marketplace support.
    Implements rate limiting, error handling, and structured data extraction.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the Amazon API client with settings."""
        self.settings = settings
        self._last_request_time = 0.0
        
        # Initialize Amazon API for Canadian marketplace
        try:
            self.amazon_api = AmazonApi(
                key=settings.amz_access_key,
                secret=settings.amz_secret_key,
                tag=settings.amz_partner_tag,
                country=settings.amz_marketplace  # 'CA' for Canadian marketplace
            )
            logger.info(f"Amazon API client initialized for {settings.amz_marketplace} marketplace")
        except Exception as e:
            logger.error(f"Failed to initialize Amazon API client: {e}")
            raise
    
    async def _throttle_request(self) -> None:
        """
        Implement rate limiting to comply with PAAPI limits.
        CRITICAL: PAAPI free tier allows 1 request per second.
        """
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        
        if time_since_last_request < self.settings.api_rate_limit_delay:
            sleep_time = self.settings.api_rate_limit_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            await asyncio.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _extract_price_from_offers(self, offers: Dict[str, Any]) -> Optional[Decimal]:
        """
        Extract price from PAAPI offers structure.
        GOTCHA: PAAPI v5 has nested structure for price information.
        """
        try:
            listings = offers.get('Listings', [])
            if not listings:
                return None
            
            # Get the first listing (primary offer)
            listing = listings[0]
            price_info = listing.get('Price')
            
            if not price_info:
                return None
            
            # Try to get the display value and amount
            amount = price_info.get('Amount')
            if amount:
                return Decimal(str(amount))
            
            # Fallback to display value parsing
            display_value = price_info.get('DisplayValue', '')
            if display_value:
                # Remove currency symbols and parse
                price_str = display_value.replace('$', '').replace(',', '').strip()
                try:
                    return Decimal(price_str)
                except (ValueError, TypeError):
                    pass
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting price from offers: {e}")
            return None
    
    def _extract_image_url(self, images: Dict[str, Any]) -> Optional[str]:
        """Extract the highest quality image URL from PAAPI images structure."""
        try:
            primary = images.get('Primary')
            if not primary:
                return None
            
            # Try to get the largest image
            for size in ['Large', 'Medium', 'Small']:
                image_info = primary.get(size)
                if image_info and 'URL' in image_info:
                    return image_info['URL']
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting image URL: {e}")
            return None
    
    async def get_product_info(self, asin: str) -> Optional[AmazonProduct]:
        """
        Get product information for a single ASIN using PAAPI.
        
        Args:
            asin: Amazon Standard Identification Number
            
        Returns:
            AmazonProduct with real data or None if failed
        """
        if not asin or len(asin) != 10:
            logger.warning(f"Invalid ASIN format: {asin}")
            return None
        
        await self._throttle_request()
        
        try:
            from amazon_paapi.sdk.models.get_items_resource import GetItemsResource
            
            # Use the SDK's resource enums
            resources = [
                GetItemsResource.ITEM_INFO_TITLE,
                GetItemsResource.ITEM_INFO_FEATURES,
                GetItemsResource.OFFERS_LISTINGS_PRICE,
                GetItemsResource.OFFERS_SUMMARIES_HIGHEST_PRICE,
                GetItemsResource.IMAGES_PRIMARY_LARGE,
            ]
            
            logger.debug(f"Making PAAPI request for ASIN: {asin}")
            # Use the correct method signature
            response = self.amazon_api.get_items(item_ids=[asin], resources=resources)
            
            if not response or not hasattr(response, 'items_result'):
                logger.warning(f"No items_result in PAAPI response for {asin}")
                return None
            
            items = response.items_result.items if response.items_result else []
            if not items:
                logger.warning(f"No items found in PAAPI response for {asin}")
                return None
            
            item = items[0]
            return self._parse_paapi_item(item, asin)
            
        except Exception as e:
            logger.error(f"PAAPI request failed for {asin}: {e}")
            return None
    
    def _parse_paapi_item(self, item: Dict[str, Any], asin: str) -> Optional[AmazonProduct]:
        """Parse PAAPI item response into AmazonProduct model."""
        try:
            # Extract title
            title = ""
            item_info = item.get('ItemInfo', {})
            title_info = item_info.get('Title', {})
            if title_info:
                title = title_info.get('DisplayValue', '')
            
            if not title:
                logger.warning(f"No title found for ASIN {asin}")
                return None
            
            # Extract prices
            offers = item.get('Offers', {})
            current_price = self._extract_price_from_offers(offers)
            
            # Try to get list price from SavingBasis
            list_price = None
            listings = offers.get('Listings', [])
            if listings:
                listing = listings[0]
                saving_basis = listing.get('SavingBasis')
                if saving_basis and 'Amount' in saving_basis:
                    list_price = Decimal(str(saving_basis['Amount']))
            
            # If no list price, use current price as list price
            if not list_price and current_price:
                list_price = current_price
            
            # Calculate discount
            discount_percent = None
            if current_price and list_price and list_price > current_price:
                discount = float((list_price - current_price) / list_price * 100)
                discount_percent = round(discount)
            
            # Extract image
            images = item.get('Images', {})
            image_url = self._extract_image_url(images)
            
            # Extract features
            features = []
            features_info = item_info.get('Features', {})
            if features_info and 'DisplayValues' in features_info:
                features = features_info['DisplayValues'][:5]  # Limit to 5 features
            
            # Extract brand
            brand = None
            byline_info = item_info.get('ByLineInfo', {})
            if byline_info and 'Brand' in byline_info:
                brand_info = byline_info['Brand']
                if 'DisplayValue' in brand_info:
                    brand = brand_info['DisplayValue']
            
            # Create AmazonProduct
            product = AmazonProduct(
                asin=asin,
                title=title,
                current_price=current_price,
                list_price=list_price,
                discount_percent=discount_percent,
                image_url=image_url,
                brand=brand,
                features=features,
                availability="Available",  # PAAPI doesn't always provide this
                prime_eligible=False,  # Would need separate Prime check
                data_source=DataSource.PAAPI
            )
            
            logger.info(f"Successfully parsed PAAPI data for {asin}: {title} - ${current_price}")
            return product
            
        except ValidationError as e:
            logger.error(f"Validation error creating AmazonProduct for {asin}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing PAAPI item for {asin}: {e}")
            return None
    
    async def get_multiple_products(self, asins: List[str]) -> Dict[str, Optional[AmazonProduct]]:
        """
        Get product information for multiple ASINs.
        
        Args:
            asins: List of Amazon ASINs
            
        Returns:
            Dict mapping ASIN to AmazonProduct (or None if failed)
        """
        results = {}
        
        # PAAPI allows batch requests but we'll do individual requests
        # to better handle rate limiting and errors
        for asin in asins:
            if len(results) > 0:
                # Add extra delay between requests for safety
                await asyncio.sleep(0.5)
            
            product = await self.get_product_info(asin)
            results[asin] = product
            
            if product:
                logger.info(f"Successfully retrieved data for {asin}")
            else:
                logger.warning(f"Failed to retrieve data for {asin}")
        
        success_count = sum(1 for p in results.values() if p is not None)
        logger.info(f"Retrieved {success_count}/{len(asins)} products successfully")
        
        return results
    
    async def search_products(self, keywords: str, max_results: int = 10) -> List[AmazonProduct]:
        """
        Search for products by keywords (if needed for future features).
        
        Args:
            keywords: Search terms
            max_results: Maximum number of results to return
            
        Returns:
            List of AmazonProduct objects
        """
        # This would implement search functionality if needed
        # For now, we're focusing on getting products by ASIN from SavingsGuru
        logger.warning("Search functionality not implemented - focusing on ASIN-based retrieval")
        return []
    
    def is_healthy(self) -> bool:
        """Check if the API client is properly configured."""
        try:
            # Basic configuration check
            return (
                bool(self.settings.amz_access_key) and
                bool(self.settings.amz_secret_key) and
                bool(self.settings.amz_partner_tag) and
                self.amazon_api is not None
            )
        except Exception:
            return False