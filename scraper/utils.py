"""
Shared utilities for logging, data formatting, and common operations.
Following error handling patterns from existing codebase.
"""

import asyncio
import logging
import time
import json
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration.
    Pattern inspired by use-cases/mcp-server/src/database/utils.ts
    """
    # Configure loguru
    logger.remove()  # Remove default handler
    
    # Add console handler
    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        logger.add(
            sink=log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="1 week"
        )
    
    logger.info(f"Logging configured with level: {log_level}")


def extract_asin_from_url(url: str) -> Optional[str]:
    """
    Extract ASIN from Amazon URL.
    Handles various Amazon URL formats including short links.
    """
    if not url:
        return None
    
    # Clean up the URL
    url = url.strip()
    
    # Common ASIN patterns in Amazon URLs
    patterns = [
        r'/dp/([A-Z0-9]{10})',          # /dp/ASIN format
        r'/gp/product/([A-Z0-9]{10})',  # /gp/product/ASIN format
        r'/product/([A-Z0-9]{10})',     # /product/ASIN format
        r'asin=([A-Z0-9]{10})',         # asin= parameter
        r'/([A-Z0-9]{10})/?$',          # ASIN at end of path
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            asin = match.group(1).upper()
            if validate_asin(asin):
                return asin
    
    return None


def validate_asin(asin: str) -> bool:
    """Validate ASIN format."""
    if not asin:
        return False
    
    # ASIN should be exactly 10 alphanumeric characters
    return len(asin) == 10 and asin.isalnum()


def resolve_short_link(short_url: str) -> Optional[str]:
    """
    Resolve Amazon short link (amzn.to) to get the full URL.
    This would need to be implemented with HTTP requests if needed.
    """
    # For now, return the short URL as-is
    # In production, you might want to actually resolve it
    return short_url


def format_price(price: float, currency: str = "CAD") -> str:
    """Format price for display."""
    if currency == "CAD":
        return f"${price:.2f}"
    else:
        return f"{currency} {price:.2f}"


def calculate_discount_percentage(original_price: float, current_price: float) -> int:
    """Calculate discount percentage."""
    if original_price <= 0 or current_price <= 0:
        return 0
    
    if current_price >= original_price:
        return 0
    
    discount = ((original_price - current_price) / original_price) * 100
    return round(discount)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-')


def save_json_file(data: Any, filepath: str, indent: int = 2) -> bool:
    """
    Save data to JSON file with proper error handling.
    Pattern based on database operation timing from mcp-server utils.
    """
    start_time = time.time()
    
    try:
        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath_obj, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        
        duration = time.time() - start_time
        logger.info(f"JSON file saved successfully in {duration*1000:.1f}ms: {filepath}")
        return True
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed to save JSON file after {duration*1000:.1f}ms: {filepath} - {e}")
        return False


def load_json_file(filepath: str) -> Optional[Any]:
    """Load data from JSON file with proper error handling."""
    start_time = time.time()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        duration = time.time() - start_time
        logger.info(f"JSON file loaded successfully in {duration*1000:.1f}ms: {filepath}")
        return data
        
    except FileNotFoundError:
        logger.warning(f"JSON file not found: {filepath}")
        return None
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed to load JSON file after {duration*1000:.1f}ms: {filepath} - {e}")
        return None


def clean_text(text: str) -> str:
    """Clean and normalize text data."""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove some common HTML entities
    html_entities = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' '
    }
    
    for entity, char in html_entities.items():
        text = text.replace(entity, char)
    
    return text


def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def create_affiliate_url(asin: str, partner_tag: str, marketplace: str = "CA") -> str:
    """Create Amazon affiliate URL."""
    base_urls = {
        "CA": "https://www.amazon.ca",
        "US": "https://www.amazon.com",
        "UK": "https://www.amazon.co.uk"
    }
    
    base_url = base_urls.get(marketplace, base_urls["CA"])
    return f"{base_url}/dp/{asin}?tag={partner_tag}"


def batch_items(items: List[Any], batch_size: int = 10) -> List[List[Any]]:
    """Split items into batches for processing."""
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    return f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 10000}"


def measure_execution_time(operation_name: str = "Operation"):
    """
    Decorator to measure execution time of functions.
    Pattern based on database timing from mcp-server.
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed successfully in {duration*1000:.1f}ms")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed after {duration*1000:.1f}ms: {e}")
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{operation_name} completed successfully in {duration*1000:.1f}ms")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{operation_name} failed after {duration*1000:.1f}ms: {e}")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def validate_deal_data(deal_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate deal data and return validation errors.
    Returns empty dict if valid, otherwise dict with error lists.
    """
    errors = {}
    
    # Required fields
    required_fields = ['id', 'title', 'price', 'affiliate_url', 'data_source']
    for field in required_fields:
        if field not in deal_data or not deal_data[field]:
            if 'required' not in errors:
                errors['required'] = []
            errors['required'].append(f"Missing required field: {field}")
    
    # Price validation
    if 'price' in deal_data:
        try:
            price = float(deal_data['price'])
            if price <= 0:
                if 'price' not in errors:
                    errors['price'] = []
                errors['price'].append("Price must be greater than 0")
        except (ValueError, TypeError):
            if 'price' not in errors:
                errors['price'] = []
            errors['price'].append("Price must be a valid number")
    
    # URL validation
    if 'affiliate_url' in deal_data:
        if not is_valid_url(deal_data['affiliate_url']):
            if 'url' not in errors:
                errors['url'] = []
            errors['url'].append("Invalid affiliate URL format")
    
    # Data source validation  
    if 'data_source' in deal_data:
        valid_sources = ['PAAPI', 'SCRAPED', 'FALLBACK']
        if deal_data['data_source'] not in valid_sources:
            if 'data_source' not in errors:
                errors['data_source'] = []
            errors['data_source'].append(f"Invalid data source. Must be one of: {valid_sources}")
    
    return errors