import queue
import time
import pandas as pd
import logging
import constants
from second_source_scraper.DirectorsScraper.DirectorsScraperWorker import DirectorsScraperWorker
from second_source_scraper.StarsScraper.StarsScraperWorker import StarsScraperWorker
import ast

from second_source_scraper.WritersScraper.WritersScraperWorker import WritersScraperWorker


class DirectorsScraper:
    def __init__(self):
        self.scraped_movies = {}
        self.tasks_queue = queue.Queue()
        self.scraped_directors = {}
        self.logger = logging.getLogger("DirectorsScraper")

    def read_movies_from_checkpoint(self):
        with open("checkpoint_actor_movies_scraped.csv", "r") as f:
            lines = f.readlines()
            for line in lines:
                href, raiting = line.split(",")
                href = href.strip()
                raiting = float(raiting)
                self.scraped_movies[href] = float(raiting)

    def initialization(self, movies):
        self.logger.debug("Movies to scrape directors {}".format(len(movies)))

        self.directors_tasks = {}
        self.tasks = []
        small_task_number = 0
        for movie in movies:
            adapted_url = movie["url_imdb"].replace("imdb", "m.imdb")
            self.scraped_movies[adapted_url] = float(movie["user_raiting"])
            for (director_name, director_url) in movie["directors"]:
                if director_name not in self.directors_tasks.keys():
                    self.directors_tasks[director_name] = []
                self.directors_tasks[director_name].append([director_name, director_url, movie["url_imdb"]])
                small_task_number += 1
        self.logger.debug("Subtasks to resolve {}".format(small_task_number))

        task_number = 0
        for key in self.directors_tasks:
            self.tasks_queue.put([task_number, self.directors_tasks[key]])
            task_number += 1
        self.logger.debug("Tasks to resolve {}".format(task_number))

        if constants.USE_MOVIES_CHECKPOINT_STAR_SCRAPER:
            self.read_movies_from_checkpoint()

    def calculate_stars_of_movie(self, movie):
        stars = 0
        for director in movie["directors"]:
            director_name = director[0]
            if director_name not in self.scraped_directors.keys():
                self.logger.error("Director no in scraped director. {}".format(director_name))
            else:
                star_before_director_movies = self.scraped_directors[director_name]["star_before"]
                if movie["url_imdb"] in star_before_director_movies:
                    stars += 1
                    continue
        return stars

    def calculate_directors(self, movies):
        for movie in movies:
            movie["directors"] = self.calculate_stars_of_movie(movie)
        return movies

    def manage_scrape_directors(self):
        workers = []
        for worker_number in range(200):
            worker = DirectorsScraperWorker(worker_number, self.tasks_queue, self.scraped_directors, self.scraped_movies)
            worker.start()
            workers.append(worker)

        self.tasks_queue.join()

    def process_directors(self, movies):
        start_time = time.time()

        self.initialization(movies)
        self.manage_scrape_directors()

        df = pd.DataFrame.from_records(self.scraped_directors)
        df.to_csv("scraped_directors.csv", index=False)

        movies = self.calculate_directors(movies)

        total_time_elapsed = time.time() - start_time

        self.logger.debug("Total time whole scraping {:.3g} minutes".format(total_time_elapsed / 60))

        return movies