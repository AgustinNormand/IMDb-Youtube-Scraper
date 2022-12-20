import logging
from third_source_scraper.YoutubeScraper import YoutubeScraper


class ThirdSourceScraper:
    def __init__(self, secondScraperQueue, thirdScraperQueue):
        self.logger = logging.getLogger("ThirdSourceScraper")
        self.youtube_scraper = YoutubeScraper()
        self.secondScraperQueue = secondScraperQueue
        self.thirdScraperQueue = thirdScraperQueue

    def begin_scrape(self):
        while True:
            secondScraperMovie = self.secondScraperQueue.get()
            if secondScraperMovie == "NO_MORE_MOVIES":
                self.secondScraperQueue.put("NO_MORE_MOVIES")
                self.thirdScraperQueue.put("NO_MORE_MOVIES")
                break
            else:
                processed_movie = self.youtube_scraper.scrape_movie(secondScraperMovie)
                if processed_movie != None:
                    self.thirdScraperQueue.put(processed_movie)
                else:
                    self.logger.error("Movie not processed {}".format(secondScraperMovie))




    def log_measurements(self):
        pass #TODO