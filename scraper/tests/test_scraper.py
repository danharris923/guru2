"""
Tests for web scraping fallback and main scraper functionality.
Tests anti-bot measures and no fake data generation.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal

from ..scraper_fallback import AmazonScrapingClient
from ..focused_scraper import FocusedScraper
from ..models import AmazonProduct, Deal, DataSource


class TestAmazonScrapingClient:
    """Test Amazon scraping client functionality."""
    
    def test_init_success(self, test_settings):
        """Test successful initialization of scraping client."""
        client = AmazonScrapingClient(test_settings)
        
        assert client.settings == test_settings
        assert client.client is not None
        assert "Mozilla/5.0" in client.base_headers["User-Agent"]
        assert "Chrome" in client.base_headers["User-Agent"]
    
    @pytest.mark.asyncio
    async def test_add_random_delay(self, mock_scraping_client):
        """Test random delay implementation."""
        import time
        
        start_time = time.time()
        await mock_scraping_client._add_random_delay()
        duration = time.time() - start_time
        
        # Should delay between min and max settings
        assert duration >= mock_scraping_client.settings.scraper_delay_min
        assert duration <= mock_scraping_client.settings.scraper_delay_max + 0.1  # Small buffer for execution time
    
    def test_get_randomized_headers(self, mock_scraping_client):
        """Test header randomization for bot detection avoidance."""
        headers1 = mock_scraping_client._get_randomized_headers()
        headers2 = mock_scraping_client._get_randomized_headers()
        
        # Headers should contain required fields
        assert "User-Agent" in headers1
        assert "Accept-Language" in headers1
        assert "Mozilla/5.0" in headers1["User-Agent"]
        
        # Headers might be different due to randomization
        # (This is probabilistic, so we just check they're valid)
        assert isinstance(headers1["User-Agent"], str)
        assert isinstance(headers2["Accept-Language"], str)
    
    def test_extract_price_from_text_success(self, mock_scraping_client):
        """Test price extraction from various text formats."""
        test_cases = [
            ("CDN$ 29.99", Decimal("29.99")),
            ("$29.99", Decimal("29.99")),
            ("29.99", Decimal("29.99")),
            ("CDN$ 1,299.99", Decimal("1299.99")),
            ("$1,299.99", Decimal("1299.99")),
        ]
        
        for text, expected in test_cases:
            result = mock_scraping_client._extract_price_from_text(text)
            assert result == expected, f"Failed for text: {text}"
    
    def test_extract_price_from_text_invalid(self, mock_scraping_client):
        """Test price extraction with invalid text."""
        test_cases = ["", "No price here", "abc", None]
        
        for text in test_cases:
            result = mock_scraping_client._extract_price_from_text(text)
            assert result is None, f"Should return None for: {text}"
    
    def test_extract_title(self, mock_scraping_client, mock_beautifulsoup):
        """Test product title extraction from HTML."""
        title = mock_scraping_client._extract_title(mock_beautifulsoup)
        assert title == "Test Product"
    
    def test_extract_current_price(self, mock_scraping_client, mock_beautifulsoup):
        """Test current price extraction from HTML."""
        price = mock_scraping_client._extract_current_price(mock_beautifulsoup)
        assert price == Decimal("29.99")
    
    def test_extract_list_price(self, mock_scraping_client, mock_beautifulsoup):
        """Test list price extraction from HTML."""
        price = mock_scraping_client._extract_list_price(mock_beautifulsoup)
        assert price == Decimal("49.99")
    
    def test_extract_image_url(self, mock_scraping_client, mock_beautifulsoup):
        """Test image URL extraction from HTML."""
        url = mock_scraping_client._extract_image_url(mock_beautifulsoup)
        assert url == "https://example.com/image.jpg"
    
    def test_extract_availability(self, mock_scraping_client, mock_beautifulsoup):
        """Test availability extraction from HTML."""
        availability = mock_scraping_client._extract_availability(mock_beautifulsoup)
        assert "In Stock" in availability
    
    def test_extract_product_data_success(self, mock_scraping_client, mock_beautifulsoup):
        """Test complete product data extraction from HTML."""
        product = mock_scraping_client._extract_product_data(mock_beautifulsoup, "B08N5WRWNW")
        
        assert product is not None
        assert isinstance(product, AmazonProduct)
        assert product.asin == "B08N5WRWNW"
        assert product.title == "Test Product"
        assert product.current_price == Decimal("29.99")
        assert product.list_price == Decimal("49.99")
        assert product.discount_percent == 40
        assert product.data_source == DataSource.SCRAPED
    
    def test_extract_product_data_no_price(self, mock_scraping_client):
        """Test product data extraction when no price is found (should return None)."""
        from bs4 import BeautifulSoup
        
        html_no_price = """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1 id="productTitle">Test Product</h1>
                <!-- No price elements -->
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html_no_price, 'html.parser')
        product = mock_scraping_client._extract_product_data(soup, "B08N5WRWNW")
        
        # Should return None if no valid price found (CRITICAL: no fake data)
        assert product is None
    
    def test_is_valid_product_page_success(self, mock_scraping_client, mock_beautifulsoup):
        """Test valid product page detection."""
        is_valid = mock_scraping_client._is_valid_product_page(mock_beautifulsoup)
        assert is_valid is True
    
    def test_is_valid_product_page_blocked(self, mock_scraping_client):
        """Test blocked page detection."""
        from bs4 import BeautifulSoup
        
        blocked_html = """
        <html>
            <body>
                <h1>Robot Check</h1>
                <p>We can't connect to the server for this app or website at this time.</p>
                <p>Enter the characters you see below</p>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(blocked_html, 'html.parser')
        is_valid = mock_scraping_client._is_valid_product_page(soup)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_scrape_product_invalid_asin(self, mock_scraping_client):
        """Test scraping with invalid ASIN."""
        # Test empty ASIN
        result = await mock_scraping_client.scrape_product("")
        assert result is None
        
        # Test wrong length ASIN
        result = await mock_scraping_client.scrape_product("INVALID")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scrape_product_success(self, mock_scraping_client, sample_html_content):
        """Test successful product scraping."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = sample_html_content.encode()
        
        mock_scraping_client.client.get.return_value = mock_response
        
        result = await mock_scraping_client.scrape_product("B08N5WRWNW")
        
        assert result is not None
        assert isinstance(result, AmazonProduct)
        assert result.asin == "B08N5WRWNW"
        assert result.data_source == DataSource.SCRAPED
    
    @pytest.mark.asyncio
    async def test_scrape_product_503_retry(self, mock_scraping_client):
        """Test retry logic when getting 503 (rate limited)."""
        # Mock 503 response followed by success
        mock_responses = [
            MagicMock(status_code=503),  # First attempt
            MagicMock(status_code=503),  # Second attempt
            MagicMock(status_code=200, content=b"<html><h1 id='productTitle'>Test</h1></html>")  # Third attempt
        ]
        
        mock_scraping_client.client.get.side_effect = mock_responses
        
        result = await mock_scraping_client.scrape_product("B08N5WRWNW")
        
        # Should eventually succeed after retries
        assert mock_scraping_client.client.get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_scrape_product_max_retries(self, mock_scraping_client):
        """Test max retries exceeded."""
        # Mock all attempts returning 503
        mock_response = MagicMock(status_code=503)
        mock_scraping_client.client.get.return_value = mock_response
        
        result = await mock_scraping_client.scrape_product("B08N5WRWNW")
        
        # Should fail after max retries
        assert result is None
        assert mock_scraping_client.client.get.call_count == mock_scraping_client.settings.max_retry_attempts


class TestFocusedScraper:
    """Test main scraper functionality."""
    
    def test_init_success(self, test_settings):
        """Test successful initialization of main scraper."""
        scraper = FocusedScraper(test_settings)
        
        assert scraper.settings == test_settings
        assert scraper.amazon_api is not None
        assert scraper.session is not None
        assert scraper.stats["posts_scraped"] == 0
    
    def test_categorize_post(self, test_settings):
        """Test post categorization logic."""
        scraper = FocusedScraper(test_settings)
        
        test_cases = [
            ("Apple iPhone 13", "Electronics"),
            ("Kitchen Knife Set", "Home & Garden"),
            ("Nike Running Shoes", "Clothing"),
            ("Harry Potter Book", "Books"),
            ("LEGO Building Set", "Toys & Games"),
            ("Skincare Moisturizer", "Health & Beauty"),
            ("Yoga Mat", "Sports"),
            ("Random Deal", "General"),
        ]
        
        for title, expected_category in test_cases:
            category = scraper._categorize_post(title)
            assert category == expected_category, f"Failed for title: {title}"
    
    def test_extract_single_post_success(self, test_settings):
        """Test extraction of single SavingsGuru post."""
        from bs4 import BeautifulSoup
        
        post_html = """
        <article class="post">
            <h2><a href="/test-deal">Great Deal on Test Product</a></h2>
            <div class="content">
                <p>This is a great deal description.</p>
                <a href="https://amzn.to/test123">Check it out</a>
                <a href="https://amazon.ca/dp/B08N5WRWNW">Direct link</a>
            </div>
        </article>
        """
        
        soup = BeautifulSoup(post_html, 'html.parser')
        post_element = soup.find('article')
        
        scraper = FocusedScraper(test_settings)
        post = scraper._extract_single_post(post_element, "https://savingsguru.ca")
        
        assert post is not None
        assert post.post_title == "Great Deal on Test Product"
        assert len(post.extracted_asins) > 0
        assert "B08N5WRWNW" in post.extracted_asins
    
    def test_extract_single_post_no_asins(self, test_settings):
        """Test post extraction when no ASINs are found."""
        from bs4 import BeautifulSoup
        
        post_html = """
        <article class="post">
            <h2>Deal without Amazon links</h2>
            <div class="content">
                <p>This deal has no Amazon links.</p>
            </div>
        </article>
        """
        
        soup = BeautifulSoup(post_html, 'html.parser')
        post_element = soup.find('article')
        
        scraper = FocusedScraper(test_settings)
        post = scraper._extract_single_post(post_element, "https://savingsguru.ca")
        
        # Should return None if no ASINs found
        assert post is None
    
    def test_create_deals_from_products_success(self, test_settings, mock_amazon_product, mock_savingsguru_post):
        """Test deal creation from real product data."""
        scraper = FocusedScraper(test_settings)
        
        products = {"B08N5WRWNW": mock_amazon_product}
        posts = [mock_savingsguru_post]
        
        deals = scraper.create_deals_from_products(products, posts)
        
        assert len(deals) == 1
        assert isinstance(deals[0], Deal)
        assert deals[0].asin == "B08N5WRWNW"
        assert deals[0].data_source == "PAAPI"
        assert deals[0].price > 0  # CRITICAL: Real price only
    
    def test_create_deals_from_products_no_real_data(self, test_settings, mock_savingsguru_post):
        """Test deal creation when no real product data is available."""
        scraper = FocusedScraper(test_settings)
        
        # No products available (None values)
        products = {"B08N5WRWNW": None}
        posts = [mock_savingsguru_post]
        
        deals = scraper.create_deals_from_products(products, posts)
        
        # CRITICAL: Should create no deals if no real data (never fake data)
        assert len(deals) == 0
    
    def test_sort_deals_by_discount(self, test_settings):
        """Test deals sorting by discount percentage."""
        scraper = FocusedScraper(test_settings)
        
        # Create mock deals with different discounts
        deals = [
            Deal(
                id="deal1", title="Deal 1", imageUrl="http://example.com/1.jpg",
                price=20.0, originalPrice=40.0, discountPercent=50,
                category="Electronics", description="Test", affiliateUrl="http://example.com",
                featured=False, dateAdded="2024-01-01T00:00:00Z", dataSource="PAAPI", asin="ASIN001"
            ),
            Deal(
                id="deal2", title="Deal 2", imageUrl="http://example.com/2.jpg",
                price=30.0, originalPrice=50.0, discountPercent=40,
                category="Electronics", description="Test", affiliateUrl="http://example.com",
                featured=False, dateAdded="2024-01-01T00:00:00Z", dataSource="PAAPI", asin="ASIN002"
            ),
            Deal(
                id="deal3", title="Deal 3", imageUrl="http://example.com/3.jpg",
                price=10.0, originalPrice=20.0, discountPercent=50,
                category="Electronics", description="Test", affiliateUrl="http://example.com",
                featured=False, dateAdded="2024-01-01T00:00:00Z", dataSource="PAAPI", asin="ASIN003"
            ),
        ]
        
        sorted_deals = scraper._sort_deals_by_discount(deals)
        
        # Should be sorted by discount percentage (highest first)
        assert sorted_deals[0].discountPercent == 50
        assert sorted_deals[1].discountPercent == 50  # Same discount
        assert sorted_deals[2].discountPercent == 40
    
    def test_mark_featured_deals(self, test_settings):
        """Test marking of featured deals."""
        scraper = FocusedScraper(test_settings)
        
        # Create deals with various discount levels
        deals = []
        for i in range(25):
            discount = 60 - (i * 2)  # 60%, 58%, 56%, ..., 10%
            deal = Deal(
                id=f"deal{i}", title=f"Deal {i}", imageUrl="http://example.com/img.jpg",
                price=float(40 - discount/2), originalPrice=40.0, discountPercent=discount,
                category="Electronics", description="Test", affiliateUrl="http://example.com",
                featured=False, dateAdded="2024-01-01T00:00:00Z", dataSource="PAAPI", asin=f"ASIN{i:03d}"
            )
            deals.append(deal)
        
        marked_deals = scraper._mark_featured_deals(deals, featured_threshold=40)
        
        # Count featured deals
        featured_count = sum(1 for deal in marked_deals if deal.featured)
        
        # Should mark up to 20 deals with 40%+ discount as featured
        assert featured_count <= 20
        
        # All featured deals should have discount >= 40%
        for deal in marked_deals:
            if deal.featured:
                assert deal.discountPercent >= 40


class TestNoFakeDataGeneration:
    """Critical tests to ensure no fake data is ever generated."""
    
    def test_no_fake_data_in_amazon_product_creation(self, test_settings):
        """Test that AmazonProduct creation fails with invalid data."""
        # Try to create product without required fields
        with pytest.raises(Exception):  # Pydantic validation should fail
            AmazonProduct(
                asin="B08N5WRWNW",
                title="",  # Empty title should fail
                current_price=0,  # Zero price should fail validation
            )
    
    def test_no_fake_data_in_deal_creation(self, test_settings, mock_amazon_product):
        """Test that Deal creation returns None for invalid product data."""
        # Create product with no price (should not create deal)
        invalid_product = AmazonProduct(
            asin="B08N5WRWNW",
            title="Test Product",
            current_price=None,  # No price
            data_source=DataSource.PAAPI
        )
        
        deal = Deal.from_amazon_product(invalid_product, "test-tag-20")
        
        # CRITICAL: Should return None, never fake data
        assert deal is None
    
    @pytest.mark.asyncio
    async def test_scraper_skips_products_without_real_data(self, test_settings):
        """Test that scraper skips products when real data is unavailable."""
        scraper = FocusedScraper(test_settings)
        
        # Mock API and scraping to both fail
        scraper.amazon_api.get_product_info = AsyncMock(return_value=None)
        
        with patch.object(scraper, '_try_web_scraping') as mock_scraping:
            mock_scraping.return_value = None
            
            # Try to get product data
            results = await scraper.get_real_product_data(["B08N5WRWNW"])
            
            # Should return None, never fake data
            assert results["B08N5WRWNW"] is None
            
            # Stats should reflect the skip
            assert scraper.stats['products_skipped'] == 1
            assert scraper.stats['paapi_success'] == 0
            assert scraper.stats['scraping_success'] == 0