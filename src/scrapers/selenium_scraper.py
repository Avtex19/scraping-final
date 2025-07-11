import time
import os
import json


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.utils.logger import setup_logger
from src.utils.multiproc_logging import setup_worker_logger


class EbayScraper:
    """
    A class-based eBay scraper using Selenium WebDriver.
    """

    def __init__(self, chromedriver_path=None, headless=False, timeout=10, log_file='../logs/ebay_scraper.log'):
        """
        Initialize the eBay scraper.

        Args:
            chromedriver_path (str): Path to ChromeDriver executable
            headless (bool): Whether to run browser in headless mode
            timeout (int): WebDriver wait timeout in seconds
            log_file (str): Path to the log file
        """
        self.chromedriver_path = chromedriver_path or '/Users/atukaberadze/Desktop/chromedriver-mac-arm64/chromedriver'
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.wait = None
        self.logger = setup_logger(__name__, log_file=log_file)

    def _setup_driver(self):
        """Set up Chrome WebDriver with options."""
        options = Options()

        if self.headless:
            options.add_argument('--headless')

        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')

        service = Service(self.chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, self.timeout)

        self.logger.info(" WebDriver initialized.")

    def _extract_item_data(self, item, page_num):
        name = None
        try:
            title_elem = item.find_element(By.CSS_SELECTOR, 'div.s-item__title span[role="heading"]')
            name = title_elem.text.strip()
        except NoSuchElementException:
            try:
                title_div = item.find_element(By.CSS_SELECTOR, 'div.s-item__title')
                name = title_div.text.strip()
            except NoSuchElementException:
                name = None

        if not name or name in ["New Listing", "Shop on eBay"]:
            return None

        try:
            link = item.find_element(By.CSS_SELECTOR, 'a.s-item__link').get_attribute('href')
        except NoSuchElementException:
            link = None

        try:
            price = item.find_element(By.CSS_SELECTOR, 'span.s-item__price').text.strip()
        except NoSuchElementException:
            price = None

        try:
            availability = item.find_element(By.CSS_SELECTOR, 'span.SECONDARY_INFO').text.strip()
        except NoSuchElementException:
            availability = "Unknown"

        if not link or not name:
            return None

        return {
            'name': name,
            'price': price,
            'link': link,
            'page': page_num,
            'availability': availability,
        }

    def _scrape_page(self, search_term, page_num):
        """
        Scrape a single page of eBay results.

        Args:
            search_term (str): Search term to look for
            page_num (int): Page number to scrape

        Returns:
            list: List of scraped items from the page
        """
        url = f"https://www.ebay.com/sch/i.html?_nkw={search_term}&_pgn={page_num}"
        print(f"🔍 Scraping page {page_num}: {url}")
        self.logger.info(f"🔍 Scraping page {page_num}: {url}")

        try:
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#srp-river-results li.s-item')))
            with open(f'../logs/ebay_debug_page_{page_num}.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"[DEBUG] Saved page source to ../logs/ebay_debug_page_{page_num}.html")
        except TimeoutException:
            self.logger.warning(f"⏰ Timeout on page {page_num}, skipping...")
            return []

        results_container = self.driver.find_element(By.CSS_SELECTOR, '#srp-river-results')
        items = results_container.find_elements(By.CSS_SELECTOR, 'li.s-item')
        self.logger.debug(f"Found {len(items)} <li.s-item> elements on page {page_num}")

        if not items:
            print(f"️ No items found on page {page_num}")
            self.logger.warning(f"️ No items found on page {page_num}")
            print("[DEBUG] Dumping HTML of all li.s-item elements:")
            for item in results_container.find_elements(By.CSS_SELECTOR, 'li.s-item'):
                print(item.get_attribute('outerHTML')[:500])
            return []

        results = []
        for item in items:
            item_data = self._extract_item_data(item, page_num)
            if item_data:
                results.append(item_data)

        print(f" Extracted {len(results)} items from page {page_num}")
        self.logger.info(f" Extracted {len(results)} valid items from page {page_num}")
        return results

    def scrape(self, search_term, max_pages=3, delay_between_pages=2):
        if not self.driver:
            self._setup_driver()

        results = []
        self.logger.info(f" Starting scrape for '{search_term}'")

        try:
            for page_num in range(1, max_pages + 1):
                page_results = self._scrape_page(search_term, page_num)
                results.extend(page_results)
                time.sleep(delay_between_pages)
        except Exception as e:
            self.logger.exception(f" Error during scraping '{search_term}': {e}")
        finally:
            self.close()

        self.logger.info(f"🎯 Finished scraping '{search_term}'. Total items: {len(results)}")

        os.makedirs('../logs', exist_ok=True)

        json_path = f'../logs/ebay_{search_term.replace(" ", "_")}_results.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        self.logger.info(f"💾 Saved scraped data to {json_path}")

        return results

    def scrape_multiple_terms(self, search_terms, max_pages=3, delay_between_pages=2):
        """
        Scrape eBay for multiple search terms.

        Args:
            search_terms (list): List of search terms
            max_pages (int): Maximum number of pages per search term
            delay_between_pages (int): Delay in seconds between page requests

        Returns:
            list: Combined list of all scraped items
        """
        all_results = []

        for term in search_terms:
            self.logger.info(f"🔍 Starting scrape for search term: '{term}'")
            term_results = self.scrape(term, max_pages, delay_between_pages)

            for result in term_results:
                result['search_term'] = term

            all_results.extend(term_results)
            self.logger.info(f" Completed scrape for '{term}': {len(term_results)} items")
            time.sleep(1)

        return all_results

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.wait = None
            self.logger.info(" WebDriver closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()




def scrape_term_process(term, chromedriver_path, timeout, headless, max_pages=3, log_queue=None):
    """
    Wrapper function for multiprocessing. Scrapes a search term with optional logging queue.
    Returns JSON string.

    Args:
        term (str): Search keyword.
        chromedriver_path (str): Path to ChromeDriver.
        timeout (int): WebDriver timeout.
        headless (bool): Headless mode toggle.
        max_pages (int): Max pages to scrape.
        log_queue (multiprocessing.Queue, optional): Queue for multiprocessing-safe logging.

    Returns:
        str: JSON string of scraped results.
    """
    if log_queue:
        setup_worker_logger(log_queue)

    scraper = EbayScraper(
        chromedriver_path=chromedriver_path,
        timeout=timeout,
        headless=headless
    )
    results = scraper.scrape(term, max_pages=max_pages)

    results_json = json.dumps(results, indent=2)
    return results_json


