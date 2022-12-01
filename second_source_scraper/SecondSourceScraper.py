import logging
from second_source_scraper.IMDbScraper import IMDbScraper


class SecondSourceScraper:
    def __init__(self, firstScraperQueue, secondScraperQueue):
        self.logger = None
        self.configure_logger()
        self.imdb_scraper = IMDbScraper()
        self.firstScraperQueue = firstScraperQueue
        self.secondScraperQueue = secondScraperQueue

    def configure_logger(self):
        self.logger = logging.getLogger("SecondSourceScraper")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler('./second_source_scraper/SecondSourceScraper.log', mode='w')
        file_handler.setFormatter(formatter)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def begin_scrape(self):
        while True:
            firstScraperMovie = self.firstScraperQueue.get()
            if firstScraperMovie == "NO_MORE_MOVIES":
                self.firstScraperQueue.put("NO_MORE_MOVIES")
                self.secondScraperQueue.put("NO_MORE_MOVIES")
                break
            else:
                self.secondScraperQueue.put(self.imdb_scraper.scrape_movie(firstScraperMovie))

    def log_measurements(self):
        pass #TODO
