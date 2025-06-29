import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial

from src.data.database import Database
from src.scrapers.selenium_scraper import scrape_term_process
from src.scrapers.static_scraper import StaticScraper
from src.utils.config import static_config
from src.utils.multiproc_logging import get_log_queue, start_logging_listener


def main():
    log_dir = '/Users/atukaberadze/Desktop/scraping-final/logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_queue = get_log_queue()
    listener = start_logging_listener(log_queue, log_file='logs/main.log')

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.handlers.QueueHandler(log_queue))

    all_results = []

    # --- Static Scraping ---
    logger.info("📚 Starting static scraping from BooksToScrape...")
    static_scraper = StaticScraper(static_config)
    static_results = static_scraper.scrape()
    for r in static_results:
        r['source'] = 'BooksToScrape'
        r['search_term'] = 'books'
    logger.info(f"📚 Scraped {len(static_results)} items from BooksToScrape.")
    all_results.extend(static_results)

    search_terms = ['iphone', 'macbook', 'gaming laptop']
    max_pages = 3

    with Database() as db:
        job_id = db.queue_job('books')
        db.insert_products(static_results, job_id=job_id)
        db.mark_job_complete(job_id)

        logger.info("⚙️ Launching multiprocessing for eBay scraping...")

        scrape_func = partial(
            scrape_term_process,
            chromedriver_path='/Users/atukaberadze/Desktop/chromedriver-mac-arm64/chromedriver',
            timeout=10,
            headless=True,
            max_pages=max_pages,
            log_queue=log_queue  # 🔥 Pass log queue to subprocess
        )

        with ProcessPoolExecutor(max_workers=min(len(search_terms), 3)) as executor:
            future_to_term = {executor.submit(scrape_func, term): term for term in search_terms}

            for future in as_completed(future_to_term):
                term = future_to_term[future]
                try:
                    results = future.result()
                    job_id = db.queue_job(term)

                    for r in results:
                        r['search_term'] = term
                        r['source'] = 'eBay'

                    db.insert_products(results, job_id=job_id)
                    db.mark_job_complete(job_id)

                    logger.info(f"🛍 Scraped {len(results)} items for '{term}' from eBay.")
                    all_results.extend(results)

                except Exception as e:
                    logger.error(f"❌ Error scraping '{term}': {e}")

    logger.info(f"✅ Total of {len(all_results)} products saved to SQLite.")

    print("\n📋 Sample results:")
    for item in all_results[:10]:
        print(
            f"[{item.get('source')}] {item.get('name')} - {item.get('price')} - {item.get('availability')} (Search: {item.get('search_term')})")

    listener.stop()  # ✅ Stop the logging listener properly


if __name__ == "__main__":
    main()
