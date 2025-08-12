"""
Main scraper that integrates SavingsGuru.ca post scraping with real Amazon data.
NO FAKE DATA GENERATION - uses PAAPI → web scraping → skip product fallback chain.
"""

import asyncio
import re
import json
from typing import List, Optional, Dict, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from settings import Settings
from models import Deal, SavingsGuruPost, AmazonProduct, DataSource, ScrapingSession
from amazon_api import AmazonAPIClient
from scraper_fallback import AmazonScrapingClient
from utils import (
    setup_logging, extract_asin_from_url, save_json_file, 
    generate_session_id, measure_execution_time
)
from deal_manager import DealManager


class FocusedScraper:
    """
    Main scraper that combines SavingsGuru.ca posts with real Amazon product data.
    CRITICAL: Never generates fake data - uses real API/scraping or skips product.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the scraper with settings and clients."""
        self.settings = settings or Settings()
        
        # Set up logging
        setup_logging(self.settings.log_level)
        
        # Initialize clients
        self.amazon_api = AmazonAPIClient(self.settings)
        self.scraper_client = None  # Will be created in async context
        self.deal_manager = DealManager(self.settings)
        
        # Session tracking
        self.session = ScrapingSession(session_id=generate_session_id())
        
        # Statistics
        self.stats = {
            'posts_scraped': 0,
            'asins_found': 0,
            'paapi_success': 0,
            'scraping_success': 0,
            'products_skipped': 0,
            'deals_created': 0
        }
        
        logger.info("FocusedScraper initialized with real data sources only")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.scraper_client = AmazonScrapingClient(self.settings)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.scraper_client:
            await self.scraper_client.close()
    
    @measure_execution_time("SavingsGuru post scraping")
    async def scrape_savingsguru_posts(self, max_pages: int = 5) -> List[SavingsGuruPost]:
        """
        Scrape SavingsGuru.ca for deal posts and extract Amazon links.
        PRESERVES existing SavingsGuru.ca scraping logic for ASIN extraction.
        """
        posts = []
        base_url = "https://www.savingsguru.ca"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for page in range(1, max_pages + 1):
                try:
                    url = f"{base_url}/page/{page}" if page > 1 else base_url
                    
                    logger.info(f"Scraping SavingsGuru page {page}: {url}")
                    response = await client.get(url)
                    
                    if response.status_code != 200:
                        logger.warning(f"Failed to fetch page {page}: {response.status_code}")
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_posts = self._extract_posts_from_page(soup, base_url)
                    
                    posts.extend(page_posts)
                    self.stats['posts_scraped'] += len(page_posts)
                    
                    logger.info(f"Found {len(page_posts)} posts on page {page}")
                    
                    # Add delay between page requests
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error scraping page {page}: {e}")
                    continue
        
        logger.info(f"Total posts scraped from SavingsGuru: {len(posts)}")
        return posts
    
    def _extract_posts_from_page(self, soup: BeautifulSoup, base_url: str) -> List[SavingsGuruPost]:
        """Extract deal posts from a SavingsGuru page."""
        posts = []
        
        # Look for post containers (adjust selectors based on actual site structure)
        post_selectors = [
            '.post',
            '.deal-post',
            'article',
            '.entry',
            '.deal-item'
        ]
        
        post_elements = []
        for selector in post_selectors:
            elements = soup.select(selector)
            if elements:
                post_elements = elements
                break
        
        for post_element in post_elements:
            try:
                post = self._extract_single_post(post_element, base_url)
                if post:
                    posts.append(post)
            except Exception as e:
                logger.warning(f"Error extracting post: {e}")
                continue
        
        return posts
    
    def _extract_single_post(self, post_element, base_url: str) -> Optional[SavingsGuruPost]:
        """Extract data from a single post element."""
        try:
            # Extract post title
            title_selectors = ['h1', 'h2', 'h3', '.title', '.post-title']
            title = ""
            for selector in title_selectors:
                title_elem = post_element.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Extract post URL
            link_elem = post_element.select_one('a[href]')
            post_url = ""
            if link_elem:
                href = link_elem.get('href')
                if href:
                    post_url = urljoin(base_url, href)
            
            # Find all Amazon links in the post
            amazon_links = []
            link_elements = post_element.select('a[href*="amzn.to"], a[href*="amazon.ca"], a[href*="amazon.com"]')
            
            for link in link_elements:
                href = link.get('href')
                if href and ('amzn.to' in href or 'amazon.ca' in href or 'amazon.com' in href):
                    amazon_links.append(href)
            
            # Extract ASINs from links
            extracted_asins = []
            for link in amazon_links:
                asin = extract_asin_from_url(link)
                if asin:
                    extracted_asins.append(asin)
            
            # Remove duplicates while preserving order
            extracted_asins = list(dict.fromkeys(extracted_asins))
            
            if not extracted_asins:
                logger.debug(f"No ASINs found in post: {title}")
                return None
            
            # Extract description/content
            content_selectors = ['.content', '.post-content', '.entry-content', 'p']
            description = ""
            for selector in content_selectors:
                content_elem = post_element.select_one(selector)
                if content_elem:
                    description = content_elem.get_text(strip=True)[:500]  # Limit length
                    break
            
            # Generate post ID
            post_id = f"sg_{hash(post_url)}_{datetime.utcnow().strftime('%Y%m%d')}"
            
            # Determine category from title (basic categorization)
            category = self._categorize_post(title)
            
            return SavingsGuruPost(
                post_id=post_id,
                post_title=title,
                post_url=post_url,
                amazon_short_links=amazon_links,
                extracted_asins=extracted_asins,
                category=category,
                description=description
            )
            
        except Exception as e:
            logger.error(f"Error extracting single post: {e}")
            return None
    
    def _categorize_post(self, title: str) -> str:
        """Basic categorization based on post title keywords."""
        title_lower = title.lower()
        
        categories = {
            'Electronics': ['electronics', 'tech', 'computer', 'laptop', 'phone', 'tablet', 'camera', 'tv'],
            'Home & Garden': ['home', 'kitchen', 'garden', 'furniture', 'decor', 'appliance'],
            'Clothing': ['clothing', 'fashion', 'shirt', 'dress', 'shoes', 'jacket'],
            'Books': ['book', 'novel', 'kindle', 'ebook', 'reading'],
            'Toys & Games': ['toy', 'game', 'kids', 'children', 'play'],
            'Health & Beauty': ['health', 'beauty', 'skincare', 'makeup', 'supplement'],
            'Sports': ['sport', 'fitness', 'gym', 'exercise', 'outdoor'],
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return "General"
    
    @measure_execution_time("Real product data retrieval")
    async def get_real_product_data(self, asins: List[str]) -> Dict[str, Optional[AmazonProduct]]:
        """
        Get real product data using PAAPI → web scraping → skip fallback chain.
        CRITICAL: Never generates fake data.
        """
        results = {}
        
        for asin in asins:
            self.session.total_products_attempted += 1
            self.stats['asins_found'] += 1
            
            logger.info(f"Processing ASIN: {asin}")
            
            # Step 1: Try PAAPI first
            product = await self._try_paapi(asin)
            
            if product:
                results[asin] = product
                self.session.total_products_successful += 1
                self.stats['paapi_success'] += 1
                logger.info(f"✓ PAAPI success for {asin}: {product.title}")
                continue
            
            # Step 2: Try web scraping fallback
            product = await self._try_web_scraping(asin)
            
            if product:
                results[asin] = product
                self.session.total_products_successful += 1
                self.stats['scraping_success'] += 1
                logger.info(f"✓ Scraping success for {asin}: {product.title}")
                continue
            
            # Step 3: Skip product (NO FAKE DATA)
            results[asin] = None
            self.stats['products_skipped'] += 1
            logger.warning(f"✗ Skipping {asin} - no real data available")
            self.session.add_error(f"No real data available for ASIN {asin}")
        
        return results
    
    async def _try_paapi(self, asin: str) -> Optional[AmazonProduct]:
        """Try to get product data using Amazon PAAPI."""
        try:
            logger.debug(f"Trying PAAPI for {asin}")
            self.session.total_api_calls += 1
            
            product = await self.amazon_api.get_product_info(asin)
            
            if product and product.current_price and product.current_price > 0:
                logger.debug(f"PAAPI returned valid product for {asin}")
                return product
            else:
                logger.debug(f"PAAPI returned invalid/incomplete data for {asin}")
                return None
                
        except Exception as e:
            logger.warning(f"PAAPI error for {asin}: {e}")
            return None
    
    async def _try_web_scraping(self, asin: str) -> Optional[AmazonProduct]:
        """Try to get product data using web scraping."""
        try:
            logger.debug(f"Trying web scraping for {asin}")
            self.session.total_scraping_calls += 1
            
            product = await self.scraper_client.scrape_product(asin)
            
            if product and product.current_price and product.current_price > 0:
                logger.debug(f"Web scraping returned valid product for {asin}")
                return product
            else:
                logger.debug(f"Web scraping returned invalid/incomplete data for {asin}")
                return None
                
        except Exception as e:
            logger.warning(f"Web scraping error for {asin}: {e}")
            return None
    
    def create_deals_from_products(
        self, 
        products: Dict[str, Optional[AmazonProduct]], 
        posts: List[SavingsGuruPost]
    ) -> List[Deal]:
        """
        Create Deal objects from real product data.
        CRITICAL: Only creates deals with real pricing data.
        """
        deals = []
        post_lookup = {asin: post for post in posts for asin in post.extracted_asins}
        
        for asin, product in products.items():
            if not product:
                continue  # Skip products without real data
            
            # Get associated SavingsGuru post for context
            savingsguru_post = post_lookup.get(asin)
            
            # Create deal from real product data
            deal = Deal.from_amazon_product(
                amazon_product=product,
                partner_tag=self.settings.amz_partner_tag,
                savingsguru_post=savingsguru_post
            )
            
            if deal:
                deals.append(deal)
                self.stats['deals_created'] += 1
                logger.info(f"✓ Created deal for {asin}: {deal.title} - ${deal.price}")
            else:
                logger.warning(f"✗ Failed to create deal for {asin} - validation failed")
        
        return deals
    
    def _sort_deals_by_discount(self, deals: List[Deal]) -> List[Deal]:
        """Sort deals by discount percentage (highest first)."""
        return sorted(
            deals, 
            key=lambda d: d.discount_percent or 0, 
            reverse=True
        )
    
    def _mark_featured_deals(self, deals: List[Deal], featured_threshold: int = 40) -> List[Deal]:
        """Mark top deals as featured based on discount percentage."""
        sorted_deals = self._sort_deals_by_discount(deals)
        
        # Mark top 20 deals with 40%+ discount as featured
        featured_count = 0
        for deal in sorted_deals:
            if (deal.discount_percent and 
                deal.discount_percent >= featured_threshold and 
                featured_count < 20):
                deal.featured = True
                featured_count += 1
            else:
                deal.featured = False
        
        return sorted_deals
    
    async def scrape_deals(self, max_pages: int = None, output_file: str = "deals.json") -> List[Deal]:
        """
        Main scraping method that orchestrates the entire process.
        Returns deals with 100% real data - no fake pricing ever generated.
        Now manages deal count to maintain target of ~120 deals.
        """
        logger.info("Starting SavingsGuru real data scraping with deal management")
        
        # Use settings default if no max_pages specified
        if max_pages is None:
            max_pages = self.settings.max_pages_to_scrape
        
        try:
            # Step 1: Scrape SavingsGuru posts (more pages for more deals)
            posts = await self.scrape_savingsguru_posts(max_pages)
            
            if not posts:
                logger.warning("No posts found on SavingsGuru - aborting")
                return []
            
            # Step 2: Extract unique ASINs
            all_asins = []
            for post in posts:
                all_asins.extend(post.extracted_asins)
            
            unique_asins = list(dict.fromkeys(all_asins))  # Remove duplicates
            logger.info(f"Found {len(unique_asins)} unique ASINs to process")
            
            if not unique_asins:
                logger.warning("No ASINs found in posts - aborting")
                return []
            
            # Step 3: Get real product data (PAAPI → scraping → skip)
            products = await self.get_real_product_data(unique_asins)
            
            # Step 4: Create deals from real data only
            new_deals = self.create_deals_from_products(products, posts)
            
            if not new_deals:
                logger.warning("No valid new deals created from real data")
                # Still process existing deals through deal manager
                new_deals = []
            else:
                logger.info(f"Created {len(new_deals)} new deals from scraped data")
            
            # Step 5: Use deal manager to handle deduplication, freshness, and count management
            # Determine output path first for deal manager
            if not output_file.startswith('/'):
                output_path = f"public/{output_file}"
            else:
                output_path = output_file
            
            management_result = await self.deal_manager.process_deals(new_deals, output_path)
            final_deals = management_result['deals']
            deal_stats = management_result['stats']
            
            # Update our stats with deal management info
            self.stats.update(deal_stats)
            self.stats['deals_created'] = len(final_deals)
            
            # Step 6: Sort and mark featured deals on final set
            final_deals = self._mark_featured_deals(final_deals)
            
            # Step 7: Save managed deals to output file
            deals_data = [deal.dict() for deal in final_deals]
            success = save_json_file(deals_data, output_path)
            
            if success:
                logger.info(f"Saved {len(final_deals)} managed deals to {output_path}")
                logger.info(f"Deal management stats: {deal_stats}")
            else:
                logger.error(f"Failed to save deals to {output_path}")
            
            # Complete session tracking
            self.session.completed_at = datetime.utcnow()
            
            # Log final statistics
            self._log_final_statistics()
            
            return final_deals
            
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
            self.session.add_error(f"Critical error: {e}")
            return []
    
    def _log_final_statistics(self):
        """Log comprehensive statistics about the scraping session."""
        logger.info("Scraping Session Complete - Final Statistics:")
        logger.info(f"  Posts scraped: {self.stats['posts_scraped']}")
        logger.info(f"  ASINs found: {self.stats['asins_found']}")
        logger.info(f"  PAAPI successes: {self.stats['paapi_success']}")
        logger.info(f"  Web scraping successes: {self.stats['scraping_success']}")
        logger.info(f"  Products skipped (no real data): {self.stats['products_skipped']}")
        logger.info(f"  Final deals created: {self.stats['deals_created']}")
        logger.info(f"  Success rate: {self.session.success_rate:.1f}%")
        logger.info(f"  Session ID: {self.session.session_id}")
        
        # Log data source breakdown
        paapi_pct = (self.stats['paapi_success'] / max(self.stats['deals_created'], 1)) * 100
        scraping_pct = (self.stats['scraping_success'] / max(self.stats['deals_created'], 1)) * 100
        
        logger.info(f"  Data sources - PAAPI: {paapi_pct:.1f}%, Scraping: {scraping_pct:.1f}%")
        
        if self.session.errors:
            logger.warning(f"  Errors encountered: {len(self.session.errors)}")


async def main():
    """Main entry point for running the scraper."""
    try:
        async with FocusedScraper() as scraper:
            deals = await scraper.scrape_deals(max_pages=3)
            print(f"\nScraping completed successfully!")
            print(f"Generated {len(deals)} deals with 100% real data")
            print(f"Zero fake prices generated")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())