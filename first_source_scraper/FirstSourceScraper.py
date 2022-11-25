import logging
import time

from first_source_scraper.BOMMoviePageScraper import BOMMoviePageScraper
from first_source_scraper.BOMOpeningWeekendsScraper import BOMOpeningWeekendsScraper


class FirstSourceScraper:
    def __init__(self):
        self.logger = logging.getLogger("__main__")
        self.bom_opening_weekends_scraper = BOMOpeningWeekendsScraper()
        self.bom_movie_page_scrapper = BOMMoviePageScraper()

    def start(self):
        start_time = time.time()
        movies = self.bom_opening_weekends_scraper.scrape_opening_weekends_pages()

        for unique_id in movies:
            movies[unique_id] = self.bom_movie_page_scrapper.scrape_movie_details(movies[unique_id])
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
