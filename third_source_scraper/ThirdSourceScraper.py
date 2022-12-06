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
                #self.thirdScraperQueue.put(self.youtube_scraper.scrape_movie(secondScraperMovie))
                # TODO Uncomment this to not avoid youtubescraper
                self.thirdScraperQueue.put(secondScraperMovie)


    def log_measurements(self):
        pass #TODO