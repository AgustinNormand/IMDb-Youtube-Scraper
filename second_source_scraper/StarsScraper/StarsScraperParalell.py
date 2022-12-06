import constants
import time
import requests
from fake_headers import Headers
import logging
from requests.adapters import HTTPAdapter, Retry
from second_source_scraper.StarsScraper.ActorScraper import ActorScraper


class StarsScraperParalell:
    def __init__(self):
        self.scraped_actors = {}
        self.last_request_timestamp = time.time()
        self.logger = logging.getLogger("StarsScraper")
        self.time_elapsed_waiting_http_response = 0
        self.scraped_movies = {}
        self.actor_scraper = ActorScraper()

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
            actors.append((actor_name, actor_url))
        return actors

    def get_actors_that_need_scrape(self, actors):
        name_actors_that_need_scrape = []
        url_actors_that_need_scrape = []
        for actor in actors:
            actor_name = actor[0]
            actor_url = actor[1]
            if actor_name not in self.scraped_actors.keys():
                url_actors_that_need_scrape.append(actor_url)
                name_actors_that_need_scrape.append(actor_name)
        return [name_actors_that_need_scrape, url_actors_that_need_scrape]

    def scrape_actors_that_need_scrape(self, names, urls, movie_url):
        self.scraped_actors, self.scraped_movies, star_count = self.actor_scraper.scrape_actors(names, urls, self.scraped_actors, movie_url, self.scraped_movies)
        return star_count

    def scrape_stars(self, soup, movie):
        self.logger.debug("Processing {}".format(movie["movie_name"]))
        actors = self.get_actors(soup)
        self.logger.debug("Actors {}".format(actors))

        #self.scrape_actors_if_needed(actors)
        names, urls = self.get_actors_that_need_scrape(actors)

        star_count = self.scrape_actors_that_need_scrape(names, urls, movie["url_imdb"])


        #rs = (grequests.get(u) for u in actors_that_need_scrape)


        #{'Robert Downey Jr.': ['https://m.imdb.com/title/tt18392014', 'https://m.imdb.com/title/tt2094116',
        #                       'https://m.imdb.com/title/tt14404618',

        #star_count = self.process_actors(actors, movie)
        movie["movie_star"] = star_count
        self.logger.debug("Star Count of {} is {}".format(movie["movie_name"], star_count))
        return movie
