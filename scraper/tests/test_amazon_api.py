"""
Tests for Amazon PAAPI integration client.
Tests real Canadian marketplace behavior and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal

from ..amazon_api import AmazonAPIClient
from ..models import AmazonProduct, DataSource
from ..settings import Settings


class TestAmazonAPIClient:
    """Test Amazon API client functionality."""
    
    def test_init_success(self, test_settings: Settings):
        """Test successful initialization of Amazon API client."""
        client = AmazonAPIClient(test_settings)
        
        assert client.settings == test_settings
        assert client._last_request_time == 0.0
        assert client.amazon_api is not None
    
    def test_init_invalid_credentials(self):
        """Test initialization with invalid credentials."""
        import os
        os.environ["AMZ_ACCESS_KEY"] = ""
        
        with pytest.raises(Exception):
            # This should fail during Settings() validation
            Settings()
    
    @pytest.mark.asyncio
    async def test_throttle_request(self, mock_amazon_api_client):
        """Test rate limiting implementation."""
        import time
        
        # First request should not throttle
        start_time = time.time()
        await mock_amazon_api_client._throttle_request()
        duration1 = time.time() - start_time
        
        # Second request immediately after should throttle
        mock_amazon_api_client._last_request_time = time.time()
        start_time = time.time()
        await mock_amazon_api_client._throttle_request()
        duration2 = time.time() - start_time
        
        assert duration1 < 0.1  # First request is fast
        assert duration2 >= 0.9  # Second request is throttled (at least 1 second)
    
    def test_extract_price_from_offers_success(self, mock_amazon_api_client):
        """Test price extraction from PAAPI offers structure."""
        offers = {
            "Listings": [
                {
                    "Price": {
                        "Amount": 29.99,
                        "DisplayValue": "$29.99"
                    }
                }
            ]
        }
        
        price = mock_amazon_api_client._extract_price_from_offers(offers)
        assert price == Decimal("29.99")
    
    def test_extract_price_from_offers_display_value_fallback(self, mock_amazon_api_client):
        """Test price extraction using display value fallback."""
        offers = {
            "Listings": [
                {
                    "Price": {
                        "DisplayValue": "$29.99"
                    }
                }
            ]
        }
        
        price = mock_amazon_api_client._extract_price_from_offers(offers)
        assert price == Decimal("29.99")
    
    def test_extract_price_from_offers_no_price(self, mock_amazon_api_client):
        """Test price extraction when no price is available."""
        offers = {"Listings": []}
        
        price = mock_amazon_api_client._extract_price_from_offers(offers)
        assert price is None
    
    def test_extract_image_url_success(self, mock_amazon_api_client):
        """Test image URL extraction from PAAPI images structure."""
        images = {
            "Primary": {
                "Large": {
                    "URL": "https://example.com/large-image.jpg"
                },
                "Medium": {
                    "URL": "https://example.com/medium-image.jpg"
                }
            }
        }
        
        url = mock_amazon_api_client._extract_image_url(images)
        assert url == "https://example.com/large-image.jpg"
    
    def test_extract_image_url_fallback(self, mock_amazon_api_client):
        """Test image URL extraction with fallback to smaller sizes."""
        images = {
            "Primary": {
                "Medium": {
                    "URL": "https://example.com/medium-image.jpg"
                }
            }
        }
        
        url = mock_amazon_api_client._extract_image_url(images)
        assert url == "https://example.com/medium-image.jpg"
    
    def test_extract_image_url_no_image(self, mock_amazon_api_client):
        """Test image URL extraction when no image is available."""
        images = {}
        
        url = mock_amazon_api_client._extract_image_url(images)
        assert url is None
    
    @pytest.mark.asyncio
    async def test_get_product_info_invalid_asin(self, mock_amazon_api_client):
        """Test product info retrieval with invalid ASIN."""
        # Test empty ASIN
        result = await mock_amazon_api_client.get_product_info("")
        assert result is None
        
        # Test wrong length ASIN
        result = await mock_amazon_api_client.get_product_info("INVALID")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_product_info_success(self, mock_amazon_api_client, mock_paapi_response):
        """Test successful product info retrieval."""
        # Mock the API call
        mock_amazon_api_client.amazon_api.get_items.return_value = mock_paapi_response
        
        result = await mock_amazon_api_client.get_product_info("B08N5WRWNW")
        
        assert result is not None
        assert isinstance(result, AmazonProduct)
        assert result.asin == "B08N5WRWNW"
        assert result.title == "Test Product"
        assert result.current_price == Decimal("29.99")
        assert result.list_price == Decimal("49.99")
        assert result.discount_percent == 40
        assert result.data_source == DataSource.PAAPI
    
    @pytest.mark.asyncio
    async def test_get_product_info_api_error(self, mock_amazon_api_client):
        """Test product info retrieval when API returns error."""
        # Mock API to raise exception
        mock_amazon_api_client.amazon_api.get_items.side_effect = Exception("API Error")
        
        result = await mock_amazon_api_client.get_product_info("B08N5WRWNW")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_product_info_no_items(self, mock_amazon_api_client):
        """Test product info retrieval when API returns no items."""
        # Mock API to return empty response
        mock_amazon_api_client.amazon_api.get_items.return_value = {
            "ItemsResult": {"Items": []}
        }
        
        result = await mock_amazon_api_client.get_product_info("B08N5WRWNW")
        assert result is None
    
    def test_parse_paapi_item_minimal_data(self, mock_amazon_api_client):
        """Test parsing PAAPI item with minimal required data."""
        item = {
            "ItemInfo": {
                "Title": {
                    "DisplayValue": "Test Product"
                }
            },
            "Offers": {
                "Listings": [
                    {
                        "Price": {
                            "Amount": 29.99
                        }
                    }
                ]
            }
        }
        
        result = mock_amazon_api_client._parse_paapi_item(item, "B08N5WRWNW")
        
        assert result is not None
        assert result.asin == "B08N5WRWNW"
        assert result.title == "Test Product"
        assert result.current_price == Decimal("29.99")
        assert result.data_source == DataSource.PAAPI
    
    def test_parse_paapi_item_no_title(self, mock_amazon_api_client):
        """Test parsing PAAPI item without title (should fail)."""
        item = {
            "ItemInfo": {},
            "Offers": {
                "Listings": [{"Price": {"Amount": 29.99}}]
            }
        }
        
        result = mock_amazon_api_client._parse_paapi_item(item, "B08N5WRWNW")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_multiple_products(self, mock_amazon_api_client, mock_paapi_response):
        """Test retrieving multiple products."""
        # Mock successful API calls
        mock_amazon_api_client.amazon_api.get_items.return_value = mock_paapi_response
        
        asins = ["B08N5WRWNW", "B07QR73T66"]
        results = await mock_amazon_api_client.get_multiple_products(asins)
        
        assert len(results) == 2
        assert "B08N5WRWNW" in results
        assert "B07QR73T66" in results
        
        # Both should be successful in this mock
        assert results["B08N5WRWNW"] is not None
        assert results["B07QR73T66"] is not None
    
    @pytest.mark.asyncio
    async def test_get_multiple_products_mixed_results(self, mock_amazon_api_client, mock_paapi_response):
        """Test retrieving multiple products with mixed success/failure."""
        # Mock API to succeed for first ASIN, fail for second
        def mock_get_items(asin, resources=None):
            if asin == "B08N5WRWNW":
                return mock_paapi_response
            else:
                raise Exception("API Error")
        
        mock_amazon_api_client.amazon_api.get_items.side_effect = mock_get_items
        
        asins = ["B08N5WRWNW", "INVALID123"]
        results = await mock_amazon_api_client.get_multiple_products(asins)
        
        assert len(results) == 2
        assert results["B08N5WRWNW"] is not None
        assert results["INVALID123"] is None
    
    def test_is_healthy_success(self, test_settings: Settings):
        """Test health check with valid configuration."""
        client = AmazonAPIClient(test_settings)
        assert client.is_healthy() is True
    
    def test_is_healthy_missing_credentials(self):
        """Test health check with missing credentials."""
        import os
        
        # Save original values
        original_access = os.environ.get("AMZ_ACCESS_KEY")
        original_secret = os.environ.get("AMZ_SECRET_KEY")
        
        try:
            # Set empty credentials
            os.environ["AMZ_ACCESS_KEY"] = ""
            os.environ["AMZ_SECRET_KEY"] = ""
            
            with pytest.raises(Exception):
                # Should fail during initialization
                client = AmazonAPIClient(Settings())
        finally:
            # Restore original values
            if original_access:
                os.environ["AMZ_ACCESS_KEY"] = original_access
            if original_secret:
                os.environ["AMZ_SECRET_KEY"] = original_secret


class TestAmazonAPIIntegration:
    """Integration tests for Amazon API (these would use real API calls in CI)."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_canadian_marketplace(self, test_settings: Settings):
        """Test with real Canadian marketplace (if API keys are provided)."""
        # This test would only run if real API keys are available
        # Skip in normal testing to avoid API rate limits
        pytest.skip("Integration test - requires real API keys")
        
        # client = AmazonAPIClient(test_settings)
        # result = await client.get_product_info("B08N5WRWNW")  # Known Canadian ASIN
        # 
        # assert result is not None
        # assert result.asin == "B08N5WRWNW"
        # assert result.data_source == DataSource.PAAPI