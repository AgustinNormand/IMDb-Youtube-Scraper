import logging
from logging import config

import constants
from second_source_scraper.StarsScraper.StarsScraper import StarsScraper

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)


from scrapers_manager.ScrapersManager import ScrapersManager


if __name__ == "__main__":
    sm = ScrapersManager()
    if not constants.START_FROM_CHECKPOINT_IMDb_SCRAPER:
        sm.begin_scrape()
    else:
        sm.begin_scrape_from_third_scraper()

