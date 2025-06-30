# Scrapy settings for Amazon scraping project
import random
import platform

BOT_NAME = 'amazon_scraper'

SPIDER_MODULES = ['src.scrapers.scrapy_crawler.amazon_spider']
NEWSPIDER_MODULE = 'src.scrapers.scrapy_crawler.amazon_spider'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure delays (more conservative for Amazon)
DOWNLOAD_DELAY = random.uniform(5, 10)
RANDOMIZE_DOWNLOAD_DELAY = True

# Configure concurrent requests
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Enable AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 20
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
AUTOTHROTTLE_DEBUG = False

# Override user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'

# Configure retry settings
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403, 404]

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = False

# macOS-specific SSL and network configurations
system = platform.system().lower()
if system == 'darwin':  # macOS
    # SSL configuration for macOS
    DOWNLOADER_CLIENT_TLS_METHOD = 'TLSv1.2'
    # Force IPv4 (sometimes macOS IPv6 causes issues)
    REACTOR_THREADPOOL_MAXSIZE = 20
    # Increase timeout for macOS network stack
    DOWNLOAD_TIMEOUT = 60
    # Use macOS-compatible DNS settings
    DNSCACHE_ENABLED = True
    DNSCACHE_SIZE = 10000
    DNS_TIMEOUT = 60

# Configure middlewares
DOWNLOADER_MIDDLEWARES = {
    'src.scrapers.scrapy_crawler.amazon_spider.RotateUserAgentMiddleware': 100,
    'src.scrapers.scrapy_crawler.amazon_spider.MacOSCompatibilityMiddleware': 150,
    'src.scrapers.scrapy_crawler.amazon_spider.DelayMiddleware': 200,
    'src.scrapers.scrapy_crawler.amazon_spider.AmazonAntiBlockMiddleware': 300,
}

# Configure item pipelines
ITEM_PIPELINES = {
    'src.scrapers.scrapy_crawler.amazon_spider.CollectorPipeline': 300,
}

# Configure logging
LOG_LEVEL = 'WARNING'

# Enable cookies
COOKIES_ENABLED = True

# Configure timeouts
DOWNLOAD_TIMEOUT = 45

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Set request fingerprinter implementation
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7' 