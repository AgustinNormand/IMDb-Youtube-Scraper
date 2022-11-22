from BOMMoviePageScraper import BOMMoviePageScraper
from BOMOpeningWeekendsScraper import BOMOpeningWeekendsScraper
import logging

class FirstSourceScraper:
    def __init__(self):
        self.logger = logging.getLogger("__main__")
        self.bom_opening_weekends_scraper = BOMOpeningWeekendsScraper()
        self.bom_movie_page_scrapper = BOMMoviePageScraper()
        self.total_time_elapsed = 0  # TODO

    def start(self):
        movies = self.bom_opening_weekends_scraper.scrape_opening_weekends_pages()

        for unique_id in movies:
            movies[unique_id] = self.bom_movie_page_scrapper.scrape_movie_details(movies[unique_id])
