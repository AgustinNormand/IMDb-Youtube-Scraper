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
            #print("Moive in third")
            if secondScraperMovie == "NO_MORE_MOVIES":
                self.secondScraperQueue.put("NO_MORE_MOVIES")
                self.thirdScraperQueue.put("NO_MORE_MOVIES")
                break
            else:
                #processed_movie = self.youtube_scraper.scrape_movie(secondScraperMovie)
                # TODO Uncomment this to not avoid youtubescraper
                processed_movie = secondScraperMovie
                if processed_movie != None:
                    self.thirdScraperQueue.put(processed_movie)
                    self.logger.debug("Ignoring process of {}".format(processed_movie))
                else:
                    self.logger.error("Movie not processed {}".format(secondScraperMovie))




    def log_measurements(self):
        pass #TODO