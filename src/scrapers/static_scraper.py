import json
import multiprocessing
import os
from functools import partial
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..utils.helpers import (
    RequestHelper,
    build_absolute_url,
    sanitize_price,
    sanitize_text
)
from ..utils.logger import setup_logger


def scrape_page_worker(page_num: int, base_url: str, selectors: dict, delay_range: tuple) -> List[Dict[str, Any]]:
    """
    Top-level function to scrape a single page.
    Must be outside the class for multiprocessing pickling.
    """
    logger = setup_logger(f"worker_{page_num}", log_file=None)

    url = base_url.format(page_num)
    logger.info(f" Scraping page {page_num}: {url}")
    try:
        request_helper = RequestHelper(delay_range)
        response = request_helper.get_with_delay(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        containers = soup.select(selectors['container'])
        logger.debug(f" Found {len(containers)} items on page {page_num}")

        results = []
        for item in containers:
            data = extract_data_static(item, base_url, selectors)
            if data:
                results.append(data)

        return results
    except Exception as e:
        logger.warning(f" Error scraping {url}: {e}")
        return []


def extract_data_static(item, base_url: str, selectors: dict) -> Dict[str, Any]:
    data = {}

    name_elem = item.select_one(selectors['name'])
    if name_elem:
        data['name'] = sanitize_text(name_elem.get('title') or name_elem.get_text())

    price_elem = item.select_one(selectors['price'])
    if price_elem:
        data['price'] = sanitize_price(price_elem.text)

    link_elem = item.select_one(selectors['link'])
    if link_elem:
        data['link'] = build_absolute_url(base_url, link_elem.get('href'))

    img_elem = item.select_one(selectors['image'])
    if img_elem:
        data['image'] = build_absolute_url(base_url, img_elem.get('src'))

    avail_elem = item.select_one(selectors.get('availability', ''))
    if avail_elem:
        data['availability'] = sanitize_text(avail_elem.get_text())

    data['scrape_time'] = datetime.utcnow().isoformat()

    return data if data.get('name') and data.get('link') else {}


class StaticScraper(BaseScraper):
    def __init__(self, config: Dict[str, Any], log_file='logs/static_scraper.log'):
        self.config = config
        self.logger = setup_logger(__name__, log_file=log_file)
        # Delay range for requests (min, max) seconds
        self.delay_range = config.get('delay_range', (1, 2))

    def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info(f" Starting static scraping for source: {self.config.get('name')}")
        start_page = self.config.get('start_page', 1)
        max_pages = self.config.get('max_pages', 1)
        base_url = self.config.get('base_url')
        selectors = self.config['selectors']

        page_nums = list(range(start_page, start_page + max_pages))
        self.logger.info(f" Dispatching scraping for {len(page_nums)} pages...")

        worker_func = partial(scrape_page_worker, base_url=base_url, selectors=selectors, delay_range=self.delay_range)

        with multiprocessing.Pool(processes=min(4, multiprocessing.cpu_count())) as pool:
            results = pool.map(worker_func, page_nums)

        scraped_data = [item for sublist in results for item in sublist if item]

        self.logger.info(f" Finished scraping. Total items scraped: {len(scraped_data)}")

        os.makedirs('logs', exist_ok=True)
        json_path = f"logs/{self.config.get('name', 'static_scrape').replace(' ', '_').lower()}_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=2)
        self.logger.info(f" Saved scraped data to {json_path}")

        return scraped_data
