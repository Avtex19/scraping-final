import scrapy
import json
import re
import time
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
    """Middleware to rotate User-Agent headers"""
    
    def __init__(self):
        self.ua = UserAgent()
    
    def process_request(self, request, spider):
        request.headers['User-Agent'] = self.ua.random
        return None


class AmazonAntiBlockMiddleware:
    """Middleware to handle Amazon's anti-bot measures"""
    
    def process_response(self, request, response, spider):
        # Check for common Amazon blocking patterns
        if any(pattern in response.text.lower() for pattern in [
            'captcha', 'robot', 'automated', 'blocked', 'unusual traffic'
        ]):
            spider.logger.warning(f"🛡️ Potential blocking detected on {request.url}")
            # Don't retry automatically, just log
            
        return response


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
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_DEBUG': True,
        'DOWNLOAD_TIMEOUT': 30,
        'LOG_LEVEL': 'WARNING',
        'ITEM_PIPELINES': {
            'src.scrapers.scrapy_crawler.amazon_spider.CollectorPipeline': 300,
        }
    }
    
    def __init__(self, search_terms=None, max_pages=1, job_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_terms = search_terms or ['laptop']
        self.max_pages = max_pages
        self.job_id = job_id
        self.custom_logger = setup_logger(f"{self.name}_logger", log_file='logs/amazon_scraper.log')
        # Clear global items at start
        global SCRAPED_ITEMS
        SCRAPED_ITEMS = []
    
    def start_requests(self):
        """Generate initial requests for Amazon search"""
        # Use the search URL that works (from test script)
        url = "https://www.amazon.com/s?k=laptop"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        self.custom_logger.info(f"🚀 Starting Amazon scraper for search")
        
        yield scrapy.Request(
            url=url,
            headers=headers,
            callback=self.parse,
            meta={'search_term': 'laptop', 'page': 1}
        )
    
    def parse(self, response):
        """Parse Amazon search results"""
        search_term = response.meta.get('search_term')
        page = response.meta.get('page', 1)
        
        self.custom_logger.info(f"📋 Parsing search results for '{search_term}' - Page {page}")
        self.custom_logger.info(f"📄 Response status: {response.status}")
        self.custom_logger.info(f"📏 Response length: {len(response.text)} characters")
        
        # Extract products using the working selectors
        products = self.extract_products(response, search_term)
        
        # Store items in global variable
        global SCRAPED_ITEMS
        SCRAPED_ITEMS.extend(products)
        
        self.custom_logger.info(f"✅ Extracted {len(products)} valid products for '{search_term}'")
        
        # Yield items for Scrapy pipeline
        for product in products:
            yield product
    
    def extract_products(self, response, search_term):
        """Extract products using the working selectors from test script"""
        products = []
        
        # Use the selector that worked in our test script
        containers = response.css('[data-component-type="s-search-result"]')
        self.custom_logger.info(f"🔍 Found {len(containers)} search result containers")
        
        for container in containers:
            product = self.extract_single_product(container, response.url, search_term)
            if product:
                products.append(product)
        
        return products
    
    def extract_single_product(self, container, page_url, search_term):
        """Extract individual product data using exact selectors from Amazon HTML"""
        try:
            # Use exact selectors from the provided HTML structure
            title_selectors = [
                '[data-cy="title-recipe"] h2 span::text',
                '[data-cy="title-recipe"] span::text',
                'h2 span::text'
            ]
            
            price_selectors = [
                '[data-cy="price-recipe"] .a-price .a-offscreen::text',
                '.a-price .a-offscreen::text',
                '[data-cy="price-recipe"] .a-color-price::text',
                '.a-price-whole::text'
            ]
            
            link_selectors = [
                '[data-cy="title-recipe"] a::attr(href)',
                'h2 a::attr(href)',
                '.a-link-normal::attr(href)'
            ]
            
            rating_selectors = [
                '[data-cy="reviews-block"] .a-icon-alt::text',
                '.a-icon-alt::text'
            ]
            
            # Extract title
            title = None
            for selector in title_selectors:
                title = container.css(selector).get()
                if title and title.strip():
                    title = title.strip()
                    break
            
            # Extract price
            price_text = None
            for selector in price_selectors:
                price_text = container.css(selector).get()
                if price_text and price_text.strip():
                    break
            
            # Extract link
            link = None
            for selector in link_selectors:
                link = container.css(selector).get()
                if link:
                    break
            
            # Extract rating
            rating = None
            for selector in rating_selectors:
                rating_element = container.css(selector).get()
                if rating_element and rating_element.strip():
                    rating = rating_element.strip()
                    break
            
            # Only include products with valid name (price might not always be available)
            if title:
                # Parse price if available, otherwise set to None
                price = self.parse_price(price_text) if price_text else None
                
                # Make link absolute
                if link and not link.startswith('http'):
                    link = f"https://www.amazon.com{link}"
                
                self.custom_logger.debug(f"✅ Extracted product: {title[:50]}...")
                
                return {
                    'name': title,
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
    
    def parse_price(self, price_str):
        """Parse price string to float"""
        if not price_str:
            return None
        try:
            # Remove currency symbols and commas
            clean_price = re.sub(r'[^\d.]', '', price_str)
            return float(clean_price) if clean_price else None
        except (ValueError, TypeError):
            return None 