#!/usr/bin/env python3
"""
Entry point script to run the SavingsGuru scraper and generate deals.json.
This script handles the complete data pipeline from scraping to React app consumption.
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# Add scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.focused_scraper import FocusedScraper
from scraper.settings import Settings
from scraper.utils import setup_logging


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run SavingsGuru scraper to generate real Amazon deals data'
    )
    
    parser.add_argument(
        '--pages', 
        type=int, 
        default=None,
        help='Number of SavingsGuru pages to scrape (default: from settings, ~20)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='public/deals.json',
        help='Output file path for deals data (default: public/deals.json)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--no-paapi',
        action='store_true',
        help='Skip Amazon PAAPI and use only web scraping'
    )
    
    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Run in test mode with limited data'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point for the scraper."""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    
    print("Starting SavingsGuru Real Data Scraper (Target: ~120 deals)")
    
    # Use settings default if pages not specified
    pages_to_scrape = args.pages
    if pages_to_scrape is None:
        settings = Settings()
        pages_to_scrape = settings.max_pages_to_scrape
    
    print(f"Pages to scrape: {pages_to_scrape}")
    print(f"Output file: {args.output}")
    print(f"Log level: {args.log_level}")
    
    if args.no_paapi:
        print("WARNING: PAAPI disabled - using web scraping only")
    
    if args.test_mode:
        print("Running in test mode")
        pages_to_scrape = min(pages_to_scrape, 2)  # Limit pages in test mode
    
    try:
        # Initialize settings
        settings = Settings()
        
        # Verify environment
        if not verify_environment(settings, args.no_paapi):
            return 1
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run the scraper
        async with FocusedScraper(settings) as scraper:
            # Optionally disable PAAPI for testing
            if args.no_paapi:
                scraper.amazon_api = None
            
            deals = await scraper.scrape_deals(
                max_pages=pages_to_scrape,
                output_file=args.output
            )
            
            if deals:
                print(f"Successfully generated {len(deals)} deals with real data")
                print(f"Output saved to: {args.output}")
                
                # Print summary statistics
                print_summary_stats(deals, scraper.stats)
                
                return 0
            else:
                print("ERROR: No deals generated - check logs for errors")
                return 1
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        return 1
    except Exception as e:
        print(f"Critical error: {e}")
        return 1


def verify_environment(settings: Settings, skip_paapi: bool = False) -> bool:
    """Verify that the environment is properly configured."""
    print("Verifying environment configuration...")
    
    if not skip_paapi:
        # Check Amazon API credentials
        try:
            if not settings.amz_access_key or settings.amz_access_key == "dummy_access_key":
                print("ERROR: AMZ_ACCESS_KEY not configured or using dummy value")
                print("   Set your real Amazon API credentials in .env file")
                return False
                
            if not settings.amz_secret_key or settings.amz_secret_key == "dummy_secret_key":
                print("ERROR: AMZ_SECRET_KEY not configured or using dummy value")
                return False
                
            print("SUCCESS: Amazon API credentials configured")
        except Exception as e:
            print(f"ERROR: Error checking API credentials: {e}")
            return False
    
    # Check output directory is writable
    try:
        test_file = Path("public") / ".test_write"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")
        test_file.unlink()
        print("SUCCESS: Output directory is writable")
    except Exception as e:
        print(f"ERROR: Cannot write to output directory: {e}")
        return False
    
    return True


def print_summary_stats(deals, stats):
    """Print summary statistics about the scraping session."""
    print("\nScraping Summary:")
    print(f"   SavingsGuru posts processed: {stats['posts_scraped']}")
    print(f"   Amazon ASINs found: {stats['asins_found']}")
    print(f"   PAAPI successes: {stats['paapi_success']}")
    print(f"   Web scraping successes: {stats['scraping_success']}")
    print(f"   Products skipped (no real data): {stats['products_skipped']}")
    print(f"   Final deals created: {stats['deals_created']}")
    
    # Data source breakdown
    paapi_deals = sum(1 for deal in deals if deal.data_source == 'PAAPI')
    scraped_deals = sum(1 for deal in deals if deal.data_source == 'SCRAPED')
    
    print(f"\nData Sources:")
    print(f"   PAAPI: {paapi_deals} deals ({paapi_deals/len(deals)*100:.1f}%)")
    print(f"   Web Scraped: {scraped_deals} deals ({scraped_deals/len(deals)*100:.1f}%)")
    
    # Discount analysis
    discounts = [deal.discount_percent for deal in deals if deal.discount_percent]
    if discounts:
        avg_discount = sum(discounts) / len(discounts)
        max_discount = max(discounts)
        featured_count = sum(1 for deal in deals if deal.featured)
        
        print(f"\nDiscount Analysis:")
        print(f"   Average discount: {avg_discount:.1f}%")
        print(f"   Maximum discount: {max_discount}%")
        print(f"   Featured deals: {featured_count}")
    
    # Categories
    categories = {}
    for deal in deals:
        categories[deal.category] = categories.get(deal.category, 0) + 1
    
    print(f"\nCategories:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   {category}: {count} deals")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)