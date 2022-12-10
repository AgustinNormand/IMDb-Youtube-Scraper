import queue
import time
import pandas as pd
import logging
from second_source_scraper.StarsScraper.StarsScraperWorker import StarsScraperWorker


class StarsScraper:
    def __init__(self):
        self.scraped_movies = {}
        self.tasks_queue = queue.Queue()
        self.scraped_actors = {}
        self.logger = logging.getLogger("StarsScraper")

    def initialization(self, movies):
        self.logger.debug("Movies to scrape stars {}".format(len(movies)))

        self.actors_tasks = {}
        self.tasks = []
        small_task_number = 0
        for movie in movies:
            adapted_url = movie["url_imdb"].replace("imdb", "m.imdb")
            self.scraped_movies[adapted_url] = float(movie["user_raiting"])
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
            #break
        self.logger.debug("Tasks to resolve {}".format(task_number))


    def manage_scrape_actors(self):
        workers = []
        for worker_number in range(350):
            worker = StarsScraperWorker(worker_number, self.tasks_queue, self.scraped_actors, self.scraped_movies)
            worker.start()
            workers.append(worker)

        self.tasks_queue.join()

    def process_stars(self, movies):
        start_time = time.time()

        self.initialization(movies)

        self.manage_scrape_actors()

        df = pd.DataFrame.from_records(self.scraped_actors)
        df.to_csv("scraped_actors.csv", index=False)

        total_time_elapsed = time.time() - start_time

        self.logger.debug("Total time whole scraping {:.3g} minutes".format(total_time_elapsed / 60))

        return movies