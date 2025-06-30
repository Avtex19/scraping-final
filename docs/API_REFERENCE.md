# API Reference - Advanced Web Scraping Framework

> **📢 Recent Updates**: The CLI has been moved to `src/cli/` and the Amazon scraper has been significantly enhanced with sophisticated anti-bot protection. See the [changelog](../README.md#recent-updates--improvements) for details.

## Import Paths

### Updated Import Paths (v2.0+)
```python
# CLI Components
from src.cli.interface import ScrapingCLI
from src.cli.commands import CommandProcessor

# Enhanced Amazon Scraper
from src.scrapers.scrapy_crawler.amazon_scraper import AmazonScrapyRunner

# Other Scrapers (unchanged)
from src.scrapers.static_scraper import StaticScraper
from src.scrapers.selenium_scraper import EbayScraper
```

## Table of Contents
1. [Core Modules](#core-modules)
2. [Scrapers](#scrapers)
3. [Data Management](#data-management)
4. [Analysis](#analysis)
5. [CLI Interface](#cli-interface)
6. [Utilities](#utilities)
7. [Configuration](#configuration)
8. [Type Definitions](#type-definitions)

## Core Modules

### Overview
The framework is organized into several core modules that handle different aspects of web scraping, data processing, and analysis.

```
src/
├── scrapers/        # Web scraping implementations
├── data/           # Data models and database operations
├── analysis/       # Statistical analysis and reporting
├── cli/            # Command-line interface
└── utils/          # Utility functions and helpers
```

## Scrapers

### Base Scraper

#### `src.scrapers.base_scraper.BaseScraper`

Abstract base class for all scrapers.

```python
class BaseScraper(ABC):
    @abstractmethod
    def scrape(self) -> List[Dict[str, Any]]:
        """Run the scraping process and return extracted data."""
        pass
```

**Methods:**
- `scrape()`: Abstract method that must be implemented by subclasses

### Static Scraper

#### `src.scrapers.static_scraper.StaticScraper`

BeautifulSoup4-based scraper for static HTML content.

```python
class StaticScraper(BaseScraper):
    def __init__(self, config: Dict[str, Any], log_file: str = 'logs/static_scraper.log')
    def scrape(self) -> List[Dict[str, Any]]
```

**Constructor Parameters:**
- `config` (Dict): Configuration dictionary with scraping parameters
- `log_file` (str): Path to log file

**Methods:**
- `scrape()`: Execute static scraping based on configuration

**Configuration Format:**
```python
{
    'name': 'SiteName',
    'base_url': 'https://example.com/page-{}.html',
    'start_page': 1,
    'max_pages': 3,
    'delay_range': (1, 2),
    'selectors': {
        'container': '.product',
        'name': '.title',
        'price': '.price',
        'link': 'a'
    }
}
```

### Dynamic Scraper

#### `src.scrapers.selenium_scraper.EbayScraper`

Selenium WebDriver-based scraper for dynamic content.

```python
class EbayScraper:
    def __init__(self, chromedriver_path: str = None, headless: bool = False, 
                 timeout: int = 10, log_file: str = 'logs/ebay_scraper.log')
    def scrape(self, search_term: str, max_pages: int = 3, 
               delay_between_pages: int = 2) -> List[Dict[str, Any]]
    def scrape_multiple_terms(self, search_terms: List[str], max_pages: int = 3, 
                             delay_between_pages: int = 2) -> List[Dict[str, Any]]
    def close(self)
```

**Constructor Parameters:**
- `chromedriver_path` (str): Path to ChromeDriver executable
- `headless` (bool): Run browser in headless mode
- `timeout` (int): WebDriver timeout in seconds
- `log_file` (str): Path to log file

**Methods:**
- `scrape(search_term, max_pages, delay_between_pages)`: Scrape single search term
- `scrape_multiple_terms(search_terms, max_pages, delay_between_pages)`: Scrape multiple terms
- `close()`: Close WebDriver and clean up resources

**Context Manager Support:**
```python
with EbayScraper(headless=True) as scraper:
    results = scraper.scrape('laptop')
```

### Framework Scraper

#### `src.scrapers.scrapy_crawler.amazon_scraper.AmazonScrapyRunner`

Scrapy framework-based scraper with advanced anti-bot protection.

```python
class AmazonScrapyRunner:
    def __init__(self, db_path: str = "scraped_data.db")
    def run_scraper(self, search_terms: List[str], max_pages: int = 1) -> List[Dict[str, Any]]
```

**Constructor Parameters:**
- `db_path` (str): Path to SQLite database

**Methods:**
- `run_scraper(search_terms, max_pages)`: Execute Scrapy scraping with database integration

**Features:**
- User-Agent rotation middleware
- Anti-bot detection and handling
- Automatic retry with exponential backoff
- Database integration

## Data Management

### Database

#### `src.data.database.Database`

SQLite database interface with job tracking and product storage.

```python
class Database:
    def __init__(self, db_path: str = "scraped_data.db")
    def queue_job(self, search_term: str) -> int
    def mark_job_complete(self, job_id: int)
    def insert_products(self, products: List[Dict[str, Any]], job_id: int = None)
    def get_products(self, source: str = None, search_term: str = None) -> List[Dict[str, Any]]
    def get_pending_jobs() -> List[sqlite3.Row]
    def close()
```

**Constructor Parameters:**
- `db_path` (str): Path to SQLite database file

**Methods:**
- `queue_job(search_term)`: Create new scraping job, returns job_id
- `mark_job_complete(job_id)`: Mark job as completed with timestamp
- `insert_products(products, job_id)`: Insert scraped products into database
- `get_products(source, search_term)`: Retrieve products with optional filtering
- `get_pending_jobs()`: Get all pending jobs
- `close()`: Close database connection

**Context Manager Support:**
```python
with Database() as db:
    job_id = db.queue_job('search_term')
    db.insert_products(results, job_id)
```

### Data Models

#### `src.data.models.Product`

Data class representing a scraped product.

```python
@dataclass
class Product:
    name: str
    price: Optional[float] = None
    price_numeric: Optional[float] = None
    link: Optional[str] = None
    image: Optional[str] = None
    availability: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    condition: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    source: Optional[str] = None
    search_term: Optional[str] = None
    scrape_time: Optional[str] = None
    extra_attributes: Dict[str, Any] = field(default_factory=dict)
```

**Methods:**
- `from_dict(data: Dict) -> Product`: Create Product from dictionary
- `to_dict() -> Dict`: Convert Product to dictionary
- `is_valid() -> bool`: Check if product has minimum required data
- `get_quality_score() -> float`: Calculate data quality score (0-1)

#### `src.data.models.ScrapingConfiguration`

Configuration model for scraping operations.

```python
@dataclass
class ScrapingConfiguration:
    source_name: str
    base_url: str
    selectors: Dict[str, str]
    max_pages: int = 1
    start_page: int = 1
    delay_range: tuple = (1, 2)
    timeout: int = 30
    retries: int = 3
```

**Methods:**
- `validate() -> List[str]`: Validate configuration and return errors
- `is_valid() -> bool`: Check if configuration is valid
- `to_dict() -> Dict`: Convert to dictionary

### Data Processing

#### `src.data.processors.DataProcessor`

Data cleaning and validation pipeline.

```python
class DataProcessor:
    def __init__(self)
    def process_products(self, products: List[Dict], pipeline: List[str]) -> List[Product]
    def clean_text(self, data: Dict) -> Dict
    def normalize_price(self, data: Dict) -> Dict
    def validate_url(self, data: Dict) -> Dict
    def extract_currency(self, data: Dict) -> Dict
```

**Methods:**
- `process_products(products, pipeline)`: Apply processing pipeline to products
- `clean_text(data)`: Clean and sanitize text fields
- `normalize_price(data)`: Extract and normalize price data
- `validate_url(data)`: Validate and clean URLs
- `extract_currency(data)`: Extract currency information

## Analysis

### Statistical Analysis

#### `src.analysis.statistics.DataStatistics`

Comprehensive statistical analysis of scraped data.

```python
class DataStatistics:
    def __init__(self, db_path: str = "scraped_data.db")
    def load_data(self) -> pd.DataFrame
    def data_quality_checks(self) -> Dict[str, Any]
    def statistical_summaries(self) -> Dict[str, Any]
    def generate_price_analysis(self) -> Dict[str, Any]
    def export_statistics(self, output_dir: str, format: str = "json") -> str
```

**Methods:**
- `load_data()`: Load data from database into pandas DataFrame
- `data_quality_checks()`: Assess data completeness and validity
- `statistical_summaries()`: Generate statistical summaries by source
- `generate_price_analysis()`: Advanced price analysis with outlier detection
- `export_statistics(output_dir, format)`: Export analysis in specified format

**Data Quality Metrics:**
- Completeness percentages for all fields
- Validity checks for prices and URLs
- Duplicate detection
- Consistency analysis across sources

### Trend Analysis

#### `src.analysis.trends.TrendAnalyzer`

Time-based trend analysis and source comparison.

```python
class TrendAnalyzer:
    def __init__(self, db_path: str = "scraped_data.db")
    def load_data(self) -> pd.DataFrame
    def analyze_price_trends(self) -> Dict[str, Any]
    def comparative_source_analysis(self) -> Dict[str, Any]
    def generate_trend_visualizations(self, output_dir: str) -> List[str]
    def generate_trend_report(self) -> Dict[str, Any]
```

**Methods:**
- `analyze_price_trends()`: Analyze price changes over time
- `comparative_source_analysis()`: Compare performance across sources
- `generate_trend_visualizations(output_dir)`: Create trend charts
- `generate_trend_report()`: Comprehensive trend analysis report

### Report Generation

#### `src.analysis.reports.ReportGenerator`

Professional HTML report generation with charts and visualizations.

```python
class ReportGenerator:
    def __init__(self, db_path: str = "scraped_data.db")
    def generate_comprehensive_report(self, output_dir: str) -> str
    def generate_statistical_report(self, output_dir: str) -> str
    def generate_custom_report(self, config: Dict, output_dir: str) -> str
    def export_data_formats(self, output_dir: str) -> Dict[str, str]
    def export_charts(self, output_dir: str) -> str
```

**Methods:**
- `generate_comprehensive_report(output_dir)`: Full analysis report with all features
- `generate_statistical_report(output_dir)`: Statistics-focused report
- `generate_custom_report(config, output_dir)`: Configurable report generation
- `export_data_formats(output_dir)`: Export data in CSV, JSON, Excel formats
- `export_charts(output_dir)`: Export all charts as standalone files

## CLI Interface

### Main Interface

#### `src.cli.interface.ScrapingCLI`

Interactive command-line interface for the framework.

```python
class ScrapingCLI:
    def __init__(self)
    def run(self)
    def run_comprehensive_scrape(self)
    def view_data_analysis(self)
    def generate_reports_menu(self)
    def export_menu(self)
```

**Methods:**
- `run()`: Start interactive CLI session
- `run_comprehensive_scrape()`: Execute all scraping sources
- `view_data_analysis()`: Interactive data analysis menu
- `generate_reports_menu()`: Report generation options
- `export_menu()`: Data export options

### Command Processor

#### `src.cli.commands.CommandProcessor`

Advanced command processing and automation.

```python
class CommandProcessor:
    def __init__(self, config_path: str = None)
    def run_batch_scraping(self, sources: List[str] = None) -> Dict[str, Any]
    def validate_configuration(self) -> bool
    def run_system_diagnostics(self) -> Dict[str, Any]
    def export_configuration_template(self, output_path: str) -> str
```

**Methods:**
- `run_batch_scraping(sources)`: Execute batch scraping operations
- `validate_configuration()`: Validate system configuration
- `run_system_diagnostics()`: Check system health and dependencies
- `export_configuration_template(output_path)`: Generate configuration template

## Utilities

### Configuration Management

#### `src.utils.config`

Configuration constants and helpers.

```python
static_config = {
    'name': 'BooksToScrape',
    'base_url': 'http://books.toscrape.com/catalogue/page-{}.html',
    'selectors': {...}
}
```

### Logging

#### `src.utils.logger.setup_logger`

Enhanced logging setup with multiprocessing support.

```python
def setup_logger(name: str, log_file: str = None, log_level: int = logging.INFO, 
                 log_queue: Queue = None) -> logging.Logger
```

**Parameters:**
- `name` (str): Logger name
- `log_file` (str): Log file path
- `log_level` (int): Logging level
- `log_queue` (Queue): Multiprocessing queue for safe logging

**Returns:**
- Configured logger instance

### Helper Functions

#### `src.utils.helpers`

Utility functions for common operations.

```python
class RequestHelper:
    def __init__(self, delay_range: tuple = (1, 2))
    def get_with_delay(self, url: str, headers: Dict = None) -> requests.Response

def build_absolute_url(base: str, link: str) -> str
def sanitize_price(price_str: str) -> float
def sanitize_text(text: str) -> str
```

**RequestHelper Methods:**
- `get_with_delay(url, headers)`: HTTP GET with random delay

**Utility Functions:**
- `build_absolute_url(base, link)`: Create absolute URLs
- `sanitize_price(price_str)`: Clean and parse price strings
- `sanitize_text(text)`: Clean and normalize text

### Multiprocessing Logging

#### `src.utils.multiproc_logging`

Safe logging for multiprocessing operations.

```python
def get_log_queue() -> Queue
def setup_worker_logger(log_queue: Queue)
def start_logging_listener(log_queue: Queue, log_file: str) -> QueueListener
```

**Functions:**
- `get_log_queue()`: Create multiprocessing-safe log queue
- `setup_worker_logger(log_queue)`: Configure worker process logging
- `start_logging_listener(log_queue, log_file)`: Start logging listener in main process

## Configuration

### YAML Configuration Schema

#### `config/settings.yaml`

Main configuration file with comprehensive settings.

```yaml
scraping:
  sources:
    static:
      enabled: bool
      max_pages: int
      delay_range: [int, int]
    dynamic:
      enabled: bool
      max_pages: int
      search_terms: [str]
      headless: bool
    framework:
      enabled: bool
      max_pages: int
      search_terms: [str]
  protection:
    rate_limiting: bool
    user_agent_rotation: bool
    retry_attempts: int
    captcha_detection: bool
  advanced:
    proxy_rotation: bool
    session_management: bool
    javascript_execution: bool

analysis:
  auto_generate_reports: bool
  export_formats: [str]
  chart_generation: bool
  statistical_analysis: bool

database:
  type: str
  path: str
  optimization:
    enable_wal_mode: bool
    cache_size: int

logging:
  level: str
  file_logging:
    enabled: bool
    max_size_mb: int
```

## Type Definitions

### Common Types

```python
from typing import Dict, List, Any, Optional, Union

# Product data dictionary
ProductDict = Dict[str, Any]

# Configuration dictionary
ConfigDict = Dict[str, Any]

# Analysis result dictionary
AnalysisDict = Dict[str, Any]

# Database row
DbRow = Dict[str, Any]

# Search results
SearchResults = List[ProductDict]

# File paths
FilePath = Union[str, Path]
```

### Response Formats

#### Scraping Response
```python
{
    'name': str,
    'price': Optional[str],
    'link': Optional[str],
    'image': Optional[str],
    'availability': Optional[str],
    'search_term': str,
    'source': str,
    'scrape_time': str
}
```

#### Analysis Response
```python
{
    'total_records': int,
    'completeness': {
        'name_complete': float,
        'price_complete': float,
        'link_complete': float
    },
    'validity': {
        'valid_prices': int,
        'valid_links': int,
        'duplicate_products': int
    },
    'statistical_summaries': {
        'overall': {...},
        'by_source': {...}
    }
}
```

## Error Handling

### Exception Classes

```python
class ScrapingException(Exception):
    """Base exception for scraping operations"""
    pass

class NetworkException(ScrapingException):
    """Network-related errors"""
    pass

class ParsingException(ScrapingException):
    """Data parsing errors"""
    pass

class ValidationException(ScrapingException):
    """Data validation errors"""
    pass

class ConfigurationException(ScrapingException):
    """Configuration errors"""
    pass
```

### Error Response Format

```python
{
    'error_type': str,
    'error_message': str,
    'timestamp': str,
    'context': {
        'url': Optional[str],
        'search_term': Optional[str],
        'source': Optional[str]
    }
}
```

## Usage Examples

### Basic API Usage

```python
# Static scraping
from src.scrapers.static_scraper import StaticScraper
from src.utils.config import static_config

scraper = StaticScraper(static_config)
results = scraper.scrape()

# Database operations
from src.data.database import Database

with Database() as db:
    job_id = db.queue_job('search_term')
    db.insert_products(results, job_id)
    products = db.get_products(source='BooksToScrape')

# Analysis
from src.analysis.statistics import DataStatistics

stats = DataStatistics()
quality_report = stats.data_quality_checks()
summaries = stats.statistical_summaries()

# Report generation
from src.analysis.reports import ReportGenerator

reports = ReportGenerator()
report_path = reports.generate_comprehensive_report()
```

This API reference provides comprehensive documentation for all public interfaces in the Advanced Web Scraping Framework. For implementation details and examples, refer to the User Guide and source code documentation. 