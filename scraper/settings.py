"""
Configuration management using pydantic-settings.
Pattern mirrored from use-cases/pydantic-ai/examples/main_agent_reference/settings.py
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support for Amazon API integration."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Amazon Product Advertising API Configuration
    amz_access_key: str = Field(
        ..., 
        description="Amazon Product Advertising API Access Key",
        alias="AMZ_ACCESS_KEY"
    )
    amz_secret_key: str = Field(
        ..., 
        description="Amazon Product Advertising API Secret Key",
        alias="AMZ_SECRET_KEY"
    )
    amz_partner_tag: str = Field(
        ..., 
        description="Amazon Associate Partner Tag",
        alias="AMZ_PARTNER_TAG"
    )
    amz_marketplace: str = Field(
        default="CA", 
        description="Amazon marketplace country code"
    )
    
    # Rate limiting configuration
    api_rate_limit_delay: float = Field(
        default=1.0, 
        description="Minimum seconds between PAAPI requests"
    )
    scraper_delay_min: float = Field(
        default=1.0, 
        description="Minimum delay between scraping requests"
    )
    scraper_delay_max: float = Field(
        default=3.0, 
        description="Maximum delay between scraping requests"
    )
    
    # Scraping configuration
    max_retry_attempts: int = Field(
        default=3, 
        description="Maximum retry attempts for failed requests"
    )
    request_timeout: float = Field(
        default=30.0, 
        description="HTTP request timeout in seconds"
    )
    
    # Deal management configuration
    target_deal_count: int = Field(
        default=120, 
        description="Target number of deals to maintain on site"
    )
    max_pages_to_scrape: int = Field(
        default=20, 
        description="Maximum SavingsGuru pages to scrape for deals"
    )
    deal_freshness_hours: int = Field(
        default=24, 
        description="Hours after which deals should be refreshed"
    )
    min_deal_discount: int = Field(
        default=10, 
        description="Minimum discount percentage to include deal"
    )
    
    # Application Configuration
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    
    @field_validator("amz_access_key", "amz_secret_key", "amz_partner_tag")
    @classmethod
    def validate_amazon_credentials(cls, v):
        """Ensure Amazon API credentials are not empty."""
        if not v or v.strip() == "":
            raise ValueError("Amazon API credentials cannot be empty")
        return v
    
    @field_validator("amz_marketplace")
    @classmethod
    def validate_marketplace(cls, v):
        """Ensure marketplace is a valid country code."""
        valid_marketplaces = ["CA", "US", "UK", "DE", "FR", "IT", "ES", "IN", "JP", "AU"]
        if v not in valid_marketplaces:
            raise ValueError(f"Invalid marketplace: {v}. Must be one of {valid_marketplaces}")
        return v


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # For testing/development, create settings with dummy values if env vars missing
    if "development" in os.environ.get("APP_ENV", "development").lower():
        import warnings
        warnings.warn(f"Could not load settings: {e}. Using default values for development.")
        
        os.environ.setdefault("AMZ_ACCESS_KEY", "dummy_access_key")
        os.environ.setdefault("AMZ_SECRET_KEY", "dummy_secret_key") 
        os.environ.setdefault("AMZ_PARTNER_TAG", "savingsgurucc-20")
        
        settings = Settings()
    else:
        raise