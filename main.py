import logging
from logging import config
logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)



from scrapers_manager.ScrapersManager import ScrapersManager


if __name__ == "__main__":
    sm = ScrapersManager()
    sm.begin_scrape()