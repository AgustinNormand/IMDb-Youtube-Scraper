import pandas as pd

import constants
from scrapers_manager.GenresProcessor import GenresProcessor
import logging

from second_source_scraper.StarsScraper.StarsScraper import StarsScraper


class ResultsProcessor():
    def __init__(self, thirdScraperQueue):
        self.thirdScraperQueue = thirdScraperQueue
        self.gp = GenresProcessor()
        self.logger = logging.getLogger("ScrapersManager")
        self.result_count = 0
        self.duplicated_count = 0
        self.ss = StarsScraper()

    def export_results(self, movies):
        df = pd.DataFrame.from_records(movies)
        df.to_csv("results.csv", index=False)

    def equals(self, movie1, movie2):
        keys = list(movie1.keys())
        keys.remove("uniqueID")

        for key in keys:
            if movie1[key] != movie2[key]:
                return False
        return True

    def is_in(self, searched_movie, movies):
        for movie in movies:
            if self.equals(movie, searched_movie):
                return True
        return False

    def delete_duplicates(self, movies):
        unique_movies = []
        for movie in movies:
            if not self.is_in(movie, unique_movies):
                unique_movies.append(movie)
            else:
                self.duplicated_count += 1
                self.logger.debug("Movie duplicated detected {}".format(movie))
        return unique_movies

    def process_results(self):
        movies = []
        while True:
            thirdScraperMovie = self.thirdScraperQueue.get()
            if thirdScraperMovie == "NO_MORE_MOVIES":
                self.thirdScraperQueue.put("NO_MORE_MOVIES")
                break
            else:
                if thirdScraperMovie != None:
                    movies.append(thirdScraperMovie)
                    self.logger.debug("New movie completed the pipeline, Columns len {}, Movie {}".format(len(thirdScraperMovie.keys()),thirdScraperMovie))
                    self.result_count += 1
                else:
                    self.logger.error("None movie receibed")
        self.logger.debug("Pipeline completed, (Pending process genres, movie_star, remove duplicated)")

        if not constants.START_FROM_CHECKPOINT_IMDb_SCRAPER:
            movies = self.delete_duplicates(movies)
            movies = self.gp.process_genres(movies)
            if constants.PROCESS_STARS:
                movies = self.ss.process_stars(movies)
        else:
            movies = self.ss.process_stars(movies)
        self.export_results(movies)

    def log_measurements(self):
        self.logger.info("Duplicated movies count {}".format(self.duplicated_count))
        pass
