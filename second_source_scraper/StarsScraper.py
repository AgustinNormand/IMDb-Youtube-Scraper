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
        self.logger = logging.getLogger("SecondSourceScraperStarsScraper")
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
                #actor_url = constants.ACTORS_IMDb_URL + href + "filmotype/actress"
            actors.append((actor_name, actor_url))
        return actors

    def scrape_movie(self, movie_url):
        status_code_movie, text_response_movie = self.request(movie_url)

        if status_code_movie != 200:
            self.logger.error("Status code {}, Movie URL {}".format(status_code_movie, movie_url))
            return None

        soup = BeautifulSoup(text_response_movie, "html.parser")

        div = soup.find("div", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
        if div != None:
            raiting = float(div.find("span").get_text())
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
            if len(divs_movies) == 0:
                if "actor" in actor_url:
                    self.logger.debug("Movies in 0, scraping actress page")
                    self.scrape_actor(actor_name, actor_url.replace("actor", "actress"))
            else:
                for div_movie in divs_movies:
                    href = div_movie.find("a", {"class": "subpage"})["href"].split("/?")[0]
                    url = constants.ACTORS_IMDb_URL + href
                    self.scraped_actors[actor_name].append(url)
        except Exception as e:
            self.logger.error("Exception {}, scraping {}".format(e, actor_url))


    def scrape_actors_if_needed(self, actors):
        for actor in actors:
            actor_name = actor[0]
            actor_url = actor[1]
            if actor_name not in self.scraped_actors.keys():
                self.logger.debug("Actor {} not in scraped_actors, scraping in what movies acted".format(actor_name))
                self.scrape_actor(actor_name, actor_url)
            else:
                self.logger.debug("Actor {} was already scraped, not need to see in what movies acted".format(actor_name))
            #break  # Delte this

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
        if not found_movie:
            self.logger.error("Movie never founded {} in {}".format(movie_url, actor_movies))
        return previous_movies

    def star_before(self, movie, actor_name):
        self.logger.debug("Verifying if {}, was an actor before {}".format(actor_name, movie["movie_name"]))
        previous_movies = self.get_movies_previous_to(movie["url_imdb"], self.scraped_actors[actor_name])

        self.logger.debug("Previous movies of actor {} before {}".format(previous_movies, movie["movie_name"]))

        for previous_movie in previous_movies:
            if previous_movie not in self.scraped_movies:
                self.logger.debug("Movie not in scraped_movies, scraping raiting of {}".format(previous_movie))
                self.scrape_movie(previous_movie)
            else:
                self.logger.debug("Movie in scraped_movies, dont need to scrape raiting of {}".format(previous_movie))

            if self.scraped_movies[previous_movie] == None:
                self.logger.error("Movie without raiting {}".format(previous_movie))
            else:
                if self.scraped_movies[previous_movie] >= 7.5:
                    self.logger.debug("Movie found that proves is a star, stop looking")
                    return True
        return False

    def process_actors(self, actors, movie):
        star_count = 0
        for actor_tuple in actors:
            actor_name = actor_tuple[0]
            if self.star_before(movie, actor_name):
                star_count += 1
            #break

        return star_count

    def scrape_stars(self, soup, movie):
        self.logger.debug("Processing {}".format(movie["movie_name"]))
        actors = self.get_actors(soup)
        self.logger.debug("Actors {}".format(actors))

        self.scrape_actors_if_needed(actors)
        #{'Robert Downey Jr.': ['https://m.imdb.com/title/tt18392014', 'https://m.imdb.com/title/tt2094116',
        #                       'https://m.imdb.com/title/tt14404618',

        star_count = self.process_actors(actors, movie)
        movie["movie_star"] = star_count
        self.logger.debug("Star Count of {} is {}".format(movie["movie_name"], star_count))
        return movie