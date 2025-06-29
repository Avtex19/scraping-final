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

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.data.database import Database
from src.utils.logger import setup_logger


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
        'LOG_LEVEL': 'WARNING'
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
        """Generate initial requests for Amazon laptop page"""
        # Use the specific laptop URL you provided
        url = "https://www.amazon.com/Notebooks-Laptop-Computers/b?ie=UTF8&node=565108"
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        self.custom_logger.info(f"🚀 Starting Amazon scraper for laptop products")
        
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
        
        # Extract products using our proven selectors
        products = self.extract_products(response, search_term)
        
        # Store items in global variable
        global SCRAPED_ITEMS
        SCRAPED_ITEMS.extend(products)
        
        self.custom_logger.info(f"✅ Extracted {len(products)} valid products for '{search_term}'")
        
        # Yield items for Scrapy pipeline
        for product in products:
            yield product
    
    def extract_products(self, response, search_term):
        """Extract products using the selectors that worked"""
        products = []
        
        # Use our proven container selector
        containers = response.css('.a-section.a-spacing-base')
        self.custom_logger.debug(f"🔍 Found {len(containers)} product containers")
        
        for container in containers:
            product = self.extract_single_product(container, response.url, search_term)
            if product:
                products.append(product)
        
        return products
    
    def extract_single_product(self, container, page_url, search_term):
        """Extract individual product data"""
        try:
            # Product name using our proven selectors
            name_selectors = [
                '[data-cy="title-recipe"] h2 span::text',
                '.s-line-clamp-1 h2 span::text',
                'h2 span::text'
            ]
            name = self.extract_text_with_fallbacks(container, name_selectors)
            
            # Price using our proven selectors
            price_selectors = [
                '[data-cy="price-recipe"] .a-price .a-offscreen::text',
                '.a-price .a-offscreen::text'
            ]
            price_text = self.extract_text_with_fallbacks(container, price_selectors)
            
            # Product link
            link_selectors = [
                '[data-cy="title-recipe"] a::attr(href)',
                '.s-line-clamp-1::attr(href)',
                'h2 a::attr(href)'
            ]
            link = self.extract_text_with_fallbacks(container, link_selectors)
            
            # Only include products with valid name and price
            if name and price_text:
                price = self.parse_price(price_text)
                
                # Make link absolute
                if link and not link.startswith('http'):
                    link = f"https://www.amazon.com{link}"
                
                return {
                    'name': name,
                    'price': price,
                    'link': link,
                    'search_term': search_term,
                    'scrape_time': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'availability': 'In Stock'
                }
        except Exception as e:
            self.custom_logger.debug(f"❌ Error extracting product: {e}")
        
        return None
    
    def extract_text_with_fallbacks(self, container, selectors):
        """Try multiple selectors and return first match"""
        for selector in selectors:
            try:
                result = container.css(selector).get()
                if result and result.strip():
                    return result.strip()
            except:
                continue
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