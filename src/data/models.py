"""
Data models for the scraping framework.
Defines structured data classes for products, jobs, and analysis results.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json


class JobStatus(Enum):
    """Enumeration for job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DataSource(Enum):
    """Enumeration for data sources."""
    BOOKS_TO_SCRAPE = "BooksToScrape"
    EBAY = "eBay"
    AMAZON = "Amazon"
    CUSTOM = "Custom"


@dataclass
class Product:
    """
    Data model for a scraped product.
    Represents a single product with all its attributes.
    """
    name: str
    price: Optional[str] = None
    price_numeric: Optional[float] = None
    link: Optional[str] = None
    image: Optional[str] = None
    availability: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    condition: Optional[str] = None
    shipping_cost: Optional[float] = None
    seller: Optional[str] = None
    
    # Metadata
    source: Optional[str] = None
    search_term: Optional[str] = None
    scrape_time: Optional[str] = None
    page_number: Optional[int] = None
    position_on_page: Optional[int] = None
    
    # Additional attributes for flexible data storage
    extra_attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Set scrape_time if not provided
        if not self.scrape_time:
            self.scrape_time = datetime.utcnow().isoformat()
        
        # Parse price if not already numeric
        if self.price and not self.price_numeric:
            self.price_numeric = self._parse_price(self.price)
    
    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to numeric value."""
        if not price_str:
            return None
        
        try:
            # Remove currency symbols and whitespace
            import re
            clean_price = re.sub(r'[^\d.,]', '', price_str)
            clean_price = clean_price.replace(',', '')
            return float(clean_price) if clean_price else None
        except (ValueError, TypeError):
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary."""
        data = {
            'name': self.name,
            'price': self.price,
            'price_numeric': self.price_numeric,
            'link': self.link,
            'image': self.image,
            'availability': self.availability,
            'description': self.description,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'category': self.category,
            'brand': self.brand,
            'model': self.model,
            'condition': self.condition,
            'shipping_cost': self.shipping_cost,
            'seller': self.seller,
            'source': self.source,
            'search_term': self.search_term,
            'scrape_time': self.scrape_time,
            'page_number': self.page_number,
            'position_on_page': self.position_on_page
        }
        
        # Add extra attributes
        data.update(self.extra_attributes)
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create product from dictionary."""
        # Separate known fields from extra attributes
        known_fields = {
            'name', 'price', 'price_numeric', 'link', 'image', 'availability',
            'description', 'rating', 'reviews_count', 'category', 'brand',
            'model', 'condition', 'shipping_cost', 'seller', 'source',
            'search_term', 'scrape_time', 'page_number', 'position_on_page'
        }
        
        product_data = {k: v for k, v in data.items() if k in known_fields}
        extra_attributes = {k: v for k, v in data.items() if k not in known_fields}
        
        product = cls(**product_data)
        product.extra_attributes = extra_attributes
        
        return product
    
    def is_valid(self) -> bool:
        """Check if product has minimum required data."""
        return bool(self.name and (self.link or self.price))
    
    def get_quality_score(self) -> float:
        """Calculate data quality score (0-1)."""
        fields = [
            self.name, self.price_numeric, self.link, self.image,
            self.availability, self.category, self.brand
        ]
        
        filled_fields = sum(1 for field in fields if field is not None)
        return filled_fields / len(fields)


@dataclass
class ScrapingJob:
    """
    Data model for a scraping job.
    Tracks the execution of scraping operations.
    """
    search_term: str
    source: str
    status: JobStatus = JobStatus.PENDING
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    
    # Job configuration
    max_pages: int = 1
    delay_range: tuple = (1, 2)
    timeout: int = 30
    
    # Results
    total_products: int = 0
    successful_products: int = 0
    failed_products: int = 0
    
    # Metadata
    job_id: Optional[int] = None
    user_id: Optional[str] = None
    priority: int = 1
    retries: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
    
    def start(self):
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow().isoformat()
    
    def complete(self, products_count: int = 0):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow().isoformat()
        self.successful_products = products_count
        self.total_products = products_count
    
    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow().isoformat()
        self.error_message = error_message
    
    def get_duration(self) -> Optional[float]:
        """Get job duration in seconds."""
        if not self.started_at or not self.completed_at:
            return None
        
        start = datetime.fromisoformat(self.started_at)
        end = datetime.fromisoformat(self.completed_at)
        return (end - start).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary."""
        return {
            'job_id': self.job_id,
            'search_term': self.search_term,
            'source': self.source,
            'status': self.status.value if isinstance(self.status, JobStatus) else self.status,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error_message': self.error_message,
            'max_pages': self.max_pages,
            'delay_range': self.delay_range,
            'timeout': self.timeout,
            'total_products': self.total_products,
            'successful_products': self.successful_products,
            'failed_products': self.failed_products,
            'user_id': self.user_id,
            'priority': self.priority,
            'retries': self.retries,
            'max_retries': self.max_retries
        }


@dataclass
class AnalysisResult:
    """
    Data model for analysis results.
    Stores the output of data analysis operations.
    """
    analysis_type: str
    generated_at: str
    data_period_start: Optional[str] = None
    data_period_end: Optional[str] = None
    total_records_analyzed: int = 0
    
    # Analysis results
    results: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    
    # Quality indicators
    confidence_score: Optional[float] = None
    data_quality_score: Optional[float] = None
    completeness_score: Optional[float] = None
    
    # Metadata
    analysis_id: Optional[str] = None
    version: str = "1.0"
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.generated_at:
            self.generated_at = datetime.utcnow().isoformat()
        
        if not self.analysis_id:
            import uuid
            self.analysis_id = str(uuid.uuid4())
    
    def add_metric(self, name: str, value: float, description: str = ""):
        """Add a metric to the analysis."""
        self.metrics[name] = value
        if description:
            self.parameters[f"{name}_description"] = description
    
    def add_insight(self, insight: str):
        """Add an insight to the analysis."""
        self.insights.append(insight)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary."""
        return {
            'analysis_id': self.analysis_id,
            'analysis_type': self.analysis_type,
            'generated_at': self.generated_at,
            'data_period_start': self.data_period_start,
            'data_period_end': self.data_period_end,
            'total_records_analyzed': self.total_records_analyzed,
            'results': self.results,
            'metrics': self.metrics,
            'insights': self.insights,
            'confidence_score': self.confidence_score,
            'data_quality_score': self.data_quality_score,
            'completeness_score': self.completeness_score,
            'version': self.version,
            'parameters': self.parameters
        }
    
    def to_json(self) -> str:
        """Convert analysis result to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class ScrapingConfiguration:
    """
    Data model for scraping configuration.
    Defines parameters for scraping operations.
    """
    source_name: str
    base_url: str
    selectors: Dict[str, str]
    
    # Pagination
    max_pages: int = 1
    start_page: int = 1
    
    # Request settings
    delay_range: tuple = (1, 2)
    timeout: int = 30
    retries: int = 3
    
    # Headers and user agents
    headers: Dict[str, str] = field(default_factory=dict)
    user_agents: List[str] = field(default_factory=list)
    
    # Advanced settings
    javascript_required: bool = False
    login_required: bool = False
    proxy_required: bool = False
    
    # Data processing
    data_filters: Dict[str, Any] = field(default_factory=dict)
    data_transformations: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.source_name:
            errors.append("Source name is required")
        
        if not self.base_url:
            errors.append("Base URL is required")
        
        if not self.selectors:
            errors.append("Selectors are required")
        
        required_selectors = ['container', 'name', 'price', 'link']
        for selector in required_selectors:
            if selector not in self.selectors:
                errors.append(f"Required selector '{selector}' is missing")
        
        if self.max_pages < 1:
            errors.append("Max pages must be at least 1")
        
        if self.timeout < 1:
            errors.append("Timeout must be at least 1 second")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'source_name': self.source_name,
            'base_url': self.base_url,
            'selectors': self.selectors,
            'max_pages': self.max_pages,
            'start_page': self.start_page,
            'delay_range': self.delay_range,
            'timeout': self.timeout,
            'retries': self.retries,
            'headers': self.headers,
            'user_agents': self.user_agents,
            'javascript_required': self.javascript_required,
            'login_required': self.login_required,
            'proxy_required': self.proxy_required,
            'data_filters': self.data_filters,
            'data_transformations': self.data_transformations
        }


# Factory functions for creating model instances

def create_product_from_scraped_data(data: Dict[str, Any], source: str, search_term: str) -> Product:
    """Create Product instance from scraped data."""
    return Product(
        name=data.get('name', ''),
        price=data.get('price'),
        link=data.get('link'),
        image=data.get('image'),
        availability=data.get('availability'),
        source=source,
        search_term=search_term,
        extra_attributes=data
    )


def create_scraping_job(search_term: str, source: str, **kwargs) -> ScrapingJob:
    """Create ScrapingJob instance with default values."""
    return ScrapingJob(
        search_term=search_term,
        source=source,
        **kwargs
    )


def create_analysis_result(analysis_type: str, **kwargs) -> AnalysisResult:
    """Create AnalysisResult instance with default values."""
    return AnalysisResult(
        analysis_type=analysis_type,
        generated_at=datetime.utcnow().isoformat(),
        **kwargs
    ) 