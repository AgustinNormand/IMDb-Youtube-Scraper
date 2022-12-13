import queue
import time
import pandas as pd
import logging
import constants
from second_source_scraper.StarsScraper.StarsScraperWorker import StarsScraperWorker
import ast

from second_source_scraper.WritersScraper.WritersScraperWorker import WritersScraperWorker


class WritersScraper:
    def __init__(self):
        self.scraped_movies = {}
        self.tasks_queue = queue.Queue()
        self.scraped_writers = {}
        self.logger = logging.getLogger("WritersScraper")

    def read_movies_from_checkpoint(self):
        with open("checkpoint_actor_movies_scraped.csv", "r") as f:
            lines = f.readlines()
            for line in lines:
                href, raiting = line.split(",")
                href = href.strip()
                raiting = float(raiting)
                self.scraped_movies[href] = float(raiting)

    def initialization(self, movies):
        self.logger.debug("Movies to scrape writers {}".format(len(movies)))

        self.writers_tasks = {}
        self.tasks = []
        small_task_number = 0
        for movie in movies:
            adapted_url = movie["url_imdb"].replace("imdb", "m.imdb")
            self.scraped_movies[adapted_url] = float(movie["user_raiting"])
            for (writer_name, writer_url) in movie["writers"]:
                if writer_name not in self.writers_tasks.keys():
                    self.writers_tasks[writer_name] = []
                self.writers_tasks[writer_name].append([writer_name, writer_url, movie["url_imdb"]])
                small_task_number += 1
        self.logger.debug("Subtasks to resolve {}".format(small_task_number))

        task_number = 0
        for key in self.writers_tasks:
            self.tasks_queue.put([task_number, self.writers_tasks[key]])
            task_number += 1
        self.logger.debug("Tasks to resolve {}".format(task_number))

        if constants.USE_MOVIES_CHECKPOINT_STAR_SCRAPER:
            self.read_movies_from_checkpoint()

    def calculate_stars_of_movie(self, movie):
        stars = 0
        for writer in movie["writers"]:
            writer_name = writer[0]
            if writer_name not in self.scraped_writers.keys():
                self.logger.error("Writer no in scraped writers. {}".format(writer_name))
            else:
                star_before_writer_movies = self.scraped_writers[writer_name]["star_before"]
                if movie["url_imdb"] in star_before_writer_movies:
                    stars += 1
                    continue
        return stars

    def calculate_writers(self, movies):
        for movie in movies:
            movie["writers"] = self.calculate_stars_of_movie(movie)
        return movies

    def manage_scrape_writers(self):
        workers = []
        for worker_number in range(200):
            worker = WritersScraperWorker(worker_number, self.tasks_queue, self.scraped_writers, self.scraped_movies)
            worker.start()
            workers.append(worker)

        self.tasks_queue.join()

    def process_writers(self, movies):
        start_time = time.time()

        self.initialization(movies)
        self.manage_scrape_writers()

        df = pd.DataFrame.from_records(self.scraped_writers)
        df.to_csv("scraped_writers.csv", index=False)

        movies = self.calculate_writers(movies)

        total_time_elapsed = time.time() - start_time

        self.logger.debug("Total time whole scraping {:.3g} minutes".format(total_time_elapsed / 60))

        return movies