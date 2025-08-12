"""
Pytest configuration and shared fixtures for SavingsGuru scraper tests.
"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Generator, AsyncGenerator

from ..settings import Settings
from ..models import AmazonProduct, Deal, DataSource, SavingsGuruPost


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with dummy values."""
    import os
    
    # Set test environment variables
    os.environ["AMZ_ACCESS_KEY"] = "test_access_key"
    os.environ["AMZ_SECRET_KEY"] = "test_secret_key"
    os.environ["AMZ_PARTNER_TAG"] = "test-tag-20"
    os.environ["APP_ENV"] = "testing"
    
    return Settings()


@pytest.fixture
def mock_amazon_product() -> AmazonProduct:
    """Create a mock AmazonProduct for testing."""
    return AmazonProduct(
        asin="B08N5WRWNW",
        title="Test Product",
        current_price=29.99,
        list_price=49.99,
        discount_percent=40,
        image_url="https://example.com/image.jpg",
        availability="In Stock",
        prime_eligible=True,
        brand="TestBrand",
        features=["Feature 1", "Feature 2"],
        data_source=DataSource.PAAPI
    )


@pytest.fixture
def mock_deal(mock_amazon_product: AmazonProduct) -> Deal:
    """Create a mock Deal for testing."""
    return Deal.from_amazon_product(
        amazon_product=mock_amazon_product,
        partner_tag="test-tag-20"
    )


@pytest.fixture
def mock_savingsguru_post() -> SavingsGuruPost:
    """Create a mock SavingsGuruPost for testing."""
    return SavingsGuruPost(
        post_id="test_post_123",
        post_title="Great Deal on Test Product",
        post_url="https://savingsguru.ca/test-post",
        amazon_short_links=["https://amzn.to/test123"],
        extracted_asins=["B08N5WRWNW"],
        category="Electronics",
        description="This is a test deal description"
    )


@pytest.fixture
def mock_http_response():
    """Create a mock HTTP response for testing."""
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.json.return_value = {"test": "data"}
    response_mock.text = "Mock response text"
    response_mock.content = b"Mock response content"
    return response_mock


@pytest.fixture
def mock_paapi_response():
    """Create a mock Amazon PAAPI response for testing."""
    return {
        "ItemsResult": {
            "Items": [
                {
                    "ASIN": "B08N5WRWNW",
                    "ItemInfo": {
                        "Title": {
                            "DisplayValue": "Test Product"
                        },
                        "Features": {
                            "DisplayValues": ["Feature 1", "Feature 2"]
                        },
                        "ByLineInfo": {
                            "Brand": {
                                "DisplayValue": "TestBrand"
                            }
                        }
                    },
                    "Offers": {
                        "Listings": [
                            {
                                "Price": {
                                    "DisplayValue": "$29.99",
                                    "Amount": 29.99
                                },
                                "SavingBasis": {
                                    "DisplayValue": "$49.99",
                                    "Amount": 49.99
                                }
                            }
                        ]
                    },
                    "Images": {
                        "Primary": {
                            "Large": {
                                "URL": "https://example.com/image.jpg"
                            }
                        }
                    }
                }
            ]
        }
    }


@pytest.fixture
async def mock_amazon_api_client(test_settings: Settings):
    """Create a mock Amazon API client for testing."""
    from ..amazon_api import AmazonAPIClient
    
    # Create client but mock the actual API
    client = AmazonAPIClient(test_settings)
    client.amazon_api = MagicMock()
    
    return client


@pytest.fixture
async def mock_scraping_client(test_settings: Settings):
    """Create a mock scraping client for testing."""
    from ..scraper_fallback import AmazonScrapingClient
    
    client = AmazonScrapingClient(test_settings)
    client.client = AsyncMock()
    
    return client


@pytest.fixture
def sample_html_content() -> str:
    """Sample HTML content for testing scraping."""
    return """
    <html>
        <head><title>Test Product</title></head>
        <body>
            <h1 id="productTitle">Test Product</h1>
            <span class="a-price-current">
                <span class="a-offscreen">$29.99</span>
            </span>
            <span class="a-price-basis">
                <span class="a-offscreen">$49.99</span>
            </span>
            <img id="landingImage" src="https://example.com/image.jpg" alt="Test Product" />
            <div id="availability">
                <span class="a-color-success">In Stock</span>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_beautifulsoup(sample_html_content: str):
    """Create a BeautifulSoup object from sample HTML."""
    from bs4 import BeautifulSoup
    return BeautifulSoup(sample_html_content, 'html.parser')


class AsyncContextManagerMock:
    """Mock async context manager for testing."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, *args):
        pass


@pytest.fixture
def mock_async_context_manager():
    """Factory for creating async context manager mocks."""
    return AsyncContextManagerMock