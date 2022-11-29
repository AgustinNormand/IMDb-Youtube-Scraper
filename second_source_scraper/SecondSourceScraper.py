import logging

from second_source_scraper.IMDbScraper import IMDbScraper

class SecondSourceScraper:
    def __init__(self):
        self.logger = logging.getLogger("__main__")
        self.imdb_scraper = IMDbScraper()

    def start(self, movies):
        for uniqueID in movies:
            movies[uniqueID] = self.imdb_scraper.scrape_movie(movies[uniqueID])
        return movies