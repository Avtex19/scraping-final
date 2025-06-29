import re
import time
import random
import logging
from urllib.parse import urljoin
import requests


class RequestHelper:
    def __init__(self, delay_range=(1, 2)):
        self.delay_range = delay_range
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def get_with_delay(self, url: str, headers=None):
        if headers is None:
            headers = {'User-Agent': 'Mozilla/5.0'}
        time.sleep(random.uniform(*self.delay_range))
        response = self.session.get(url, headers=headers)
        response.raise_for_status()
        return response


def build_absolute_url(base: str, link: str) -> str:
    return urljoin(base, link)


def sanitize_price(text: str) -> float:
    cleaned = re.sub(r'[^\d.]', '', text)
    try:
        return float(cleaned)
    except:
        return 0.0


def sanitize_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip())
