#!/usr/bin/env python3
"""
Production scraper runner for maintaining ~120 deals.
This script is designed for scheduled runs (cron jobs, etc.) to keep the site fresh.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Add scraper directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scraper'))

from scraper.focused_scraper import FocusedScraper
from scraper.settings import Settings
from scraper.utils import setup_logging


async def run_production_scrape():
    """Run a production scrape targeting ~120 deals."""
    print(f"🚀 Starting production scrape at {datetime.now()}")
    print("Target: ~120 deals with real Amazon pricing")
    
    try:
        # Initialize with production settings
        settings = Settings()
        
        # Validate environment
        print("🔍 Validating production environment...")
        if not validate_production_environment(settings):
            return False
        
        # Run the scraper with deal management
        async with FocusedScraper(settings) as scraper:
            deals = await scraper.scrape_deals(
                output_file="public/deals.json"
            )
            
            if deals:
                print(f"✅ Production scrape completed successfully!")
                print(f"📊 Generated {len(deals)} deals with real data")
                print(f"🎯 Target: {settings.target_deal_count} deals")
                
                # Print deal management stats
                if hasattr(scraper, 'stats'):
                    stats = scraper.stats
                    print(f"📈 Stats:")
                    print(f"   - Existing deals: {stats.get('existing_deals', 0)}")
                    print(f"   - New deals scraped: {stats.get('new_deals_scraped', 0)}")
                    print(f"   - Final count: {stats.get('final_deal_count', len(deals))}")
                    print(f"   - PAAPI successes: {stats.get('paapi_success', 0)}")
                    print(f"   - Scraping successes: {stats.get('scraping_success', 0)}")
                    print(f"   - Products skipped: {stats.get('products_skipped', 0)}")
                
                return True
            else:
                print("❌ No deals generated - check logs")
                return False
                
    except Exception as e:
        print(f"💥 Production scrape failed: {e}")
        logging.exception("Production scrape error")
        return False


def validate_production_environment(settings: Settings) -> bool:
    """Validate the production environment is ready."""
    
    # Check Amazon API credentials
    if (not settings.amz_access_key or 
        settings.amz_access_key == "dummy_access_key" or
        not settings.amz_secret_key or 
        settings.amz_secret_key == "dummy_secret_key"):
        print("❌ Amazon API credentials not configured for production")
        return False
    
    # Check output directory
    public_dir = Path("public")
    if not public_dir.exists():
        try:
            public_dir.mkdir(parents=True, exist_ok=True)
            print("📁 Created public directory")
        except Exception as e:
            print(f"❌ Cannot create public directory: {e}")
            return False
    
    # Check write permissions
    try:
        test_file = public_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        print(f"❌ Cannot write to public directory: {e}")
        return False
    
    print("✅ Production environment validated")
    return True


def main():
    """Main entry point for production scraper."""
    
    # Set up production logging
    setup_logging("INFO")
    
    # Create log file for production runs
    log_file = Path("scraper_production.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    
    # Run the scraper
    success = asyncio.run(run_production_scrape())
    
    if success:
        print("🎉 Production scrape completed successfully")
        return 0
    else:
        print("😞 Production scrape failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)