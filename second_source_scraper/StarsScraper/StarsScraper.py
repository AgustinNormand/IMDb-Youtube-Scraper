import queue
import time
import pandas as pd
import logging
import constants
from second_source_scraper.StarsScraper.StarsScraperWorker import StarsScraperWorker
import ast

class StarsScraper:
    def __init__(self):
        self.scraped_movies = {}
        self.tasks_queue = queue.Queue()
        self.scraped_actors = {}
        self.logger = logging.getLogger("StarsScraper")

    def read_movies_from_checkpoint(self):
        with open("checkpoint_actor_movies_scraped.csv", "r") as f:
            lines = f.readlines()
            for line in lines:
                href, raiting = line.split(",")
                href = href.strip()
                raiting = float(raiting)
                self.scraped_movies[href] = float(raiting)

    def read_actors_from_checkpoint(self):
        data = pd.read_csv("scraped_actors.csv")
        for actor_name in data.columns:
            if actor_name in self.scraped_actors.keys():
                print("Actor was already in dict")

            self.scraped_actors[actor_name] = {}
            movies = data[actor_name][0]
            star_before = data[actor_name][1]
            specific_url = data[actor_name][2]
            self.scraped_actors[actor_name]["movies"] = ast.literal_eval(movies)
            self.scraped_actors[actor_name]["url"] = specific_url
            self.scraped_actors[actor_name]["star_before"] = ast.literal_eval(star_before)

    def get_missing_actors_scrape(self, movies):
        missing_actors_scrape = []
        for movie in movies:
            for actor in movie["actors"]:
                actor_name = actor[0]
                if actor_name not in self.scraped_actors.keys():
                    if actor_name not in missing_actors_scrape:
                        missing_actors_scrape.append(actor_name)
        return missing_actors_scrape

    def initialization(self, movies):
        self.logger.debug("Movies to scrape stars {}".format(len(movies)))

        self.actors_tasks = {}
        self.tasks = []
        small_task_number = 0
        for movie in movies:
            for (actor_name, actor_url) in movie["actors"]:
                if actor_name not in self.actors_tasks.keys():
                    self.actors_tasks[actor_name] = []
                self.actors_tasks[actor_name].append([actor_name, actor_url, movie["url_imdb"]])
                small_task_number += 1
        self.logger.debug("Subtasks to resolve {}".format(small_task_number))

        task_number = 0
        for key in self.actors_tasks:
            self.tasks_queue.put([task_number, self.actors_tasks[key]])
            task_number += 1
        self.logger.debug("Tasks to resolve {}".format(task_number))

    def add_ranking_movies_to_scraped_movies(self, movies):
        for movie in movies:
            adapted_url = movie["url_imdb"].replace("imdb", "m.imdb")
            self.scraped_movies[adapted_url] = float(movie["user_raiting"])

    def create_tasks_for_missing_actors(self, missing_scrape_actors, movies):
        self.actors_tasks = {}
        self.tasks = []
        small_task_number = 0
        for movie in movies:
            for (actor_name, actor_url) in movie["actors"]:
                if actor_name in missing_scrape_actors:
                    if actor_name not in self.actors_tasks.keys():
                        self.actors_tasks[actor_name] = []
                    self.actors_tasks[actor_name].append([actor_name, actor_url, movie["url_imdb"]])
                    small_task_number += 1
        self.logger.debug("Subtasks to resolve {}".format(small_task_number))

        task_number = 0
        for key in self.actors_tasks:
            self.tasks_queue.put([task_number, self.actors_tasks[key]])
            task_number += 1
        self.logger.debug("Tasks to resolve {}".format(task_number))

    def calculate_stars_of_movie(self, movie):
        stars = 0
        for actor in movie["actors"]:
            actor_name = actor[0]
            if actor_name not in self.scraped_actors.keys():
                self.logger.error("Actor no in scraped actors. {}".format(actor_name))
            else:
                star_before_actor_movies = self.scraped_actors[actor_name]["star_before"]
                #print("Movie URL {}".format(movie["url_imdb"]))
                #print("Star Before Actor Movies {}".format(star_before_actor_movies))
                #adapted_movie_url = movie["url_imdb"].replace("imdb.com", "m.imdb.com")
                if movie["url_imdb"] in star_before_actor_movies:
                    stars += 1
                    continue
        return stars

    def calculate_stars(self, movies):
        for movie in movies:
            movie["movie_star"] = self.calculate_stars_of_movie(movie)
            movie.pop("actors")
        return movies

    def manage_scrape_actors(self):
        workers = []
        for worker_number in range(200):
            worker = StarsScraperWorker(worker_number, self.tasks_queue, self.scraped_actors, self.scraped_movies)
            worker.start()
            workers.append(worker)

        self.tasks_queue.join()

    def process_stars(self, movies):
        start_time = time.time()

        self.add_ranking_movies_to_scraped_movies(movies)

        if constants.USE_MOVIES_CHECKPOINT_STAR_SCRAPER:
            self.read_movies_from_checkpoint()

        if constants.USE_ACTORS_CHECKPOINT_STAR_SCRAPER:
            self.read_actors_from_checkpoint()
            self.logger.debug("Checkpoint readed")
            missing_scrape_actors = self.get_missing_actors_scrape(movies)
            self.logger.debug("Actors with scrape missing {}".format(missing_scrape_actors))
            self.create_tasks_for_missing_actors(missing_scrape_actors, movies)
            self.manage_scrape_actors()
        else:
            self.initialization(movies)
            self.manage_scrape_actors()

            df = pd.DataFrame.from_records(self.scraped_actors)
            df.to_csv("scraped_actors.csv", index=False)

        movies = self.calculate_stars(movies)

        total_time_elapsed = time.time() - start_time

        self.logger.debug("Total time whole scraping {:.3g} minutes".format(total_time_elapsed / 60))

        return movies