import logging

from src.data.database import Database
from src.scrapers.selenium_scraper import EbayScraper
from src.scrapers.static_scraper import StaticScraper
from src.utils.config import static_config

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    all_results = []

    # --- Static scraping ---
    logger.info("Starting static scraping from BooksToScrape...")
    static_scraper = StaticScraper(static_config)
    static_results = static_scraper.scrape()
    for r in static_results:
        r['source'] = 'BooksToScrape'
        r['search_term'] = 'books'

    logger.info(f"Scraped {len(static_results)} items from BooksToScrape.")
    all_results.extend(static_results)

    # --- Dynamic scraping from eBay ---
    search_terms = ['iphone', 'macbook', 'gaming laptop']

    with Database() as db:
        # Static scraper save
        job_id = db.queue_job('books')
        db.insert_products(static_results, job_id=job_id)
        db.mark_job_complete(job_id)

        with EbayScraper(headless=True, timeout=10) as ebay_scraper:
            for term in search_terms:
                job_id = db.queue_job(term)

                logger.info(f"Starting eBay scrape for search term: '{term}'")
                ebay_results = ebay_scraper.scrape(term, max_pages=3)

                for r in ebay_results:
                    r['search_term'] = term
                    r['source'] = 'eBay'

                db.insert_products(ebay_results, job_id=job_id)
                db.mark_job_complete(job_id)

                logger.info(f"Completed eBay scrape for '{term}' with {len(ebay_results)} items.")
                all_results.extend(ebay_results)

    logger.info(f"✅ Total of {len(all_results)} products saved to SQLite.")

    # --- Preview output ---
    print("\n📋 Sample results:")
    for item in all_results[:10]:
        print(f"[{item.get('source')}] {item.get('name')} - {item.get('price')} - {item.get('availability')} (Search: {item.get('search_term')})")


if __name__ == "__main__":
    main()
