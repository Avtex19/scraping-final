import multiprocessing
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


class StaticScraper(BaseScraper):
    def __init__(self, config: Dict[str, Any], log_file='logs/static_scraper.log'):
        self.config = config
        self.logger = setup_logger(__name__, log_file=log_file)
        self.request_helper = RequestHelper(config.get('delay_range', (1, 2)))

    def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info(f"📚 Starting static scraping for source: {self.config.get('name')}")
        start_page = self.config.get('start_page', 1)
        max_pages = self.config.get('max_pages', 1)
        base_url = self.config.get('base_url')

        page_nums = list(range(start_page, start_page + max_pages))
        self.logger.info(f"📄 Dispatching scraping for {len(page_nums)} pages...")

        # Use multiprocessing Pool
        with multiprocessing.Pool(processes=min(4, multiprocessing.cpu_count())) as pool:
            results = pool.map(partial(self._scrape_page, base_url=base_url), page_nums)

        # Flatten results and filter empty
        scraped_data = [item for sublist in results for item in sublist if item]

        self.logger.info(f"✅ Finished scraping. Total items scraped: {len(scraped_data)}")
        return scraped_data

    def _scrape_page(self, page_num: int, base_url: str) -> List[Dict[str, Any]]:
        url = base_url.format(page_num)
        self.logger.info(f"🔍 Scraping page {page_num}: {url}")
        try:
            response = self.request_helper.get_with_delay(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            containers = soup.select(self.config['selectors']['container'])
            self.logger.debug(f"📦 Found {len(containers)} items on page {page_num}")

            return [self.extract_data(item, url) for item in containers if self.extract_data(item, url)]
        except Exception as e:
            self.logger.warning(f"❌ Error scraping {url}: {e}")
            return []

    def extract_data(self, item, base_url: str) -> Dict[str, Any]:
        sel = self.config['selectors']
        data = {}

        name_elem = item.select_one(sel['name'])
        if name_elem:
            data['name'] = sanitize_text(name_elem.get('title') or name_elem.get_text())

        price_elem = item.select_one(sel['price'])
        if price_elem:
            data['price'] = sanitize_price(price_elem.text)

        link_elem = item.select_one(sel['link'])
        if link_elem:
            data['link'] = build_absolute_url(base_url, link_elem.get('href'))

        img_elem = item.select_one(sel['image'])
        if img_elem:
            data['image'] = build_absolute_url(base_url, img_elem.get('src'))

        avail_elem = item.select_one(sel.get('availability', ''))
        if avail_elem:
            data['availability'] = sanitize_text(avail_elem.get_text())

        data['scrape_time'] = datetime.utcnow().isoformat()

        return data if data.get('name') and data.get('link') else {}
