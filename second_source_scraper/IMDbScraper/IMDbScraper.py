import logging
from fake_headers import Headers
import requests
import time
from bs4 import BeautifulSoup
import constants
from requests.adapters import HTTPAdapter, Retry

class IMDbScraper():
    def __init__(self):
        self.logger = logging.getLogger("IMDbScraper")
        self.time_elapsed_waiting_http_response = 0
        self.total_movie_pages_scraped = 0
        self.last_request_timestamp = time.time()

        self.session = requests.Session()
        retry = Retry(connect=5, backoff_factor=0.5, status_forcelist=[413, 429, 503, 500])
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

    def get_raiting(self, soup, movie):
        try:
            div = soup.find("div", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
            return float(div.find("span").get_text())
        except Exception as e:
            return 0

    def process_user_reviews(self, li):
        try:
            return int(li.find("span", {"class": "score"}).get_text())
        except ValueError:
            pass

        text_response_user_reviews = None
        try:
            href = li.find("a")["href"]
            users_review_url = constants.IMDb_URL + href
            status_code_user_reviews, text_response_user_reviews = self.request(users_review_url)
            soup = BeautifulSoup(text_response_user_reviews, "html.parser")
            header = soup.find("div", {"class":"header"})
            return int(header.find("span").get_text().split("Reviews")[0].replace(",", ""))
        except Exception as e:
            self.logger.error("Exception {} processing user reviews, Writing text_response_user_reviews.html if is defined".format(e))
            if text_response_user_reviews != None:
                with open("./second_source_scraper/text_response_user_reviews.html", "w") as f:
                    f.write(text_response_user_reviews)
            return None

    def complete_none_content_review(self, movie):
        keys = ["critic_rating", "critic_reviews", "user_reviews"]
        for key in keys:
            if key not in movie.keys():
                movie[key] = None
        return movie

    def process_content_review(self, soup, movie):
        ul = soup.find("ul", {"data-testid":"reviewContent-all-reviews"})
        if ul != None:
            for li in ul.find_all("li"):
                label = li.find("span", {"class":"label"}).get_text().lower()
                if label == "metascore":
                    movie["critic_rating"] = int(li.find("span", {"class": "score-meta"}).get_text())
                if label == "critic reviews":
                    movie["critic_reviews"] = int(li.find("span", {"class": "score"}).get_text())
                if label == "user reviews":
                    movie["user_reviews"] = self.process_user_reviews(li)

                movie = self.complete_none_content_review(movie)
        else:
            movie = self.complete_none_content_review(movie)
        return movie

    def process_trailers(self, movie):
        trailers_url = movie["url_imdb"] + "/videogallery/content_type-trailer/"
        status_code_movie, text_response_movie = self.request(trailers_url)
        if status_code_movie != 200:
            self.logger.error("Status code {}, URL {}, Movie {}".format(status_code_movie, trailers_url, movie))
            return None

        soup = BeautifulSoup(text_response_movie, "html.parser")
        print(soup.find("div", {"class":"search-results"}))

        return movie

    def scrape_actors(self, soup, movie):
        actors = []
        divs_actors = soup.find_all("div", {"data-testid": "title-cast-item"})
        for div_actor in divs_actors:
            ancor = div_actor.find("a", {"data-testid": "title-cast-item__actor"})
            actor_name = ancor.get_text()
            href = ancor["href"].split("?")[0]
            actor_url = constants.ACTORS_IMDb_URL + href
            actors.append((actor_name, actor_url))
        movie["actors"] = actors
        return movie

    def scrape_directors(self, li_presentation, movie):
        directors = []
        for ancor in li_presentation.find_all("a", {"class":"ipc-metadata-list-item__list-content-item"}):
            director_name = ancor.get_text().strip()
            href = ancor["href"].split("?")[0]
            director_url = constants.ACTORS_IMDb_URL + href
            directors.append((director_name, director_url))
        movie["directors"] = directors
        return movie

    def scrape_writers(self, li_presentation, movie):
        writers = []
        for ancor in li_presentation.find_all("a", {"class":"ipc-metadata-list-item__list-content-item"}):
            writer_name = ancor.get_text().strip()
            if writer_name == "Writers":
                continue
            href = ancor["href"].split("?")[0]
            writer_url = constants.ACTORS_IMDb_URL + href
            writers.append((writer_name, writer_url))
        movie["writers"] = writers
        return movie


    def process_movie_page(self, soup, movie):
        movie["user_raiting"] = self.get_raiting(soup, movie)
        movie = self.process_content_review(soup, movie)
        movie = self.scrape_actors(soup, movie)
        section_title_cast = soup.find("section", {"data-testid":"title-cast"})
        writers_scraped = False
        directors_scraped = False
        movie["writers"] = []
        movie["directors"] = []

        if section_title_cast != None:
            for li_presentation in section_title_cast.find_all("li", {"role":"presentation", "class":"ipc-metadata-list__item"}):
                label = li_presentation.find("button", {"class":"ipc-metadata-list-item__label"})
                if label == None:
                    label = li_presentation.find("a", {"class": "ipc-metadata-list-item__label"})

                if label != None:
                    label = label.get_text().strip()
                    if label == "Directors" or label == "Director":
                        movie = self.scrape_directors(li_presentation, movie)
                        directors_scraped = True
                    if label == "Writers" or label == "Writer":
                        movie = self.scrape_writers(li_presentation, movie)
                        writers_scraped = True

        if not (writers_scraped and directors_scraped):
            self.logger.warning("Writers or directors not scraped in {}".format(movie))

        return movie

    def scrape_movie(self, movie):
        text_response_movie = None
        try:
            status_code_movie, text_response_movie = self.request(movie["url_imdb"])
            if status_code_movie != 200:
                self.logger.error("Status code {}, URL {}, Movie {}".format(status_code_movie, movie["url_imdb"], movie))
                return None
            soup = BeautifulSoup(text_response_movie, "html.parser")
            movie = self.process_movie_page(soup, movie)

            return movie
        except Exception as e:
            self.logger.error("Exception {}, Movie {}, Writing text_response_movie.html if is defined".format(e, movie))
            if text_response_movie != None:
                with open("./second_source_scraper/text_response_movie.html", "w") as f:
                    f.write(text_response_movie)
            return None