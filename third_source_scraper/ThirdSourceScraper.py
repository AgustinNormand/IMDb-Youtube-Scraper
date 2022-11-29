import logging

from third_source_scraper.YoutubeScraper import YoutubeScraper


class ThirdSourceScraper:
    def __init__(self):
        self.logger = logging.getLogger("__main__")
        self.youtube_scraper = YoutubeScraper()

    def start(self, movies):
        for uniqueID in movies:
            movies[uniqueID] = self.youtube_scraper.scrape_movie(movies[uniqueID])
        return movies