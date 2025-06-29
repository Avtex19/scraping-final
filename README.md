# 🕷️ Advanced Web Scraping Framework

A comprehensive web scraping solution implementing three different scraping approaches with robust anti-bot measures, error handling, and database integration.

## 🎯 Core Requirements Fulfilled

✅ **3+ Different Websites** with varying structures:
- **BooksToScrape.com**: Static HTML content
- **eBay.com**: Dynamic JavaScript-heavy content  
- **Amazon.com**: Enterprise-level anti-bot protection

✅ **Multiple Scraping Technologies**:
- **BeautifulSoup4**: Static HTML parsing
- **Selenium WebDriver**: Dynamic content & JavaScript execution
- **Scrapy Framework**: Professional-grade scraping with middleware

✅ **Protection Mechanisms**:
- Rate limiting with random delays
- User-Agent rotation
- Captcha detection and handling
- Retry logic with exponential backoff

✅ **Multiple Data Formats**:
- HTML parsing with CSS selectors
- JSON API support ready
- Structured data normalization

✅ **Robust Error Handling**:
- Comprehensive exception handling
- Multi-level logging (file + console)
- Graceful degradation on failures

## 🏗️ Architecture Overview

```
scraping-final/
├── src/
│   ├── scrapers/
│   │   ├── base_scraper.py          # Abstract base class
│   │   ├── static_scraper.py        # BeautifulSoup4 implementation
│   │   ├── selenium_scraper.py      # Selenium WebDriver implementation
│   │   └── scrapy_amazon_scraper.py # Scrapy framework implementation
│   ├── data/
│   │   └── database.py              # SQLite database layer
│   └── utils/
│       ├── config.py                # Configuration management
│       ├── helpers.py               # Utility functions
│       └── logger.py                # Logging setup
├── logs/                            # Log files
├── main.py                          # Complete implementation
├── demo_main.py                     # Demonstration script
└── requirements.txt                 # Dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd scraping-final

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Demo

```bash
python demo_main.py
```

This will demonstrate all three scraping approaches and show comprehensive results.

## 📊 Scraping Implementations

### 1. Static Scraper (BeautifulSoup4)

**Target**: BooksToScrape.com
**Features**:
- CSS selector-based extraction
- Rate limiting with random delays
- Price sanitization
- URL normalization

```python
from src.scrapers.static_scraper import StaticScraper
from src.utils.config import static_config

scraper = StaticScraper(static_config)
results = scraper.scrape()
```

### 2. Dynamic Scraper (Selenium)

**Target**: eBay.com
**Features**:
- JavaScript execution
- Dynamic content loading
- Pagination handling
- Chrome WebDriver integration

```python
from src.scrapers.selenium_scraper import EbayScraper

with EbayScraper(headless=True) as scraper:
    results = scraper.scrape('laptop', max_pages=3)
```

### 3. Scrapy Framework

**Target**: Amazon.com
**Features**:
- Professional middleware pipeline
- Advanced anti-bot protection
- User-Agent rotation
- Retry mechanisms
- Captcha detection

```python
from src.scrapers.scrapy_amazon_scraper import AmazonScrapyRunner

runner = AmazonScrapyRunner()
results = runner.run_scraper(['laptop', 'smartphone'], max_pages=2)
```

## 🛡️ Anti-Bot Protection Features

### Rate Limiting
- Random delays between requests (1-2 seconds)
- Adaptive throttling based on response codes
- Concurrent request limiting

### User-Agent Rotation
- Multiple browser signatures
- Dynamic header generation
- Request fingerprint obfuscation

### Error Detection & Recovery
- HTTP status code monitoring (403, 429, 503)
- Captcha page detection
- Automatic retry with exponential backoff

### Advanced Middleware (Scrapy)
- Custom middleware pipeline
- Request/response interceptors
- Block detection algorithms

## 💾 Database Integration

### Schema
```sql
-- Job tracking
CREATE TABLE jobs (
    job_id INTEGER PRIMARY KEY,
    search_term TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT,
    completed_at TEXT
);

-- Product storage
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT,
    price REAL,
    link TEXT UNIQUE,
    image TEXT,
    availability TEXT,
    scrape_time TEXT,
    search_term TEXT,
    job_id INTEGER
);
```

### Usage
```python
from src.data.database import Database

with Database() as db:
    job_id = db.queue_job('search_term')
    db.insert_products(results, job_id=job_id)
    db.mark_job_complete(job_id)
```

## 📋 Configuration

### Static Scraper Config
```python
static_config = {
    'name': 'BooksToScrape',
    'base_url': 'http://books.toscrape.com/catalogue/page-{}.html',
    'start_page': 1,
    'max_pages': 3,
    'delay_range': (1, 2),
    'selectors': {
        'container': 'article.product_pod',
        'name': 'h3 a',
        'price': 'p.price_color',
        'link': 'h3 a',
        'image': 'img',
        'availability': 'p.instock.availability'
    }
}
```

### Scrapy Settings
```python
custom_settings = {
    'DOWNLOAD_DELAY': 2,
    'RANDOMIZE_DOWNLOAD_DELAY': True,
    'RETRY_TIMES': 3,
    'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
    'AUTOTHROTTLE_ENABLED': True,
    'CONCURRENT_REQUESTS': 1,
    # ... more settings
}
```

## 🔧 Extensibility

### Adding New Scrapers
1. Inherit from `BaseScraper`
2. Implement the `scrape()` method
3. Add to `__init__.py`

```python
from .base_scraper import BaseScraper

class NewScraper(BaseScraper):
    def scrape(self):
        # Implementation here
        pass
```

### Adding New Websites
1. Update configuration
2. Modify selectors
3. Test extraction logic

## 📈 Performance Metrics

From the demo run:
- **Static Scraper**: 60 books scraped successfully
- **Database**: All products stored with job tracking
- **Error Handling**: Graceful degradation on failures
- **Logging**: Comprehensive logging to files and console

## 🚨 Legal & Ethical Considerations

- Respects robots.txt files
- Implements reasonable rate limiting
- Follows website terms of service
- Only scrapes publicly available data
- Educational/research purposes

## 🛠️ Dependencies

- `requests`: HTTP client library
- `beautifulsoup4`: HTML parsing
- `selenium`: Web browser automation
- `scrapy`: Professional scraping framework
- `lxml`: XML/HTML processing
- `sqlite3`: Database (built-in)

## 📝 Logging

All scrapers generate detailed logs:
- `logs/static_scraper.log`
- `logs/ebay_scraper.log`  
- `logs/amazon_scraper.log`

Log levels: DEBUG, INFO, WARNING, ERROR

## 🎉 Demo Results

The demo successfully demonstrates:
- ✅ 60 books scraped from BooksToScrape
- ✅ Scrapy framework deployed and tested
- ✅ Database integration working
- ✅ All protection mechanisms active
- ✅ Comprehensive error handling
- ✅ Professional logging system

## 🔮 Future Enhancements

- Proxy rotation integration
- Cloud deployment (AWS/Docker)
- Real-time monitoring dashboard
- API endpoint exposure
- Advanced ML-based blocking detection

---

**Built with ❤️ for comprehensive web scraping education and research.** 