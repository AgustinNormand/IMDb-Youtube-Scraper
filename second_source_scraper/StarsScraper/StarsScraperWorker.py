from threading import Thread
import logging
import time
from bs4 import BeautifulSoup
import constants
from fp.fp import FreeProxy
from fake_headers import Headers
from requests.adapters import HTTPAdapter, Retry
import requests




class StarsScraperWorker(Thread):
    def __init__(self, worker_number, tasks_queue, scraped_actors, scraped_movies):
        Thread.__init__(self)
        self.worker_number = worker_number
        self.tasks_queue = tasks_queue
        self.logger = logging.getLogger("StarsScraper")
        self.scraped_actors = scraped_actors
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

    def contains_actor_or_actress_filter(self, soup):
        scroller = soup.find("div", {"class":"ipc-chip-list__scroller"})
        if scroller == None:
            return False

        return ((scroller.find("button", {"id":"name-filmography-filter-actor"}) != None) or (scroller.find("button", {"id":"name-filmography-filter-actress"}) != None))

    def contains_filmo_section_actor_or_actress(self, soup):
        return ((soup.find("div", "filmo-section-actor") != None) or (soup.find("div", "filmo-section-actress") != None))

    def get_actor_url(self, soup, actor_url):
        div_filmo = soup.find("div", "filmo-section-actor")
        if div_filmo != None:
            return actor_url + "filmotype/actor"

        div_filmo = soup.find("div", "filmo-section-actress")
        if div_filmo != None:
            return actor_url + "filmotype/actress"

        scroller = soup.find("div", {"class": "ipc-chip-list__scroller"})
        if scroller.find("button", {"id":"name-filmography-filter-actor"}) != None:
            return actor_url + "filmotype/actor"

        if scroller.find("button", {"id": "name-filmography-filter-actress"}) != None:
            return actor_url + "filmotype/actress"

        return None #No pude pasar que llegue aca porque se checkeo antes con un if

    def parse_actor_page_to_get_url(self, text, actor_url, actor_name):
        try:
            soup = BeautifulSoup(text, "html.parser")
            if self.contains_filmo_section_actor_or_actress(soup):
                self.scraped_actors[actor_name]["url"] = self.get_actor_url(soup, actor_url)
                #with self.lock:
                self.logger.debug(
                        "Scraped {}, generic url {}, contains {}, specific url {}".format(
                            actor_name, actor_url, "filmo_section_actor_or_actress",
                            self.scraped_actors[actor_name]["url"]))
            elif self.contains_actor_or_actress_filter(soup):
                self.scraped_actors[actor_name]["url"] = self.get_actor_url(soup, actor_url)
                #with self.lock:
                self.logger.debug(
                            "Scraping {}, generic url {}, not contain {}, but contains {}, specific url {}".format(
                                actor_name, actor_url, "filmo_section_actor_or_actress",
                                "actor_filter or actress_filter",  self.scraped_actors[actor_name]["url"]
                                ))
            else:
                #with self.lock:
                self.logger.debug("Scraping {}, generic url {}, not contemplated case".format(actor_name, actor_url))
                self.scraped_actors[actor_name]["url"] = None

        except Exception as e:
            #with self.lock:
            self.logger.debug("Exception {} processing {}".format(e, actor_url))

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

    def parse_actor_page_to_get_movies(self, text):
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

    def scrape_actor(self, actor_url, actor_name):
        self.scraped_actors[actor_name] = {}
        self.scraped_actors[actor_name]["movies"] = []
        self.scraped_actors[actor_name]["star_before"] = []
        if actor_url == None:
            return

        response = self.request(actor_url)
        if response == None:
            time.sleep(60)
            response = self.request(actor_url)
            if response == None:
                return

        self.parse_actor_page_to_get_url(response, actor_url, actor_name)

        if self.scraped_actors[actor_name]["url"] == None:
            return

        response = self.request(self.scraped_actors[actor_name]["url"])

        if response == None:
            time.sleep(60)
            response = self.request(self.scraped_actors[actor_name]["url"])
            if response == None:
                return

        self.scraped_actors[actor_name]["movies"] = self.parse_actor_page_to_get_movies(response)
        self.scraped_actors[actor_name]["star_before"] = []

    def run(self):
        self.configure_session()
        while True:
            self.task_number, actor_tasks = self.tasks_queue.get()

            actor_name, actor_url, movie_url = actor_tasks[0]
            # with self.lock:
            self.logger.debug(
                "Task Received, Task Number {}, Actor {}".format(self.task_number, actor_name))

            if actor_name not in self.scraped_actors.keys():
                # with self.lock:
                self.logger.debug(
                    "Task Number {}, actor not in scraped actors, scraping {}".format(self.task_number, actor_name))
                self.scrape_actor(actor_url, actor_name)
            else:
                # with self.lock:
                self.logger.debug(
                    "Task Number {}, actor {} was in scraped actors".format(self.task_number, actor_name))

            for actor_task in actor_tasks:
                actor_name, actor_url, movie_url = actor_task

                # with self.lock:
                self.logger.debug(
                    "Task Number {}, subtask was {} star before {}".format(self.task_number, actor_name,
                                                                           movie_url))

                previous_movies = self.get_movies_previous_to(movie_url, self.scraped_actors[actor_name]["movies"])
                star_before_without_requesting = self.any_previous_is_in_scraped_with_more_than_75(previous_movies,
                                                                                                   self.scraped_movies)
                if star_before_without_requesting:
                    self.scraped_actors[actor_name]["star_before"].append(movie_url)
                    # with self.lock:
                    self.logger.debug("Task Number {}. Dont need to do any extra requests".format(self.task_number))

                else:
                    result = self.scrape_if_needed_previous_movies_raiting_until_75(previous_movies, self.scraped_movies)
                    if result:
                        self.scraped_actors[actor_name]["star_before"].append(movie_url)

            self.tasks_queue.task_done()
