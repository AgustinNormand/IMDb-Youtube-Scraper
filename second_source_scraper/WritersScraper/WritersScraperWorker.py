from threading import Thread
import logging
import time
from bs4 import BeautifulSoup
import constants
from fp.fp import FreeProxy
from fake_headers import Headers
from requests.adapters import HTTPAdapter, Retry
import requests




class WritersScraperWorker(Thread):
    def __init__(self, worker_number, tasks_queue, scraped_writers, scraped_movies):
        Thread.__init__(self)
        self.worker_number = worker_number
        self.tasks_queue = tasks_queue
        self.logger = logging.getLogger("WritersScraper")
        self.scraped_writers = scraped_writers
        self.scraped_movies = scraped_movies

    def configure_session(self):
        time.sleep(self.worker_number)
        retry = Retry(total=5, connect=5, backoff_factor=0.1, status_forcelist=[413, 429, 503, 500])
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

        try:
            r = self.session.get(url=url, proxies=self.proxies)
            text = r.text
            status_code = r.status_code
        except Exception as e:
            self.logger.error("Task Number {}, Exception {} in {}".format(self.task_number, e, url))
            return None

        if status_code != 200:
            self.logger.error("Task Number {}, Status code {} in {}".format(self.task_number, status_code, url))
            return None

        self.last_request_timestamp = time.time()
        return text

    def parse_writer_page_to_get_movies(self, text):
        soup = BeautifulSoup(text, "html.parser")
        movie_section = soup.find("section", {"id": "name-filmo-content"})
        divs_movies = movie_section.find_all("div", {"class": "col-xs-12"})
        movies = []
        for div_movie in divs_movies:
            href = div_movie.find("a", {"class": "subpage"})["href"].split("/?")[0]
            url = constants.ACTORS_IMDb_URL + href
            movies.append(url)
        return movies

    def get_movies_previous_to(self, movie_url, actor_movies):
        movie_url_title = movie_url.split("imdb.com")[1]
        found_movie = False
        previous_movies = []
        for actor_movie_url in actor_movies:
            actor_movie_url_title = actor_movie_url.split("imdb.com")[1]
            if found_movie:
                previous_movies.append(actor_movie_url)
            else:
                if movie_url_title == actor_movie_url_title:
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

    def scrape_writer(self, writer_url, writer_name):
        self.scraped_writers[writer_name] = {}
        self.scraped_writers[writer_name]["movies"] = []
        self.scraped_writers[writer_name]["star_before"] = []

        writer_url = writer_url + "filmotype/writer"

        response = self.request(writer_url)
        if response == None:
            return

        self.scraped_writers[writer_name]["movies"] = self.parse_writer_page_to_get_movies(response)
        self.scraped_writers[writer_name]["star_before"] = []

    def run(self):
        self.configure_session()
        while True:
            self.task_number, writer_tasks = self.tasks_queue.get()

            writer_name, writer_url, movie_url = writer_tasks[0]
            # with self.lock:
            self.logger.debug(
                "Task Received, Task Number {}, Writer {}".format(self.task_number, writer_name))

            if writer_name not in self.scraped_writers.keys():
                # with self.lock:
                self.logger.debug(
                    "Task Number {}, actor not in scraped actors, scraping {}, url {}".format(self.task_number, writer_name, writer_url))
                self.scrape_writer(writer_url, writer_name)
            else:
                # with self.lock:
                self.logger.warning(
                    "Task Number {}, writer {} was in scraped writers".format(self.task_number, writer_name))

            for writer_task in writer_tasks:
                writer_name, writer_url, movie_url = writer_task

                # with self.lock:
                self.logger.debug(
                    "Task Number {}, subtask was {} star before {}".format(self.task_number, writer_name,
                                                                           movie_url))

                previous_movies = self.get_movies_previous_to(movie_url, self.scraped_writers[writer_name]["movies"])
                #self.logger.debug("Movies previous to {}, are {}".format(movie_url, previous_movies))
                if previous_movies == []:
                    self.logger.warning("Previous movies empty {} {}".format(movie_url, writer_url))
                star_before_without_requesting = self.any_previous_is_in_scraped_with_more_than_75(previous_movies,
                                                                                                   self.scraped_movies)
                if star_before_without_requesting:
                    self.scraped_writers[writer_name]["star_before"].append(movie_url)
                    # with self.lock:
                    self.logger.debug("Task Number {}. Dont need to do any extra requests".format(self.task_number))

                else:
                    result = self.scrape_if_needed_previous_movies_raiting_until_75(previous_movies, self.scraped_movies)
                    if result:
                        self.scraped_writers[writer_name]["star_before"].append(movie_url)

            self.tasks_queue.task_done()
