from abc import ABC, abstractmethod


class BaseScraper(ABC):
    @abstractmethod
    def scrape(self):
        """
        Run the scraping process and return extracted data.
        """
        pass
