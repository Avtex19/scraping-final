import os
import sys
import time
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.data.database import Database
from src.utils.logger import setup_logger
from .amazon_spider import AmazonProductSpider, SCRAPED_ITEMS, RotateUserAgentMiddleware, AmazonAntiBlockMiddleware


class AmazonScrapyRunner:
    """Runner class for Amazon Scrapy scraper with database integration"""
    
    def __init__(self, db_path="scraped_data.db"):
        self.db = Database(db_path)
        self.logger = setup_logger(__name__, log_file='logs/amazon_scraper.log')
    
    def run_scraper(self, search_terms, max_pages=1):
        """Run the Amazon scraper and store results in database"""
        self.logger.info(f"🚀 Starting Amazon scraper for terms: {search_terms}")
        
        try:
            # Create a new job entry
            search_term = ', '.join(search_terms)
            job_id = self.db.queue_job(search_term)
            self.logger.info(f"📝 Created job ID: {job_id}")
            
            # Configure Scrapy settings manually
            settings = {
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
                'AUTOTHROTTLE_DEBUG': False,
                'DOWNLOAD_TIMEOUT': 30,
                'LOG_LEVEL': 'WARNING',
                'DOWNLOADER_MIDDLEWARES': {
                    'src.scrapers.scrapy_crawler.amazon_spider.RotateUserAgentMiddleware': 400,
                    'src.scrapers.scrapy_crawler.amazon_spider.AmazonAntiBlockMiddleware': 500,
                }
            }
            
            # Clear global items before starting
            global SCRAPED_ITEMS
            SCRAPED_ITEMS.clear()
            
            # Create and configure the crawler process
            process = CrawlerProcess(settings)
            
            # Add the spider to the process
            process.crawl(
                AmazonProductSpider,
                search_terms=search_terms,
                max_pages=max_pages,
                job_id=job_id
            )
            
            # Start the crawling process
            self.logger.info(f"🕸️ Starting Scrapy crawler process...")
            process.start()
            
            # After crawling, save results to database
            return self._save_results_to_database(job_id)
            
        except Exception as e:
            self.logger.error(f"❌ Error running Amazon scraper: {e}")
            return []
    
    def _save_results_to_database(self, job_id):
        """Save scraped items to the database"""
        global SCRAPED_ITEMS
        
        if not SCRAPED_ITEMS:
            self.logger.info(f"⚠️ No items collected from Amazon")
            return []
        
        # Prepare items for database insertion
        products_to_insert = []
        for item in SCRAPED_ITEMS:
            products_to_insert.append({
                'name': item.get('name', 'Unknown'),
                'price': item.get('price'),
                'link': item.get('link', ''),
                'image': '',  # Amazon scraper doesn't extract images yet
                'availability': item.get('availability', ''),
                'scrape_time': item.get('scrape_time'),
                'search_term': item.get('search_term', 'laptop')
            })
        
        # Insert all products at once
        try:
            self.db.insert_products(products_to_insert, job_id)
            saved_count = len(products_to_insert)
            
            # Mark job as complete
            self.db.mark_job_complete(job_id)
            self.logger.info(f"🎉 Saved {saved_count} Amazon products to database!")
        except Exception as e:
            self.logger.error(f"❌ Failed to save products to database: {e}")
            saved_count = 0
        
        return SCRAPED_ITEMS


def run_amazon_scraper():
    """Standalone function to run Amazon scraper"""
    runner = AmazonScrapyRunner()
    search_terms = ['laptop']
    results = runner.run_scraper(search_terms, max_pages=1)
    return results


if __name__ == "__main__":
    run_amazon_scraper() 