import pandas as pd
from scrapers_manager.GenresProcessor import GenresProcessor
import logging

class ResultsProcessor():
    def __init__(self, thirdScraperQueue):
        self.thirdScraperQueue = thirdScraperQueue
        self.gp = GenresProcessor()
        self.logger = logging.getLogger("ScrapersManager")
        self.result_count = 0

    def export_results(self, movies):
        df = pd.DataFrame.from_records(movies)
        df.to_csv("results.csv", index=False)

    def process_results(self):
        movies = []
        while True:
            thirdScraperMovie = self.thirdScraperQueue.get()
            if thirdScraperMovie == "NO_MORE_MOVIES":
                self.thirdScraperQueue.put("NO_MORE_MOVIES")
                break
            else:
                movies.append(thirdScraperMovie)
                self.logger.debug("New movie completed the pipeline (Pending process genres), Columns len {}, Movie {}".format(len(thirdScraperMovie.keys()),thirdScraperMovie))
                self.result_count += 1

        movies = self.gp.process_genres(movies)
        self.export_results(movies)

    def log_measurements(self):
        pass
