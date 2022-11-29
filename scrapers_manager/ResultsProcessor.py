import pandas as pd
from scrapers_manager.GenresProcessor import GenresProcessor


class ResultsProcessor():
    def __init__(self, thirdScraperQueue):
        self.thirdScraperQueue = thirdScraperQueue
        self.gp = GenresProcessor()

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
            movies = self.gp.process_genres(movies)
            movies.append(thirdScraperMovie)
            self.export_results(movies)

    def log_measurements(self):
        pass
