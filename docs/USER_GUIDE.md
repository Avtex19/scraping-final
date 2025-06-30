# User Guide - Advanced Web Scraping Framework

## Table of Contents
1. [Quick Start](#quick-start)
2. [Installation Guide](#installation-guide)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [CLI Interface](#cli-interface)
6. [Data Analysis](#data-analysis)
7. [Export Options](#export-options)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd scraping-final
pip install -r requirements.txt
```

### 2. Run Demo
```bash
python demo_main.py
```
This demonstrates all three scraping approaches with sample data.

### 3. Interactive CLI
```bash
# From project root
python -m src.cli.interface interactive

# Or navigate to src directory first
cd src
python -m cli.interface interactive
```
Access the full-featured command-line interface with enhanced Amazon scraping capabilities.

## Installation Guide

### Prerequisites
- Python 3.8 or higher
- Chrome browser (for Selenium)
- 4GB+ RAM (recommended)

### Step-by-Step Installation

#### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. ChromeDriver Setup
Download ChromeDriver from [chromedriver.chromium.org](https://chromedriver.chromium.org) and:
- Place in project directory, or
- Add to system PATH, or
- Update `chromedriver_path` in configuration

#### 4. Verify Installation
```bash
# Test basic functionality
python main.py

# Test interactive CLI
python -m src.cli.interface

# Test individual scrapers
cd src
python -c "from scrapers.static_scraper import StaticScraper; print('✅ Static scraper ready')"
python -c "from scrapers.selenium_scraper import EbayScraper; print('✅ Selenium scraper ready')"
python -c "from scrapers.scrapy_crawler.amazon_scraper import AmazonScrapyRunner; print('✅ Enhanced Amazon scraper ready')"
```

## Configuration

### Main Configuration File: `config/settings.yaml`

```yaml
# Core scraping settings
scraping:
  sources:
    static:
      enabled: true
      max_pages: 3
      delay_range: [1, 2]
    
    dynamic:
      enabled: true
      max_pages: 2
      search_terms: ["iphone", "laptop"]
      headless: true
    
    framework:
      enabled: true
      max_pages: 1
      search_terms: ["laptop"]
      
  protection:
    rate_limiting: true
    user_agent_rotation: true
    retry_attempts: 3
```

### Environment Variables
```bash
export SCRAPING_DB_PATH="custom_database.db"
export CHROMEDRIVER_PATH="/path/to/chromedriver"
export LOG_LEVEL="INFO"
```

## Usage Examples

### Example 1: Static Scraping (BooksToScrape)

```python
from src.scrapers.static_scraper import StaticScraper
from src.utils.config import static_config

# Initialize scraper
scraper = StaticScraper(static_config)

# Run scraping
results = scraper.scrape()

print(f"Scraped {len(results)} books")
for book in results[:3]:
    print(f"- {book['name']}: £{book['price']}")
```

**Output:**
```
Scraped 60 books
- A Light in the Attic: £51.77
- Tipping the Velvet: £53.74
- Soumission: £50.10
```

### Example 2: Dynamic Scraping (eBay)

```python
from src.scrapers.selenium_scraper import EbayScraper

# Use context manager for automatic cleanup
with EbayScraper(headless=True, timeout=10) as scraper:
    results = scraper.scrape('macbook', max_pages=2)
    
    print(f"Found {len(results)} MacBook listings")
    for item in results[:5]:
        print(f"- {item['name']}: {item['price']}")
```

**Output:**
```
Found 124 MacBook listings
- MacBook Pro 16-inch M1 Max: $2,499.00
- MacBook Air 13-inch M2: $1,199.00
- MacBook Pro 14-inch Space Gray: $1,999.00
```

### Example 3: Enhanced Framework Scraping (Amazon with Advanced Anti-Bot Protection)

```python
from src.scrapers.scrapy_crawler.amazon_scraper import AmazonScrapyRunner

# Initialize runner with enhanced anti-bot protection
runner = AmazonScrapyRunner()

# Run with sophisticated anti-detection strategies:
# - Advanced user agent rotation (7 realistic browser signatures)
# - Variable delays (5-10 seconds) with human-like patterns  
# - Multiple URL strategy attempts
# - Enhanced session management with cookies
# - Intelligent blocking detection and graceful handling
results = runner.run_scraper(['laptop'], max_pages=1)

print(f"Amazon results: {len(results)} products")
if results:
    for product in results[:3]:
        print(f"- {product['name']}: {product['price']}")
    print("✅ Successfully bypassed basic anti-bot measures!")
else:
    print("🛡️ Amazon blocked access (demonstrates advanced protection)")
    print("💡 This is normal - Amazon has enterprise-level defenses")
    print("📋 Try eBay or Static scrapers for reliable demos")
```

**Note**: The enhanced Amazon scraper now includes sophisticated anti-bot protection but Amazon's defenses are very advanced. Success rates vary, and blocking is normal behavior that demonstrates the framework's proper error handling.

### Example 4: Batch Processing Multiple Terms

```python
from src.data.database import Database
from src.scrapers.selenium_scraper import EbayScraper

search_terms = ['iphone 15', 'samsung galaxy', 'pixel 8']

with Database() as db, EbayScraper() as scraper:
    for term in search_terms:
        print(f"Scraping: {term}")
        
        # Create job tracking
        job_id = db.queue_job(term)
        
        # Scrape data
        results = scraper.scrape(term, max_pages=1)
        
        # Add metadata
        for result in results:
            result['search_term'] = term
            result['source'] = 'eBay'
        
        # Save to database
        db.insert_products(results, job_id)
        db.mark_job_complete(job_id)
        
        print(f"  ✅ Saved {len(results)} items")
```

### Example 5: Data Analysis and Reporting

```python
from src.analysis import DataStatistics, ReportGenerator

# Load and analyze data
stats = DataStatistics()
quality_report = stats.data_quality_checks()
summaries = stats.statistical_summaries()

print(f"Total products: {quality_report['total_records']}")
print(f"Price data completeness: {quality_report['completeness']['price_complete']:.1f}%")

# Generate comprehensive report
reports = ReportGenerator()
report_path = reports.generate_comprehensive_report()
print(f"Report generated: {report_path}")
```

## CLI Interface

### Main Menu Navigation

```bash
python -m src.cli.interface
```

**Available Options:**
```
🕷️ ADVANCED WEB SCRAPING FRAMEWORK
═══════════════════════════════════════════════════

1. 🚀 Run Comprehensive Scraping
2. 📊 View Data Analysis
3. 📈 Generate Reports
4. 🔍 Search & Filter Data
5. 💾 Data Export Options
6. ⚙️ Configuration Management
7. 🧪 Run Tests
8. ❓ Help & Documentation
9. 🚪 Exit

Select option (1-9):
```

### Comprehensive Scraping

**Option 1**: Runs all scraping sources automatically:
- Static scraping (BooksToScrape)
- Dynamic scraping (eBay)
- Framework scraping (Amazon)

**Features:**
- Real-time progress tracking
- Automatic error handling
- Database integration
- Performance metrics

### Data Analysis

**Option 2**: Interactive data analysis:
```
📊 DATA ANALYSIS OPTIONS
─────────────────────────

1. 📈 Statistical Summary
2. 🔍 Data Quality Report
3. 📊 Price Analysis
4. 📈 Trend Analysis
5. 🆚 Source Comparison
6. 📤 Export Analysis
```

### Report Generation

**Option 3**: Generate professional reports:
- **Comprehensive Report**: Full analysis with charts
- **Statistical Report**: Focus on data statistics
- **Trend Report**: Time-based analysis
- **Custom Report**: Configurable report options

## Data Analysis

### Statistical Analysis

```python
from src.analysis.statistics import DataStatistics

stats = DataStatistics()

# Data quality assessment
quality = stats.data_quality_checks()
print(f"Data completeness: {quality['completeness']}")

# Statistical summaries
summaries = stats.statistical_summaries()
for source, data in summaries['by_source'].items():
    print(f"{source}: {data['total_products']} products, avg price: ${data['avg_price']:.2f}")

# Price analysis with outlier detection
price_analysis = stats.generate_price_analysis()
print(f"Outliers detected: {len(price_analysis['outliers'])}")
```

### Trend Analysis

```python
from src.analysis.trends import TrendAnalyzer

trends = TrendAnalyzer()

# Price trends over time
trend_report = trends.analyze_price_trends()
print(f"Price trend direction: {trend_report['overall_trends']['trend_direction']}")

# Cross-source comparison
comparison = trends.comparative_source_analysis()
cheapest = comparison['cross_source_insights']['cheapest_source']
print(f"Cheapest source: {cheapest}")

# Generate visualizations
charts = trends.generate_trend_visualizations()
print(f"Generated {len(charts)} trend charts")
```

## Export Options

### Multiple Format Export

```python
from src.analysis.reports import ReportGenerator

reports = ReportGenerator()

# Export in all formats
exported_files = reports.export_data_formats()
for format_type, file_path in exported_files.items():
    print(f"{format_type.upper()}: {file_path}")
```

**Available Formats:**
- **CSV**: Spreadsheet-compatible format
- **JSON**: Machine-readable format
- **Excel**: Multi-sheet workbooks with source separation
- **HTML**: Interactive reports with charts

### Custom Export Configuration

```python
# CLI custom export example
python -m src.cli.interface
# → Select option 5 (Data Export)
# → Select option 5 (Custom Export Configuration)
```

**Custom Options:**
- Select specific data fields
- Apply date range filters
- Filter by source
- Choose output format
- Configure file naming

## Troubleshooting

### Common Issues

#### 1. ChromeDriver Issues
**Problem**: `WebDriverException: 'chromedriver' executable needs to be in PATH`

**Solution:**
```bash
# Download ChromeDriver for your Chrome version
# Update configuration:
export CHROMEDRIVER_PATH="/path/to/chromedriver"
```

#### 2. Network Timeout
**Problem**: Requests timing out on slow connections

**Solution:**
```yaml
# In config/settings.yaml
scraping:
  sources:
    dynamic:
      timeout: 30  # Increase timeout
```

#### 3. Memory Issues
**Problem**: High memory usage during large scraping operations

**Solution:**
```yaml
# Reduce concurrent operations
scraping:
  protection:
    max_concurrent_requests: 2
```

#### 4. Database Locked
**Problem**: `database is locked` error

**Solution:**
```python
# Ensure proper database context management
with Database() as db:
    # Perform operations here
    pass  # Database automatically closed
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
export LOG_LEVEL="DEBUG"
python demo_main.py
```

## Best Practices

### 1. Ethical Scraping
- Always check `robots.txt` before scraping
- Respect rate limits and server capacity
- Use appropriate delays between requests
- Don't scrape personal or sensitive data

### 2. Performance Optimization
- Use multiprocessing for independent operations
- Implement proper connection pooling
- Cache frequently accessed data
- Monitor memory usage for large datasets

### 3. Error Handling
- Always use context managers for resources
- Implement retry logic for transient failures
- Log errors with sufficient context
- Gracefully handle anti-bot measures

### 4. Data Quality
- Validate scraped data before storage
- Implement deduplication logic
- Regular data quality assessments
- Clean and normalize price data

### 5. Configuration Management
- Use environment-specific configurations
- Version control configuration files
- Document configuration changes
- Test configuration changes in isolation

### 6. Security
- Don't hardcode credentials
- Use environment variables for sensitive data
- Regular security updates for dependencies
- Monitor for data breaches or leaks

## Advanced Usage

### Custom Scrapers

Create custom scrapers by extending `BaseScraper`:

```python
from src.scrapers.base_scraper import BaseScraper

class CustomScraper(BaseScraper):
    def scrape(self):
        # Implement custom scraping logic
        return results
```

### Custom Data Processors

Extend data processing capabilities:

```python
from src.data.processors import DataProcessor

class CustomProcessor(DataProcessor):
    def custom_transformation(self, data):
        # Implement custom data transformation
        return processed_data
```

### Custom Analysis

Create custom analysis modules:

```python
from src.analysis.statistics import DataStatistics

class CustomAnalyzer(DataStatistics):
    def custom_analysis(self):
        # Implement custom analysis logic
        return analysis_results
```

This guide provides comprehensive coverage of the framework's capabilities. For additional help, consult the API reference documentation or check the troubleshooting section. 