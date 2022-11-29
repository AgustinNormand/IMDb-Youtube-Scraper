import logging
from second_source_scraper.IMDbScraper import IMDbScraper

class SecondSourceScraper:
    def __init__(self, firstScraperQueue, secondScraperQueue):
        self.logger = logging.getLogger("__main__")
        self.imdb_scraper = IMDbScraper()
        self.firstScraperQueue = firstScraperQueue
        self.secondScraperQueue = secondScraperQueue

    def begin_scrape(self):
        while True:
            firstScraperMovie = self.firstScraperQueue.get()
            if firstScraperMovie == "NO_MORE_MOVIES":
                self.firstScraperQueue.put("NO_MORE_MOVIES")
                self.secondScraperQueue.put("NO_MORE_MOVIES")
                break
            self.secondScraperQueue.put(self.imdb_scraper.scrape_movie(firstScraperMovie))

    def log_measurements(self):
        pass #TODO
