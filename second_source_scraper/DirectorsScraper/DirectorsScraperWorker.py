from threading import Thread
import logging
import time
from bs4 import BeautifulSoup
import constants
from fp.fp import FreeProxy
from fake_headers import Headers
from requests.adapters import HTTPAdapter, Retry
import requests




class DirectorsScraperWorker(Thread):
    def __init__(self, worker_number, tasks_queue, scraped_directors, scraped_movies):
        Thread.__init__(self)
        self.worker_number = worker_number
        self.tasks_queue = tasks_queue
        self.logger = logging.getLogger("DirectorsScraper")
        self.scraped_directors = scraped_directors
        self.scraped_movies = scraped_movies

    def configure_session(self):
        time.sleep(self.worker_number)
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update(Headers().generate())
        self.get_proxy()
        self.last_request_timestamp = time.time()

    def request(self, url):
        remaining_to_second_between_requests = 0.1 - (
                time.time() - self.last_request_timestamp)
        if remaining_to_second_between_requests > 0:
            time.sleep(remaining_to_second_between_requests)

        r = self.session.get(url=url, proxies=self.proxies)
        if r.status_code != 200:
            #with self.lock:
            self.logger.debug("Task Number {}, Status code {} in {}".format(self.task_number, r.status_code, url))
            return None
        self.last_request_timestamp = time.time()
        return r.text

    def parse_director_page_to_get_movies(self, text):
        soup = BeautifulSoup(text, "html.parser")
        movie_section = soup.find("section", {"id": "name-filmo-content"})
        divs_movies = movie_section.find_all("div", {"class": "col-xs-12"})
        movies = []
        for div_movie in divs_movies:
            href = div_movie.find("a", {"class": "subpage"})["href"].split("/?")[0]
            url = constants.ACTORS_IMDb_URL + href
            movies.append(url)
        return movies

    def get_movies_previous_to(self, movie_url, director_movies):
        movie_url_title = movie_url.split("imdb.com")[1]
        found_movie = False
        previous_movies = []
        for director_movie_url in director_movies:
            director_movie_url_title = director_movie_url.split("imdb.com")[1]
            if found_movie:
                previous_movies.append(director_movie_url)
            else:
                if movie_url_title == director_movie_url_title:
                    found_movie = True
                else:
                    continue
        return previous_movies

    def any_previous_is_in_scraped_with_more_than_75(self, previous_movies, scraped_movies):
        for previous_movie in previous_movies:
            if previous_movie in scraped_movies.keys():
                if scraped_movies[previous_movie] >= 7.5:
                    return True
        return False

    def scrape_if_needed_previous_movies_raiting_until_75(self, previous_movies, scraped_movies):
        for previous_movie in previous_movies:
            if previous_movie in scraped_movies.keys():
                if scraped_movies[previous_movie] >= 7.5:
                    return True
            else:
                text = self.request(previous_movie)
                if text == None:
                    self.logger.error("None text {}".format(previous_movie))
                    continue
                soup = BeautifulSoup(text, "html.parser")
                div = soup.find("div", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
                if div != None:
                    raiting = float(div.find("span").get_text())
                    self.logger.debug("Task Number {}, requested {}, raiting {}".format(self.task_number, previous_movie, raiting))
                    self.scraped_movies[previous_movie] = raiting
                    if raiting >= 7.5:
                        return True
                else:
                    self.scraped_movies[previous_movie] = 0
                    self.logger.debug("Task Number {}, requested {}, raiting {}".format(self.task_number, previous_movie, 0))


        return False

    def get_proxy(self):
        try:
            proxy = FreeProxy(country_id=['AR'], rand=True, timeout=0.5).get()
            self.proxies = {
                "http": proxy
            }
        except Exception as e:
            try:
                proxy = FreeProxy( rand=True, timeout=0.5).get()
                self.proxies = {
                    "http": proxy
                }
            except Exception as e:
                time.sleep(20)
                self.get_proxy()

    def scrape_writer(self, director_url, director_name):
        self.scraped_directors[director_name] = {}
        self.scraped_directors[director_name]["movies"] = []
        self.scraped_directors[director_name]["star_before"] = []

        director_url = director_url + "filmotype/director"

        response = self.request(director_url)

        if response == None:
            time.sleep(60)
            response = self.request(director_url)
            if response == None:
                return

        self.scraped_directors[director_name]["movies"] = self.parse_director_page_to_get_movies(response)
        self.scraped_directors[director_name]["star_before"] = []

    def run(self):
        self.configure_session()
        while True:
            self.task_number, director_tasks = self.tasks_queue.get()

            director_name, director_url, movie_url = director_tasks[0]
            # with self.lock:
            self.logger.debug(
                "Task Received, Task Number {}, Director {}".format(self.task_number, director_name))

            if director_name not in self.scraped_directors.keys():
                # with self.lock:
                self.logger.debug(
                    "Task Number {}, actor not in scraped directors, scraping {}, url {}".format(self.task_number, director_name, director_url))
                self.scrape_writer(director_url, director_name)
            else:
                # with self.lock:
                self.logger.warning(
                    "Task Number {}, writer {} was in scraped directors".format(self.task_number, director_name))

            for director_task in director_tasks:
                director_name, director_url, movie_url = director_task

                # with self.lock:
                self.logger.debug(
                    "Task Number {}, subtask was {} star before {}".format(self.task_number, director_name,
                                                                           movie_url))

                previous_movies = self.get_movies_previous_to(movie_url, self.scraped_directors[director_name]["movies"])
                #self.logger.debug("Movies previous to {}, are {}".format(movie_url, previous_movies))
                if previous_movies == []:
                    self.logger.warning("Previous movies empty {} {}".format(movie_url, director_url))
                star_before_without_requesting = self.any_previous_is_in_scraped_with_more_than_75(previous_movies,
                                                                                                   self.scraped_movies)
                if star_before_without_requesting:
                    self.scraped_directors[director_name]["star_before"].append(movie_url)
                    # with self.lock:
                    self.logger.debug("Task Number {}. Dont need to do any extra requests".format(self.task_number))

                else:
                    result = self.scrape_if_needed_previous_movies_raiting_until_75(previous_movies, self.scraped_movies)
                    if result:
                        self.scraped_directors[director_name]["star_before"].append(movie_url)

            self.tasks_queue.task_done()
