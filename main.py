import logging

from scrapers_manager.ScrapersManager import ScrapersManager


if __name__ == "__main__":
    sm = ScrapersManager()
    sm.begin_scrape()