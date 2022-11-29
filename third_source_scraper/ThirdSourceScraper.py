import logging
from third_source_scraper.YoutubeScraper import YoutubeScraper


class ThirdSourceScraper:
    def __init__(self, secondScraperQueue, thirdScraperQueue):
        self.logger = None
        self.configure_logger()
        self.youtube_scraper = YoutubeScraper()
        self.secondScraperQueue = secondScraperQueue
        self.thirdScraperQueue = thirdScraperQueue

    def configure_logger(self):
        self.logger = logging.getLogger("ThirdSourceScraper")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler('./third_source_scraper/ThirdSourceScraper.log', mode='w')
        file_handler.setFormatter(formatter)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

    def begin_scrape(self):
        while True:
            secondScraperMovie = self.secondScraperQueue.get()
            if secondScraperMovie == "NO_MORE_MOVIES":
                self.secondScraperQueue.put("NO_MORE_MOVIES")
                self.thirdScraperQueue.put("NO_MORE_MOVIES")
                break
            #self.thirdScraperQueue.put(self.youtube_scraper.scrape_movie(secondScraperMovie))
            # TODO Uncomment this to not avoid youtubescraper
            self.thirdScraperQueue.put(secondScraperMovie)


    def log_measurements(self):
        pass #TODO