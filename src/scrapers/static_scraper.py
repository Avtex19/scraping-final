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
        self.scraped_data = []

    def scrape(self) -> List[Dict[str, Any]]:
        self.logger.info(f" Starting static scraping for source: {self.config.get('name')}")
        base_url = self.config.get('base_url')
        start_page = self.config.get('start_page', 1)
        max_pages = self.config.get('max_pages', 1)

        for page_num in range(start_page, start_page + max_pages):
            url = base_url.format(page_num)
            self.logger.info(f" Scraping page {page_num}: {url}")
            try:
                response = self.request_helper.get_with_delay(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                containers = soup.select(self.config['selectors']['container'])
                self.logger.debug(f" Found {len(containers)} containers on page {page_num}")

                for item in containers:
                    data = self.extract_data(item, url)
                    if data:
                        self.scraped_data.append(data)
                    else:
                        self.logger.debug("⚠️ Skipped empty or malformed item")

            except Exception as e:
                self.logger.warning(f" Error scraping {url}: {e}")

        self.logger.info(f" Finished scraping. Total items scraped: {len(self.scraped_data)}")
        return self.scraped_data

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
