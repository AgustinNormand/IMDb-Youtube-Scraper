import queue
from threading import Thread, Lock
from fp.fp import FreeProxy
from requests.adapters import HTTPAdapter, Retry
import requests
import time
from fake_headers import Headers
from bs4 import BeautifulSoup
import pandas as pd
import logging
import constants


class StarsScraper:
    def __init__(self):
        self.scraped_movies = {}
        self.actors_to_scrape_queue = queue.Queue()
        self.scraped_actors = {}
        self.logger = logging.getLogger("StarsScraper")

    def initialization(self, movies):
        self.logger.debug("Movies to scrape stars {}".format(len(movies)))

        self.actors_to_scrape = []
        for movie in movies:
            self.scraped_movies[movie["url_imdb"]] = movie["user_raiting"]
            for (actor_name, actor_url) in movie["actors"]:
                if (actor_name, actor_url) not in self.actors_to_scrape:
                    if actor_name == "Lance Palmer": #Delete #TODO
                        self.actors_to_scrape.append((actor_name, actor_url))

        self.logger.debug("Actors to scrape {}".format(len(self.actors_to_scrape)))

        for actor_to_scrape in self.actors_to_scrape:
            self.actors_to_scrape_queue.put(actor_to_scrape)

    def manage_scrape_actors(self):
        lock = Lock()
        threads = []
        for worker_number in range(1): #Change to 100 #TODO
            thread = Thread(target=self.scrape_actors, daemon=True, args=(lock,worker_number,))
            threads.append(thread)
            thread.start()

        self.actors_to_scrape_queue.join()

    def contains_actor_or_actress_filter(self, soup): #Esto va a ActorScraper
        scroller = soup.find("div", {"class":"ipc-chip-list__scroller"})
        if scroller == None:
            return False

        return ((scroller.find("button", {"id":"name-filmography-filter-actor"}) != None) or (scroller.find("button", {"id":"name-filmography-filter-actress"}) != None))

    def contains_filmo_section_actor_or_actress(self, soup):#Esto va a ActorScraper
        return ((soup.find("div", "filmo-section-actor") != None) or (soup.find("div", "filmo-section-actress") != None))

    def contains_see_more_button(self, soup):#Esto va a ActorScraper
        return soup.find("span", {"class":"ipc-see-more__text"}) != None

    def get_actor_url(self, soup, actor_url):#Esto va a ActorScraper
        div_filmo = soup.find("div", "filmo-section-actor")
        if div_filmo != None:
            return actor_url + "filmotype/actor"

        div_filmo = soup.find("div", "filmo-section-actress")
        if div_filmo != None:
            return actor_url + "filmotype/actress"

    def get_movies_from_acordeon(self, previous_movies):#Esto va a ActorScraper
        movie_result_list = []
        movies = previous_movies.find("ul", {"class": "ipc-metadata-list"}).find_all("li", {
            "class": "ipc-metadata-list-summary-item"})
        for movie in movies:
            movie_dict = {}
            movie_dict["movie_name"] = movie.find("a")["aria-label"]
            movie_dict["movie_url"] = constants.IMDb_URL + movie.find("a")["href"].split("/?")[0]
            movie_result_list.append(movie_dict)
        return movie_result_list

    def contains_filmo_section_self(self, soup):#Esto va a ActorScraper
        return soup.find("div", {"class":"filmo-section-self"}) != None

    def get_previous_movies(self, soup):
        movies_section = soup.find("div", {"class": ["sc-4390696d-3", "khLxUB"]})
        acordeon_title = movies_section.find("span", {"class": "ipc-accordion__item__title"}).find("li").get_text()
        acordeon = None
        if acordeon_title == "Upcoming":
            acordeon = movies_section.find_all("div", {"class": "ipc-accordion__item__content"})[1]
        if acordeon_title == "Previous":
            acordeon = movies_section.find_all("div", {"class": "ipc-accordion__item__content"})[0]
        #return


    def parse_actor_page(self, text, actor_url, actor_name, lock):#Esto va a ActorScraper
        try:
            self.scraped_actors[actor_name] = {}
            soup = BeautifulSoup(text, "html.parser")
            if self.contains_filmo_section_actor_or_actress(soup):
                previous_movies = self.get_previous_movies(soup)
                self.scraped_actors[actor_name]["completed_scrape"] = not self.contains_see_more_button(previous_movies)
                self.scraped_actors[actor_name]["url"] = self.get_actor_url(soup, actor_url)
                self.scraped_actors[actor_name]["movies"] = self.get_movies_from_acordeon(previous_movies)
                with lock:
                    self.logger.debug(
                        "Scraped {}, generic url {}, contains {}, completed_scrape {}, specific url {}, movies {}".format(
                            actor_name, actor_url, "filmo_section_actor_or_actress",
                            self.scraped_actors[actor_name]["completed_scrape"],
                            self.scraped_actors[actor_name]["url"], self.scraped_actors[actor_name]["movies"]))
            elif self.contains_actor_or_actress_filter(soup):
                    with lock:
                        self.logger.debug(
                            "Scraping {}, generic url {}, not contain {}, but contains {}".format(
                                actor_name, actor_url, "filmo_section_actor_or_actress",
                                "actor_filter or actress_filter"
                                ))
            elif self.contains_filmo_section_self(soup):
                    with lock:
                        self.logger.debug(
                            "Scraping {}, generic url {}, not contain {}, not contain {}, contains {}, is this an actor?".format(
                                actor_name, actor_url, "filmo_section_actor_or_actress",
                                "actor_filter or actress_filter",
                                "filmo_section_self",
                                ))
                    self.scraped_actors[actor_name]["completed_scrape"] = True
                    self.scraped_actors[actor_name]["url"] = actor_url
                    self.scraped_actors[actor_name]["movies"] = []
            else:
                self.logger.debug("Scraping {}, generic url {}, not contemplated case".format(actor_name, actor_url))
                self.scraped_actors[actor_name]["completed_scrape"] = True
                self.scraped_actors[actor_name]["url"] = actor_url
                self.scraped_actors[actor_name]["movies"] = []

        except Exception as e:
            self.logger.debug("Exception {} processing {}".format(e, actor_url))

    def scrape_actors(self, lock, worker_number): #Esto va a ActorScraper
        time.sleep(worker_number*2)
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        session.headers.update(Headers().generate())
        proxy = FreeProxy(country_id=['AR'], rand=True, timeout=0.5).get()
        proxies = {
            "http": proxy
        }
        last_request_timestamp = time.time()

        while True:
            actor_name, actor_url = self.actors_to_scrape_queue.get()

            remaining_to_second_between_requests = 0.1 - (
                    time.time() - last_request_timestamp)
            if remaining_to_second_between_requests > 0:
                time.sleep(remaining_to_second_between_requests)

            r = session.get(url=actor_url, proxies=proxies)
            if r.status_code != 200:
                self.logger.debug("Status code {}".format(r.status_code))
            self.parse_actor_page(r.text, actor_url, actor_name, lock)
            #self.logger.debug("Requests url {}, status {}, actor name {}".format(actor_url, r.status_code, actor_name))

            last_request_timestamp = time.time()

            self.actors_to_scrape_queue.task_done()

    def process_stars(self, movies):
        #self.logger.debug("In process stars")
        #self.logger.debug(movies)
        start_time = time.time()

        self.initialization(movies)

        self.manage_scrape_actors()

        df = pd.DataFrame.from_records(self.scraped_actors)
        df.to_csv("scraped_actors.csv", index=False)

        #self.logger.debug(self.scraped_actors)
        total_time_elapsed = time.time() - start_time

        self.logger.debug("Total time whole scraping {:.3g} minutes".format(total_time_elapsed / 60))



        return movies