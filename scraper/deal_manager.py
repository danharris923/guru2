"""
Deal management system for maintaining target deal count and freshness.
Handles deduplication, rotation, and cleanup to maintain ~120 active deals.
"""

import json
import asyncio
from typing import List, Dict, Set
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from .models import Deal
from .settings import Settings


class DealManager:
    """
    Manages deal lifecycle to maintain target count and freshness.
    Handles deduplication, rotation, and quality filtering.
    """
    
    def __init__(self, settings: Settings):
        """Initialize deal manager with settings."""
        self.settings = settings
        self.existing_deals: List[Deal] = []
        self.existing_asins: Set[str] = set()
    
    async def load_existing_deals(self, deals_file: str = "public/deals.json") -> List[Deal]:
        """Load existing deals from file."""
        deals_path = Path(deals_file)
        
        if not deals_path.exists():
            logger.info("No existing deals file found - starting fresh")
            return []
        
        try:
            with open(deals_path, 'r', encoding='utf-8') as f:
                deals_data = json.load(f)
            
            # Convert to Deal objects
            deals = []
            for deal_data in deals_data:
                try:
                    deal = Deal(**deal_data)
                    deals.append(deal)
                except Exception as e:
                    logger.warning(f"Skipping invalid deal {deal_data.get('id', 'unknown')}: {e}")
            
            self.existing_deals = deals
            self.existing_asins = {deal.asin for deal in deals}
            
            logger.info(f"Loaded {len(deals)} existing deals from {deals_file}")
            return deals
            
        except Exception as e:
            logger.error(f"Failed to load existing deals: {e}")
            return []
    
    def filter_fresh_deals(self, deals: List[Deal]) -> List[Deal]:
        """Filter deals that are still fresh (within freshness window)."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.settings.deal_freshness_hours)
        
        fresh_deals = []
        for deal in deals:
            try:
                deal_time = datetime.fromisoformat(deal.dateAdded.replace('Z', '+00:00'))
                if deal_time.replace(tzinfo=None) > cutoff_time:
                    fresh_deals.append(deal)
            except Exception as e:
                logger.warning(f"Invalid date format for deal {deal.id}: {e}")
                # Keep deal if date parsing fails (assume fresh)
                fresh_deals.append(deal)
        
        removed_count = len(deals) - len(fresh_deals)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} stale deals (older than {self.settings.deal_freshness_hours}h)")
        
        return fresh_deals
    
    def deduplicate_deals(self, new_deals: List[Deal]) -> List[Deal]:
        """Remove deals that already exist (by ASIN)."""
        unique_deals = []
        
        for deal in new_deals:
            if deal.asin not in self.existing_asins:
                unique_deals.append(deal)
                self.existing_asins.add(deal.asin)
            else:
                logger.debug(f"Skipping duplicate deal: {deal.asin}")
        
        duplicates_removed = len(new_deals) - len(unique_deals)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate deals")
        
        return unique_deals
    
    def filter_quality_deals(self, deals: List[Deal]) -> List[Deal]:
        """Filter deals by minimum quality criteria."""
        quality_deals = []
        
        for deal in deals:
            # Check minimum discount
            if deal.discountPercent and deal.discountPercent >= self.settings.min_deal_discount:
                quality_deals.append(deal)
            elif not deal.discountPercent:
                # Keep deals without discount info (might be clearance/special deals)
                quality_deals.append(deal)
            else:
                logger.debug(f"Filtered out low discount deal: {deal.title} ({deal.discountPercent}%)")
        
        filtered_count = len(deals) - len(quality_deals)
        if filtered_count > 0:
            logger.info(f"Filtered out {filtered_count} deals below {self.settings.min_deal_discount}% discount")
        
        return quality_deals
    
    def manage_deal_count(self, all_deals: List[Deal]) -> List[Deal]:
        """Manage deal count to stay near target."""
        target = self.settings.target_deal_count
        
        if len(all_deals) <= target:
            logger.info(f"Deal count ({len(all_deals)}) is within target ({target})")
            return all_deals
        
        # Sort by priority: featured first, then by discount, then by date
        def deal_priority(deal: Deal) -> tuple:
            return (
                not deal.featured,  # Featured deals first (False sorts before True)
                -(deal.discountPercent or 0),  # Higher discounts first
                deal.dateAdded  # Newer deals first (assuming ISO format sorts correctly)
            )
        
        sorted_deals = sorted(all_deals, key=deal_priority)
        selected_deals = sorted_deals[:target]
        
        removed_count = len(all_deals) - len(selected_deals)
        logger.info(f"Trimmed to {len(selected_deals)} deals (removed {removed_count} lower priority)")
        
        return selected_deals
    
    def get_scraping_stats(self, existing_count: int, new_count: int, final_count: int) -> Dict[str, int]:
        """Calculate scraping statistics."""
        return {
            'existing_deals': existing_count,
            'new_deals_scraped': new_count,
            'final_deal_count': final_count,
            'deals_added': max(0, final_count - existing_count),
            'target_remaining': max(0, self.settings.target_deal_count - final_count)
        }
    
    async def process_deals(self, new_deals: List[Deal], deals_file: str = "public/deals.json") -> Dict:
        """
        Main deal processing pipeline:
        1. Load existing deals
        2. Filter fresh deals
        3. Deduplicate new deals
        4. Apply quality filters
        5. Manage total count
        6. Return statistics
        """
        logger.info("Starting deal management process")
        
        # Step 1: Load existing deals
        existing_deals = await self.load_existing_deals(deals_file)
        existing_count = len(existing_deals)
        
        # Step 2: Filter existing deals by freshness
        fresh_existing = self.filter_fresh_deals(existing_deals)
        
        # Step 3: Deduplicate new deals
        unique_new_deals = self.deduplicate_deals(new_deals)
        new_count = len(unique_new_deals)
        
        # Step 4: Apply quality filters to new deals
        quality_new_deals = self.filter_quality_deals(unique_new_deals)
        
        # Step 5: Combine and manage total count
        all_deals = fresh_existing + quality_new_deals
        final_deals = self.manage_deal_count(all_deals)
        final_count = len(final_deals)
        
        # Step 6: Calculate statistics
        stats = self.get_scraping_stats(existing_count, new_count, final_count)
        
        logger.info(f"Deal management complete: {stats}")
        
        return {
            'deals': final_deals,
            'stats': stats
        }


async def main():
    """Test the deal manager."""
    from .settings import Settings
    
    settings = Settings()
    manager = DealManager(settings)
    
    # Test with empty new deals
    result = await manager.process_deals([])
    print(f"Test result: {result['stats']}")


if __name__ == "__main__":
    asyncio.run(main())