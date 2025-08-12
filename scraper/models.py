"""
Pydantic models for data validation and serialization.
Ensures type safety and consistency across the application.
"""

from pydantic import BaseModel, HttpUrl, Field, validator, field_validator
from typing import Optional, List, Literal
from decimal import Decimal
from datetime import datetime
from enum import Enum


class DataSource(str, Enum):
    """Data source types for tracking where product data came from."""
    PAAPI = "PAAPI"
    SCRAPED = "SCRAPED"
    FALLBACK = "FALLBACK"
    UNKNOWN = "UNKNOWN"


class AmazonProduct(BaseModel):
    """
    Amazon product data from PAAPI or scraping.
    This is the raw product data before transformation to Deal format.
    """
    asin: str = Field(..., description="Amazon ASIN", min_length=10, max_length=10)
    title: str = Field(..., description="Product title from Amazon")
    current_price: Optional[Decimal] = Field(None, description="Current price in CAD", ge=0)
    list_price: Optional[Decimal] = Field(None, description="Original/list price in CAD", ge=0)
    discount_percent: Optional[int] = Field(None, description="Calculated discount percentage", ge=0, le=100)
    image_url: Optional[HttpUrl] = Field(None, description="High-res product image URL")
    availability: str = Field(default="Unknown", description="Product availability status")
    prime_eligible: bool = Field(default=False, description="Prime shipping eligibility")
    brand: Optional[str] = Field(None, description="Product brand")
    features: List[str] = Field(default_factory=list, description="Product features list")
    data_source: DataSource = Field(default=DataSource.UNKNOWN, description="Source of the data")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow, description="When data was retrieved")
    
    @field_validator('discount_percent')
    @classmethod
    def calculate_discount_percent(cls, v, values):
        """Calculate discount percentage if not provided."""
        if v is not None:
            return v
        
        # Try to calculate from prices if both are available
        current_price = values.data.get('current_price') if hasattr(values, 'data') else None
        list_price = values.data.get('list_price') if hasattr(values, 'data') else None
        
        if current_price and list_price and list_price > current_price:
            discount = float((list_price - current_price) / list_price * 100)
            return round(discount)
        
        return None
    
    @field_validator('asin')
    @classmethod
    def validate_asin(cls, v):
        """Validate ASIN format."""
        if not v.isalnum():
            raise ValueError('ASIN must be alphanumeric')
        return v.upper()
    
    def to_affiliate_url(self, partner_tag: str) -> str:
        """Generate Amazon.ca affiliate URL with partner tag."""
        return f"https://www.amazon.ca/dp/{self.asin}?tag={partner_tag}"


class SavingsGuruPost(BaseModel):
    """
    Data structure for SavingsGuru.ca post information.
    Used for extracting ASINs and basic deal information.
    """
    post_id: str = Field(..., description="SavingsGuru post ID")
    post_title: str = Field(..., description="Original SavingsGuru post title")
    post_url: HttpUrl = Field(..., description="SavingsGuru post URL")
    amazon_short_links: List[str] = Field(default_factory=list, description="Found amzn.to short links")
    extracted_asins: List[str] = Field(default_factory=list, description="Extracted ASINs from links")
    category: str = Field(default="General", description="Deal category")
    description: Optional[str] = Field(None, description="Post description/content")
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="When post was scraped")


class Deal(BaseModel):
    """
    Final deal object for frontend consumption.
    This is the processed and validated deal data ready for the React app.
    """
    id: str = Field(..., description="Unique deal identifier")
    title: str = Field(..., description="Deal title for display")
    image_url: HttpUrl = Field(..., description="Product image URL")
    price: float = Field(..., description="Current price in CAD", ge=0)
    original_price: Optional[float] = Field(None, description="Original/list price in CAD", ge=0)
    discount_percent: Optional[int] = Field(None, description="Discount percentage", ge=0, le=100)
    category: str = Field(..., description="Deal category")
    description: str = Field(..., description="Deal description")
    affiliate_url: HttpUrl = Field(..., description="Amazon.ca URL with affiliate tag")
    featured: bool = Field(default=False, description="Whether this deal is featured")
    date_added: str = Field(..., description="ISO format date when deal was added")
    data_source: DataSource = Field(..., description="Source of the product data")
    asin: str = Field(..., description="Amazon ASIN for reference")
    
    @field_validator('id')
    @classmethod
    def generate_id(cls, v, values):
        """Generate a unique ID if not provided."""
        if v:
            return v
        
        # Generate ID from ASIN if available
        asin = values.data.get('asin') if hasattr(values, 'data') else None
        if asin:
            return f"deal_{asin}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        return f"deal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    @classmethod
    def from_amazon_product(
        cls,
        amazon_product: AmazonProduct,
        partner_tag: str,
        savingsguru_post: Optional[SavingsGuruPost] = None
    ) -> Optional['Deal']:
        """
        Create a Deal from AmazonProduct data.
        Returns None if required data is missing (no fake data generation).
        """
        # CRITICAL: Only create deals with real pricing data
        if not amazon_product.current_price or amazon_product.current_price <= 0:
            return None
        
        # Use SavingsGuru post data for description/category if available
        category = savingsguru_post.category if savingsguru_post else "General"
        description = savingsguru_post.description or f"Great deal on {amazon_product.title}"
        
        # Generate deal ID
        deal_id = f"deal_{amazon_product.asin}_{datetime.utcnow().strftime('%Y%m%d')}"
        
        # Determine if this should be featured (high discount deals)
        featured = (
            amazon_product.discount_percent is not None and 
            amazon_product.discount_percent >= 40
        )
        
        try:
            return cls(
                id=deal_id,
                title=amazon_product.title,
                image_url=amazon_product.image_url,
                price=float(amazon_product.current_price),
                original_price=float(amazon_product.list_price) if amazon_product.list_price else None,
                discount_percent=amazon_product.discount_percent,
                category=category,
                description=description,
                affiliate_url=amazon_product.to_affiliate_url(partner_tag),
                featured=featured,
                date_added=datetime.utcnow().isoformat(),
                data_source=amazon_product.data_source,
                asin=amazon_product.asin
            )
        except Exception:
            # If any validation fails, return None (no fake data)
            return None


class ScrapingResult(BaseModel):
    """Result of a scraping operation with metadata."""
    success: bool = Field(..., description="Whether the scraping was successful")
    product: Optional[AmazonProduct] = Field(None, description="Scraped product data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    attempts: int = Field(default=1, description="Number of attempts made")
    response_time: float = Field(..., description="Response time in seconds")
    status_code: Optional[int] = Field(None, description="HTTP status code")


class ScrapingSession(BaseModel):
    """Metadata for a complete scraping session."""
    session_id: str = Field(..., description="Unique session identifier")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(None)
    total_products_attempted: int = Field(default=0)
    total_products_successful: int = Field(default=0)
    total_api_calls: int = Field(default=0)
    total_scraping_calls: int = Field(default=0)
    errors: List[str] = Field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_products_attempted == 0:
            return 0.0
        return (self.total_products_successful / self.total_products_attempted) * 100
    
    def add_error(self, error: str) -> None:
        """Add an error to the session."""
        self.errors.append(f"{datetime.utcnow().isoformat()}: {error}")