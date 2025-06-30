# Technical Architecture Document

## Overview

The Advanced Web Scraping Framework is a comprehensive, production-ready data collection system designed to extract product information from diverse e-commerce platforms. The architecture implements multiple scraping methodologies, robust anti-bot protection, and advanced data processing capabilities while maintaining scalability, reliability, and maintainability.

## System Architecture

### High-Level Architecture

The system follows a modular, layered architecture pattern that separates concerns and promotes code reusability:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   CLI Interface │    │  HTML Reports   │                │
│  │(src/cli/interface)  │  (reports.py)   │                │
│  └─────────────────┘    └─────────────────┘                │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │ Data Processing │ │    Analysis     │ │ Configuration │ │
│  │ (processors.py) │ │(statistics.py)  │ │(src/cli/      │ │
│  │                 │ │                 │ │commands.py)   │ │
│  └─────────────────┘ └─────────────────┘ └───────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Data Access Layer                        │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │   Database      │ │   File System   │ │    Models     │ │
│  │ (database.py)   │ │   Operations    │ │ (models.py)   │ │
│  └─────────────────┘ └─────────────────┘ └───────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Scraping Engine Layer                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐ │
│  │ Static Scraper  │ │Dynamic Scraper  │ │Enhanced       │ │
│  │(BeautifulSoup4) │ │   (Selenium)    │ │Framework      │ │
│  │                 │ │                 │ │(Scrapy+Config)│ │
│  └─────────────────┘ └─────────────────┘ └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Core Design Patterns

#### 1. Strategy Pattern
The scraping engine implements the Strategy pattern to support multiple scraping approaches:

- **Static Strategy**: BeautifulSoup4 for simple HTML parsing
- **Dynamic Strategy**: Selenium WebDriver for JavaScript-heavy sites
- **Framework Strategy**: Scrapy for enterprise-level scraping

Each strategy inherits from `BaseScraper` abstract base class, ensuring consistent interface while allowing specialized implementations.

#### 2. Factory Pattern
The system uses Factory patterns for creating standardized objects:

- **Product Factory**: `create_product_from_scraped_data()` creates Product instances from raw scraped data
- **Configuration Factory**: Generates default configurations for different scraping scenarios
- **Analysis Factory**: `create_analysis_result()` creates standardized analysis result objects

#### 3. Repository Pattern
The `Database` class implements the Repository pattern, providing a clean abstraction over data persistence:

```python
class Database:
    def insert_products(self, products: List[Dict], job_id: int)
    def get_products(self, filters: Dict) -> List[Product]
    def queue_job(self, search_term: str) -> int
```

#### 4. Command Pattern
The CLI system uses the Command pattern through the `CommandProcessor` class, encapsulating operations as objects that can be queued, logged, and executed.

#### 5. Observer Pattern
Implemented through the logging system and progress tracking, where multiple observers (file loggers, console loggers, progress bars) can monitor scraping operations.

## Data Flow Architecture

### 1. Scraping Pipeline

```
User Input → Configuration Loading → Scraper Selection → 
Data Extraction → Data Validation → Database Storage → 
Analysis Processing → Report Generation
```

#### Detailed Flow:
1. **Initialization**: Load YAML configuration and initialize database connections
2. **Job Queuing**: Create job entries in the database for tracking
3. **Scraper Dispatch**: Select appropriate scraper based on target website
4. **Data Extraction**: Execute scraping with anti-bot protection
5. **Data Processing**: Clean, validate, and normalize extracted data
6. **Persistence**: Store processed data in SQLite database
7. **Analysis**: Generate statistical summaries and trend analysis
8. **Reporting**: Create HTML reports and export data in multiple formats

### 2. Concurrent Processing

The system implements multiprocessing for improved performance:

```python
with ProcessPoolExecutor(max_workers=3) as executor:
    future_to_term = {
        executor.submit(scrape_func, term): term 
        for term in search_terms
    }
```

Each process operates independently with:
- Isolated WebDriver instances (Selenium)
- Separate logging queues (multiprocessing-safe)
- Individual error handling and retry mechanisms

## Anti-Bot Protection Architecture

### Multi-Layer Defense System

#### Layer 1: Request-Level Protection
- **Rate Limiting**: Random delays (1-5 seconds) between requests
- **User-Agent Rotation**: Dynamic browser signature switching
- **Header Randomization**: Varied request headers to mimic human behavior

#### Layer 2: Session Management
- **Cookie Persistence**: Maintain session state across requests
- **Request Patterns**: Randomized browsing patterns
- **Connection Reuse**: Efficient connection pooling

#### Layer 3: Detection and Recovery
- **Response Analysis**: HTTP status code monitoring (403, 429, 503)
- **Content Analysis**: CAPTCHA and block page detection
- **Adaptive Backoff**: Exponential retry delays with jitter

#### Layer 4: Scrapy Middleware (Advanced)
```python
class AmazonAntiBlockMiddleware:
    def process_response(self, request, response, spider):
        if self.detect_blocking(response):
            spider.logger.warning("Blocking detected")
            return self.handle_block(request, response)
```

## Database Design

### Schema Architecture

The database uses a normalized schema optimized for analytical queries:

```sql
-- Job Tracking Table
jobs (
    job_id INTEGER PRIMARY KEY,
    search_term TEXT,
    status TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
)

-- Product Storage Table  
products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price REAL,
    link TEXT UNIQUE,
    image TEXT,
    availability TEXT,
    scrape_time TIMESTAMP,
    search_term TEXT,
    source TEXT,
    job_id INTEGER FOREIGN KEY
)
```

### Indexing Strategy
- **Primary Indexes**: On job_id and product id for fast lookups
- **Composite Indexes**: On (source, search_term) for analytical queries
- **Unique Constraints**: On product links to prevent duplicates

## Configuration Management

### Hierarchical Configuration System

The system uses YAML-based configuration with override capabilities:

```yaml
scraping:
  sources:
    static: {enabled: true, max_pages: 3}
    dynamic: {enabled: true, search_terms: [...]}
    framework: {enabled: true, concurrent_requests: 1}
  protection:
    rate_limiting: true
    user_agent_rotation: true
    retry_attempts: 3
```

### Enhanced Scrapy Configuration

The framework includes a sophisticated Scrapy configuration system:

**Project Structure:**
- `scrapy.cfg`: Project configuration pointing to `src.scrapers.scrapy_crawler.settings`
- `src/scrapers/scrapy_crawler/settings.py`: Comprehensive Scrapy settings
- Custom middlewares for advanced anti-bot protection

**Key Scrapy Settings:**
```python
# Enhanced anti-bot configuration
DOWNLOAD_DELAY = random.uniform(5, 10)  # Human-like delays
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 20

# Custom middleware stack
DOWNLOADER_MIDDLEWARES = {
    'src.scrapers.scrapy_crawler.amazon_spider.RotateUserAgentMiddleware': 100,
    'src.scrapers.scrapy_crawler.amazon_spider.DelayMiddleware': 200,
    'src.scrapers.scrapy_crawler.amazon_spider.AmazonAntiBlockMiddleware': 300,
}
```

Configuration precedence:
1. Command-line arguments (highest)
2. Environment variables
3. YAML configuration files
4. Scrapy settings.py
5. Default values (lowest)

## Error Handling and Resilience

### Exception Hierarchy
```python
ScrapingException
├── NetworkException
├── ParsingException
├── ValidationException
└── ConfigurationException
```

### Resilience Patterns
- **Circuit Breaker**: Temporarily stop requests to failing sources
- **Retry with Backoff**: Exponential delays for transient failures
- **Graceful Degradation**: Continue processing other sources if one fails
- **Dead Letter Queue**: Store failed jobs for manual inspection

## Performance Considerations

### Optimization Strategies
1. **Connection Pooling**: Reuse HTTP connections
2. **Memory Management**: Streaming data processing for large datasets
3. **Caching**: Request response caching with TTL
4. **Parallel Processing**: Multi-process and multi-threaded execution

### Resource Management
- **Memory Limits**: Configurable memory usage caps
- **CPU Throttling**: Adaptive CPU usage based on system load
- **Disk Space**: Automatic cleanup of old log files and temporary data

## Security and Compliance

### Data Privacy
- **No Personal Data**: System excludes personal information by design
- **Anonymization**: Optional data anonymization features
- **GDPR Compliance**: Data retention and deletion policies

### Ethical Scraping
- **robots.txt Compliance**: Respects website policies
- **Rate Limiting**: Prevents server overload
- **Attribution**: Includes data source attribution in reports

## Scalability Architecture

### Horizontal Scaling
The system is designed for horizontal scaling:
- **Stateless Workers**: Scraping processes maintain no shared state
- **Database Sharding**: Support for multiple database instances
- **Load Balancing**: Request distribution across worker processes

### Vertical Scaling
- **Multi-threading**: Thread-safe operations where appropriate
- **Memory Optimization**: Efficient memory usage patterns
- **CPU Utilization**: Configurable worker process counts

## Monitoring and Observability

### Logging Architecture
- **Structured Logging**: JSON-formatted logs for analysis
- **Log Levels**: DEBUG, INFO, WARNING, ERROR for different scenarios
- **Log Aggregation**: Centralized logging with multiprocessing support

### Metrics Collection
- **Performance Metrics**: Response times, success rates, error counts
- **Business Metrics**: Products scraped, data quality scores
- **System Metrics**: Memory usage, CPU utilization, disk space

This architecture provides a robust, scalable foundation for web scraping operations while maintaining high code quality, performance, and reliability standards. 