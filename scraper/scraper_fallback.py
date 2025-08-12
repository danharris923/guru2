"""
Web scraping fallback for Amazon.ca product pages.
Used when PAAPI fails or rate limits are exceeded.
Implements anti-bot detection measures and robust error handling.
"""

import asyncio
import random
import re
import logging
from typing import Optional, Dict, List
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from pydantic import ValidationError

from .settings import Settings
from .models import AmazonProduct, DataSource, ScrapingResult


logger = logging.getLogger(__name__)


class AmazonScrapingClient:
    """
    Amazon.ca web scraping client with anti-bot measures.
    Implements proper headers, delays, and retry logic to avoid detection.
    """
    
    def __init__(self, settings: Settings):
        """Initialize the scraping client with anti-bot measures."""
        self.settings = settings
        
        # CRITICAL: Realistic browser headers to avoid bot detection
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Initialize HTTP client with session persistence
        self.client = httpx.AsyncClient(
            headers=self.base_headers,
            timeout=httpx.Timeout(self.settings.request_timeout),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
        )
        
        logger.info("Amazon scraping client initialized with anti-bot measures")
    
    async def _add_random_delay(self) -> None:
        """Add random delay between requests to avoid pattern detection."""
        delay = random.uniform(
            self.settings.scraper_delay_min,
            self.settings.scraper_delay_max
        )
        logger.debug(f"Adding random delay: {delay:.2f} seconds")
        await asyncio.sleep(delay)
    
    def _get_randomized_headers(self) -> Dict[str, str]:
        """Get headers with some randomization to avoid fingerprinting."""
        headers = self.base_headers.copy()
        
        # Rotate User-Agent occasionally
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers['User-Agent'] = random.choice(user_agents)
        
        # Add some variation to Accept-Language
        accept_languages = [
            'en-US,en;q=0.9',
            'en-US,en;q=0.9,fr;q=0.8',
            'en-CA,en;q=0.9,fr;q=0.8',
            'en-US,en;q=0.8'
        ]
        
        headers['Accept-Language'] = random.choice(accept_languages)
        
        return headers
    
    def _extract_price_from_text(self, text: str) -> Optional[Decimal]:
        """
        Extract price from text using regex patterns.
        Handles various Amazon.ca price formats.
        """
        if not text:
            return None
        
        # Common price patterns on Amazon.ca
        patterns = [
            r'CDN\$\s*([0-9,]+\.?[0-9]*)',  # CDN$ format
            r'\$([0-9,]+\.?[0-9]*)',        # $ format
            r'([0-9,]+\.?[0-9]*)',          # Plain number
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.replace(',', ''))
            if matches:
                try:
                    price_str = matches[0].replace(',', '')
                    return Decimal(price_str)
                except (ValueError, InvalidOperation):
                    continue
        
        return None
    
    def _extract_product_data(self, soup: BeautifulSoup, asin: str) -> Optional[AmazonProduct]:
        """
        Extract product data from Amazon.ca product page HTML.
        Uses multiple selectors for robustness across different page layouts.
        """
        try:
            # Extract title
            title = self._extract_title(soup)
            if not title:
                logger.warning(f"Could not extract title for ASIN {asin}")
                return None
            
            # Extract current price
            current_price = self._extract_current_price(soup)
            
            # Extract list/original price
            list_price = self._extract_list_price(soup)
            
            # If no current price found, try alternative selectors
            if not current_price:
                current_price = self._extract_price_alternative(soup)
            
            # Extract image URL
            image_url = self._extract_image_url(soup)
            
            # Extract availability
            availability = self._extract_availability(soup)
            
            # Calculate discount percentage
            discount_percent = None
            if current_price and list_price and list_price > current_price:
                discount = float((list_price - current_price) / list_price * 100)
                discount_percent = round(discount)
            
            # CRITICAL: Only return product if we have essential data
            if not current_price or current_price <= 0:
                logger.warning(f"No valid price found for ASIN {asin}")
                return None
            
            product = AmazonProduct(
                asin=asin,
                title=title,
                current_price=current_price,
                list_price=list_price,
                discount_percent=discount_percent,
                image_url=image_url,
                availability=availability,
                data_source=DataSource.SCRAPED
            )
            
            logger.info(f"Successfully scraped data for {asin}: {title} - ${current_price}")
            return product
            
        except Exception as e:
            logger.error(f"Error extracting product data for {asin}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product title using multiple selectors."""
        selectors = [
            '#productTitle',
            '.product-title',
            'h1.a-size-large',
            'h1[data-automation-id="product-title"]',
            '.pdp-product-name h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:  # Basic validation
                    return title[:200]  # Truncate long titles
        
        return None
    
    def _extract_current_price(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract current price using multiple selectors."""
        price_selectors = [
            '.a-price-current .a-offscreen',
            '.a-price .a-offscreen',
            '[data-asin-price]',
            '.a-price-whole',
            '#price_inside_buybox',
            '.a-section .a-price-current',
            '.kindle-price .a-color-price'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                price = self._extract_price_from_text(price_text)
                if price and price > 0:
                    return price
        
        return None
    
    def _extract_list_price(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Extract list/original price (crossed out price)."""
        list_price_selectors = [
            '.a-price-basis .a-offscreen',
            '.a-price-list .a-offscreen', 
            '.a-text-strike .a-offscreen',
            '[data-a-strike="true"]',
            '.a-price-was .a-offscreen'
        ]
        
        for selector in list_price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                price = self._extract_price_from_text(price_text)
                if price and price > 0:
                    return price
        
        return None
    
    def _extract_price_alternative(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """Alternative price extraction for different Amazon page layouts."""
        # Look for any element containing price-like text
        price_patterns = [
            r'CDN\$\s*[0-9,]+\.?[0-9]*',
            r'\$[0-9,]+\.?[0-9]*'
        ]
        
        for pattern in price_patterns:
            elements = soup.find_all(text=re.compile(pattern))
            for text in elements:
                price = self._extract_price_from_text(text)
                if price and price > 0:
                    return price
        
        return None
    
    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product image URL."""
        image_selectors = [
            '#landingImage',
            '.a-dynamic-image',
            '[data-old-hires]',
            '.pdp-product-image img',
            '#main-image'
        ]
        
        for selector in image_selectors:
            element = soup.select_one(selector)
            if element:
                # Try different attribute names for image URL
                for attr in ['data-old-hires', 'src', 'data-src', 'data-lazy-src']:
                    url = element.get(attr)
                    if url and url.startswith('http'):
                        return url
        
        return None
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability information."""
        availability_selectors = [
            '#availability .a-color-success',
            '#availability .a-color-price',
            '#availability span',
            '.a-stock'
        ]
        
        for selector in availability_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text:
                    return text[:100]  # Limit length
        
        return "Unknown"
    
    async def scrape_product(self, asin: str) -> Optional[AmazonProduct]:
        """
        Scrape product information from Amazon.ca product page.
        
        Args:
            asin: Amazon Standard Identification Number
            
        Returns:
            AmazonProduct with scraped data or None if failed
        """
        if not asin or len(asin) != 10:
            logger.warning(f"Invalid ASIN format: {asin}")
            return None
        
        url = f"https://www.amazon.ca/dp/{asin}"
        
        # Implement retry logic with exponential backoff
        for attempt in range(self.settings.max_retry_attempts):
            try:
                await self._add_random_delay()
                
                headers = self._get_randomized_headers()
                logger.debug(f"Scraping attempt {attempt + 1} for {asin}: {url}")
                
                response = await self.client.get(url, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Check if we got a valid product page (not blocked or captcha)
                    if self._is_valid_product_page(soup):
                        return self._extract_product_data(soup, asin)
                    else:
                        logger.warning(f"Got blocked or invalid page for {asin}")
                        
                elif response.status_code == 503:
                    # Service temporarily unavailable - likely rate limited
                    backoff_time = (2 ** attempt) + random.uniform(1, 3)
                    logger.warning(f"Got 503 for {asin}, backing off for {backoff_time:.2f}s")
                    await asyncio.sleep(backoff_time)
                    continue
                    
                elif response.status_code in [403, 429]:
                    # Forbidden or rate limited
                    backoff_time = (3 ** attempt) + random.uniform(2, 5)
                    logger.warning(f"Got {response.status_code} for {asin}, backing off for {backoff_time:.2f}s")
                    await asyncio.sleep(backoff_time)
                    continue
                    
                else:
                    logger.warning(f"Unexpected status code {response.status_code} for {asin}")
                    break
                    
            except httpx.TimeoutException:
                logger.warning(f"Timeout scraping {asin} (attempt {attempt + 1})")
                if attempt < self.settings.max_retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                    
            except Exception as e:
                logger.error(f"Error scraping {asin} (attempt {attempt + 1}): {e}")
                if attempt < self.settings.max_retry_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
        
        logger.error(f"Failed to scrape product data for {asin} after {self.settings.max_retry_attempts} attempts")
        return None
    
    def _is_valid_product_page(self, soup: BeautifulSoup) -> bool:
        """Check if the scraped page is a valid product page (not blocked/captcha)."""
        # Check for common blocking indicators
        blocking_indicators = [
            'captcha',
            'robot',
            'automation',
            'blocked',
            'access denied',
            'enter the characters you see below'
        ]
        
        page_text = soup.get_text().lower()
        
        for indicator in blocking_indicators:
            if indicator in page_text:
                return False
        
        # Check for product-specific elements
        product_indicators = [
            '#productTitle',
            '.a-price',
            '#availability'
        ]
        
        for selector in product_indicators:
            if soup.select_one(selector):
                return True
        
        return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()