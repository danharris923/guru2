#!/usr/bin/env python3
"""
Scheduler for running the production scraper at regular intervals.
Maintains ~120 deals by running scraper every few hours.
"""

import asyncio
import schedule
import time
import logging
from datetime import datetime
from pathlib import Path

from run_production_scraper import run_production_scrape


def job_wrapper():
    """Wrapper to run async scraper in sync context."""
    print(f"\n⏰ Scheduled scraper run started at {datetime.now()}")
    
    try:
        success = asyncio.run(run_production_scrape())
        if success:
            print(f"✅ Scheduled run completed at {datetime.now()}")
        else:
            print(f"❌ Scheduled run failed at {datetime.now()}")
    except Exception as e:
        print(f"💥 Scheduled run crashed at {datetime.now()}: {e}")
        logging.exception("Scheduled run error")


def main():
    """Set up and run the scheduler."""
    print("🕒 SavingsGuru Deal Scraper Scheduler")
    print("Maintaining ~120 deals with regular updates")
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper_scheduler.log'),
            logging.StreamHandler()
        ]
    )
    
    # Schedule scraper runs
    # Run every 6 hours to keep deals fresh
    schedule.every(6).hours.do(job_wrapper)
    
    # Optional: Run daily at specific time (e.g., 6 AM)
    # schedule.every().day.at("06:00").do(job_wrapper)
    
    print("📅 Scheduler configured:")
    print("   - Every 6 hours: Full scraper run")
    print("   - Target: ~120 deals")
    print("   - Deal freshness: 24 hours")
    print("   - Press Ctrl+C to stop\n")
    
    # Run initial scrape
    print("🚀 Running initial scrape...")
    job_wrapper()
    
    # Start scheduler loop
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n⏹️ Scheduler stopped by user")
    except Exception as e:
        print(f"\n💥 Scheduler crashed: {e}")
        logging.exception("Scheduler error")


if __name__ == "__main__":
    main()