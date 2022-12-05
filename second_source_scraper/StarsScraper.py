from selenium.webdriver.support.wait import WebDriverWait

import constants
import time
import requests
from fake_headers import Headers
import logging
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

class StarsScraper:
    def __init__(self):
        self.scraped_actors = {}
        self.last_request_timestamp = time.time()
        self.logger = logging.getLogger("SecondSourceScraper")
        self.time_elapsed_waiting_http_response = 0
        self.scraped_movies = {}

        self.session = requests.Session()
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update(Headers().generate())

    def sleep_if_needed(self):
        remaining_to_second_between_requests = constants.SECONDS_TO_SLEEP_BETWEEN_REQUESTS - (
                    time.time() - self.last_request_timestamp)
        if remaining_to_second_between_requests > 0:
            time.sleep(remaining_to_second_between_requests)

    def request(self, url):
        start_time_waiting_response = time.time()

        self.sleep_if_needed()
        time_between_requests = time.time() - self.last_request_timestamp
        #r = requests.get(headers=Headers().generate(), url=url)
        r = self.session.get(url=url)
        self.last_request_timestamp = time.time()

        time_elapsed = time.time() - start_time_waiting_response
        self.time_elapsed_waiting_http_response += time_elapsed
        self.logger.debug("New request to IMDb effectuated, "
                          "URL {}, "
                          "Status Code {}, "
                          "Response len {}, "
                          "Time elapsed waiting response {}, "
                          "Time between requests {}".format(url, r.status_code, len(r.text), time_elapsed, time_between_requests))
        return [r.status_code, r.text]

    def get_actors(self, soup):
        actors = []
        divs_actors = soup.find_all("div", {"data-testid":"title-cast-item"})
        for div_actor in divs_actors:
            ancor = div_actor.find("a", {"data-testid":"title-cast-item__actor"})
            actor_name = ancor.get_text()
            href = ancor["href"].split("?")[0]
            actor_url = constants.ACTORS_IMDb_URL + href + "filmotype/actor"
            #print(actor_url)
            actors.append((actor_name, actor_url))
        return actors

    def star_before(self, movie, actor_name):
        for actor_movie in reversed(self.scraped_actors[actor_name]):
            if actor_movie["name"] == movie["movie_name"]:
                break
            if actor_movie["raiting"] >= 7.5:
                return True
        return False

    def scrape_movie(self, movie_url):
        status_code_movie, text_response_movie = self.request(movie_url)

        if status_code_movie != 200:
            self.logger.error("Status code {}, Movie URL {}".format(status_code_movie, movie_url))
            return None

        soup = BeautifulSoup(text_response_movie, "html.parser")

        div = soup.find("div", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
        if div != None:
            raiting = float(div.find("span").get_text())
            #print("Raiting {}, Movie {}".format(raiting, movie_url))
            self.scraped_movies[movie_url] = raiting
        else:
            self.scraped_movies[movie_url] = None

    def scrape_actor(self, actor_name, actor_url):
        status_code_movie, text_response_movie = self.request(actor_url)

        if status_code_movie != 200:
            self.logger.error("Status code {}, URL {}, Actor {}".format(status_code_movie, actor_url, actor_name))

        try:
            soup = BeautifulSoup(text_response_movie, "html.parser")
            actor_name = soup.find("h5", {"itemprop":"name"}).find("a").get_text()
            self.scraped_actors[actor_name] = []
            movie_section = soup.find("section", {"id":"name-filmo-content"})
            divs_movies = movie_section.find_all("div", {"class":"col-xs-12"})
            for div_movie in divs_movies:
                href = div_movie.find("a", {"class": "subpage"})["href"]
                url = constants.ACTORS_IMDb_URL + href
                self.scraped_actors[actor_name].append(url)
                if url not in self.scraped_movies.keys():
                    self.scrape_movie(url)
        except Exception as e:
            print("Exception {}, scraping {}".format(e))


    def process_actors(self, actors, movie):
        star_count = 0
        for actor in actors:
            actor_name = actor[0]
            actor_url = actor[1]
            if actor_name not in self.scraped_actors.keys():
                self.scrape_actor(actor_name, actor_url)

            print(movie["url_imdb"])
            if self.star_before(movie, actor_name):
                print("{} was a star before {}".format(actor_name, movie))

            break  # Delte this

    def scrape_stars(self, soup, movie):
        actors = self.get_actors(soup)
        self.process_actors(actors, movie)
        movie["movie_star"] = 0
        return movie
