import logging
import time
from first_source_scraper.BOMMoviePageScraper import BOMMoviePageScraper
from first_source_scraper.BOMOpeningWeekendsScraper import BOMOpeningWeekendsScraper

class FirstSourceScraper:
    def __init__(self, queue):
        self.logger = None
        self.configure_logger()
        self.bom_opening_weekends_scraper = BOMOpeningWeekendsScraper()
        self.bom_movie_page_scrapper = BOMMoviePageScraper()
        self.queue = queue

    def configure_logger(self):
        self.logger = logging.getLogger("FirstSourceScraper")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fileHandler = logging.FileHandler('./first_source_scraper/FirstSourceScraper.log', mode='w')
        fileHandler.setFormatter(formatter)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(fileHandler)

    def begin_scrape(self):
        start_time = time.time()

        for movie in self.bom_opening_weekends_scraper.scrape_opening_weekends_pages():
            self.queue.put(self.bom_movie_page_scrapper.scrape_movie_details(movie))
            #break

        self.queue.put("NO_MORE_MOVIES")

        self.total_time_elapsed = time.time() - start_time

    def log_measurements(self):
        self.logger.info("Scraped {} movies from initial 5-pages".format(
            self.bom_opening_weekends_scraper.get_total_pages_scraped()))

        self.logger.info("Scraped {} movie detail pages".format(
            self.bom_movie_page_scrapper.get_total_movie_pages_scraped()))

        bom_ows_time_elapsed_waiting_http_response, bom_ows_time_elapsed_parsing = \
            self.bom_opening_weekends_scraper.get_times()

        bom_mps_time_elapsed_waiting_http_response, bom_mps_time_elapsed_parsing = \
            self.bom_movie_page_scrapper.get_times()

        self.logger.info("{} elapsed {:.3g} seconds {}".format("BOMOpeningWeekendsScraper",
                                                   bom_ows_time_elapsed_waiting_http_response,
                                                   "waiting http responses"))

        self.logger.info("{} elapsed {:.3g} seconds {}".format("BOMOpeningWeekendsScraper",
                                                   bom_ows_time_elapsed_parsing,
                                                   "parsing"))

        self.logger.info("{} elapsed {:.3g} seconds {}".format("BOMMoviePageScraper",
                                                   bom_mps_time_elapsed_waiting_http_response,
                                                   "waiting http responses"))

        self.logger.info("{} elapsed {:.3g} seconds {}".format("BOMMoviePageScraper",
                                                   bom_mps_time_elapsed_parsing,
                                                   "parsing"))

        self.logger.info("Total time of first_source_scraper {:.3g} seconds".format(self.total_time_elapsed))
