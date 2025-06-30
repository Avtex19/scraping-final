import scrapy
import json
import re
import time
import random
from scrapy.http import Request
from scrapy.exceptions import IgnoreRequest
from urllib.parse import urljoin
from datetime import datetime
import logging
import os
import sys
from fake_useragent import UserAgent
from scrapy.utils.project import get_project_settings
from src.utils.logger import setup_logger

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.data.database import Database


class RotateUserAgentMiddleware:
    """Advanced middleware to rotate User-Agent headers with realistic patterns"""
    
    def __init__(self):
        # Use a mix of popular browsers with realistic distribution across platforms
        # Prioritize macOS user agents for better compatibility on macOS systems
        self.user_agents = [
            # macOS Safari (most common on macOS)
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            
            # macOS Chrome (very common)
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # macOS Firefox
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/118.0',
            
            # Windows (for diversity)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            
            # Linux Chrome (improved representation)
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        ]
    
    def process_request(self, request, spider):
        # Rotate user agent for each request
        request.headers['User-Agent'] = random.choice(self.user_agents)
        
        # Add realistic browser headers
        request.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-US,en;q=0.8,es;q=0.7',
                'en-GB,en;q=0.9',
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
        return None


class AmazonAntiBlockMiddleware:
    """Enhanced middleware to handle Amazon's anti-bot measures"""
    
    def process_response(self, request, response, spider):
        # Check for common Amazon blocking patterns
        blocking_patterns = [
            'captcha', 'robot', 'automated', 'blocked', 'unusual traffic',
            'request blocked', 'access denied', 'temporarily blocked'
        ]
        
        response_text_lower = response.text.lower()
        if any(pattern in response_text_lower for pattern in blocking_patterns):
            spider.logger.warning(f"🛡️ Potential blocking detected on {request.url}")
            
        # Check for successful product page indicators
        if '[data-component-type="s-search-result"]' in response.text:
            spider.logger.debug(f"✅ Valid product page detected")
        elif response.status == 200:
            spider.logger.warning(f"⚠️ Page loaded but no products found - possible blocking")
            
        return response


class MacOSCompatibilityMiddleware:
    """macOS-specific middleware to handle common networking issues"""
    
    def __init__(self):
        import platform
        self.is_macos = platform.system().lower() == 'darwin'
        
    def process_request(self, request, spider):
        if self.is_macos:
            # Add macOS-specific headers that work better with Amazon
            request.headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-GPC': '1',  # Global Privacy Control (common on macOS)
            })
        return None
    
    def process_response(self, request, response, spider):
        if self.is_macos and response.status in [403, 503]:
            spider.logger.warning(f"🍎 macOS network issue detected: {response.status} on {request.url}")
            spider.logger.info("💡 macOS troubleshooting tips:")
            spider.logger.info("   1. Check if VPN/proxy is interfering")
            spider.logger.info("   2. Try disabling IPv6: sudo networksetup -setv6off Wi-Fi")
            spider.logger.info("   3. Clear DNS cache: sudo dscacheutil -flushcache")
            spider.logger.info("   4. Check macOS firewall settings")
            
        return response


class DelayMiddleware:
    """Middleware to add realistic, variable delays between requests"""
    
    def process_request(self, request, spider):
        # Add random delay between 3-8 seconds to mimic human behavior
        delay = random.uniform(3, 8)
        spider.logger.debug(f"⏰ Adding {delay:.2f}s delay before request")
        time.sleep(delay)
        return None


# Global variable to store scraped items (simple approach)
SCRAPED_ITEMS = []


class CollectorPipeline:
    """Pipeline to collect scraped items via file system"""
    
    def __init__(self):
        self.items_file = 'temp_scraped_items.json'
        # Clear any existing items
        with open(self.items_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    def process_item(self, item, spider):
        # Load existing items
        try:
            with open(self.items_file, 'r', encoding='utf-8') as f:
                items = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            items = []
        
        # Add new item
        items.append(dict(item))
        
        # Save back to file
        with open(self.items_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        
        spider.custom_logger.debug(f"🔗 Pipeline collected item #{len(items)}: {item.get('name', 'Unknown')[:30]}...")
        return item


class AmazonProductSpider(scrapy.Spider):
    name = 'amazon_products'
    allowed_domains = ['amazon.com']
    
    custom_settings = {
        'DOWNLOAD_DELAY': random.uniform(4, 7),  # More realistic delay
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'RETRY_TIMES': 2,  # Reduced retries to avoid detection
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 5,  # Start with longer delay
        'AUTOTHROTTLE_MAX_DELAY': 15,   # Allow longer delays
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,
        'DOWNLOAD_TIMEOUT': 45,  # Longer timeout
        'LOG_LEVEL': 'WARNING',
        'DOWNLOADER_MIDDLEWARES': {
            'src.scrapers.scrapy_crawler.amazon_spider.RotateUserAgentMiddleware': 100,
            'src.scrapers.scrapy_crawler.amazon_spider.MacOSCompatibilityMiddleware': 150,
            'src.scrapers.scrapy_crawler.amazon_spider.DelayMiddleware': 200,
            'src.scrapers.scrapy_crawler.amazon_spider.AmazonAntiBlockMiddleware': 300,
        },
        'ITEM_PIPELINES': {
            'src.scrapers.scrapy_crawler.amazon_spider.CollectorPipeline': 300,
        },
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': False,  # Disable robots.txt for educational purposes
    }
    
    def __init__(self, search_terms=None, max_pages=1, job_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_terms = search_terms or ['laptop']
        self.max_pages = max_pages
        self.job_id = job_id
        self.custom_logger = setup_logger(f"{self.name}_logger", log_file='../logs/amazon_scraper.log')
        # Clear global items at start
        global SCRAPED_ITEMS
        SCRAPED_ITEMS = []
    
    def start_requests(self):
        """Generate initial requests for Amazon search with multiple strategies"""
        self.custom_logger.info(f"🚀 Starting Amazon scraper for search")
        
        for search_term in self.search_terms:
            # Try multiple URL patterns to find what works
            urls = [
                f"https://www.amazon.com/s?k={search_term}&ref=sr_pg_1",
                f"https://www.amazon.com/s?k={search_term}",
                f"https://www.amazon.com/s?field-keywords={search_term}",
            ]
            
            for i, url in enumerate(urls):
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    meta={
                        'search_term': search_term, 
                        'page': 1,
                        'url_variant': i
                    },
                    dont_filter=True,  # Allow duplicate URLs for testing
                    priority=10 - i  # Try different URL patterns with different priorities
                )
    
    def parse(self, response):
        """Parse Amazon search results with enhanced extraction"""
        search_term = response.meta.get('search_term')
        page = response.meta.get('page', 1)
        url_variant = response.meta.get('url_variant', 0)
        
        self.custom_logger.info(f"📋 Parsing search results for '{search_term}' - Page {page} (URL variant {url_variant})")
        self.custom_logger.info(f"📄 Response status: {response.status}")
        self.custom_logger.info(f"📏 Response length: {len(response.text)} characters")
        
        # Extract products using multiple strategies
        products = self.extract_products_enhanced(response, search_term)
        
        if products:
            # Store items in global variable
            global SCRAPED_ITEMS
            SCRAPED_ITEMS.extend(products)
            
            self.custom_logger.info(f"✅ Extracted {len(products)} valid products for '{search_term}'")
            
            # Yield items for Scrapy pipeline
            for product in products:
                yield product
                
            # Try to get next page if we have max_pages > 1
            if page < self.max_pages:
                next_page_url = self.get_next_page_url(response, search_term, page + 1)
                if next_page_url:
                    yield scrapy.Request(
                        url=next_page_url,
                        callback=self.parse,
                        meta={'search_term': search_term, 'page': page + 1}
                    )
        else:
            self.custom_logger.warning(f"⚠️ No products extracted from {response.url}")
    
    def get_next_page_url(self, response, search_term, page_num):
        """Generate next page URL"""
        return f"https://www.amazon.com/s?k={search_term}&page={page_num}"
    
    def extract_products_enhanced(self, response, search_term):
        """Enhanced product extraction with multiple selector strategies"""
        products = []
        
        # Try multiple container selectors
        container_selectors = [
            '[data-component-type="s-search-result"]',
            '.s-result-item[data-component-type="s-search-result"]',
            '.s-result-item',
            '.sg-col-inner .s-widget-container'
        ]
        
        containers = []
        for selector in container_selectors:
            containers = response.css(selector)
            if containers:
                self.custom_logger.info(f"🔍 Found {len(containers)} containers using selector: {selector}")
                break
        
        if not containers:
            self.custom_logger.warning(f"❌ No product containers found with any selector")
            return products
        
        for i, container in enumerate(containers):
            if i >= 25:  # Limit to avoid overwhelming Amazon
                break
                
            product = self.extract_single_product_enhanced(container, response.url, search_term)
            if product:
                products.append(product)
        
        return products
    
    def extract_single_product_enhanced(self, container, page_url, search_term):
        """Enhanced single product extraction with multiple fallback strategies"""
        try:
            # Enhanced title selectors
            title_selectors = [
                '[data-cy="title-recipe"] h2 span::text',
                '[data-cy="title-recipe"] span::text',
                'h2 a span::text',
                'h2 span::text',
                '.s-size-mini .s-color-base::text',
                '.a-size-base-plus::text'
            ]
            
            # Enhanced price selectors
            price_selectors = [
                '[data-cy="price-recipe"] .a-price .a-offscreen::text',
                '.a-price .a-offscreen::text',
                '[data-cy="price-recipe"] .a-color-price::text',
                '.a-price-whole::text',
                '.a-color-price::text',
                '.a-price-symbol + .a-price-whole::text'
            ]
            
            # Enhanced link selectors
            link_selectors = [
                '[data-cy="title-recipe"] a::attr(href)',
                'h2 a::attr(href)',
                '.a-link-normal::attr(href)',
                'a.s-link-style::attr(href)'
            ]
            
            # Extract with fallbacks
            title = self.extract_with_fallbacks(container, title_selectors)
            price_text = self.extract_with_fallbacks(container, price_selectors)
            link = self.extract_with_fallbacks(container, link_selectors)
            
            # Extract rating
            rating = container.css('.a-icon-alt::text').get()
            if rating:
                rating = rating.strip()
            
            # Only include products with valid name
            if title and title.strip():
                # Parse price if available
                price = self.parse_price(price_text) if price_text else None
                
                # Make link absolute
                if link and not link.startswith('http'):
                    link = f"https://www.amazon.com{link}"
                
                self.custom_logger.debug(f"✅ Extracted product: {title[:50]}...")
                
                return {
                    'name': title.strip(),
                    'price': price,
                    'link': link,
                    'search_term': search_term,
                    'scrape_time': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'availability': 'In Stock',
                    'rating': rating,
                    'source': 'Amazon'
                }
            else:
                self.custom_logger.debug(f"❌ Missing title for product")
                
        except Exception as e:
            self.custom_logger.debug(f"❌ Error extracting product: {e}")
        
        return None
    
    def extract_with_fallbacks(self, container, selectors):
        """Try multiple selectors until one works"""
        for selector in selectors:
            result = container.css(selector).get()
            if result and result.strip():
                return result.strip()
        return None
    
    def parse_price(self, price_str):
        """Enhanced price parsing"""
        if not price_str:
            return None
        try:
            # Remove currency symbols and commas, keep numbers and decimals
            clean_price = re.sub(r'[^\d.]', '', price_str)
            if clean_price and '.' in clean_price:
                return float(clean_price)
            elif clean_price:
                return float(clean_price)
            return None
        except (ValueError, TypeError):
            return None 