import logging
from fake_headers import Headers
import requests
import time
import urllib.parse
from bs4 import BeautifulSoup


IMDb_URL = "https://www.imdb.com"

class IMDbScraper():
    def __init__(self):
        self.logger = logging.getLogger("SecondSourceScraper")
        self.time_elapsed_waiting_http_response = 0
        self.total_movie_pages_scraped = 0

    def request(self, url):
        start_time_waiting_response = time.time()
        r = requests.get(headers=Headers().generate(), url=url)
        time_elapsed = time.time() - start_time_waiting_response
        self.time_elapsed_waiting_http_response += time_elapsed
        self.logger.debug("New request to IMDb effectuated, "
                          "URL {}, "
                          "Status Code {}, "
                          "Response len {}, "
                          "Time elapsed waiting response {}".format(url, r.status_code, len(r.text), time_elapsed))
        return [r.status_code, r.text]

    def generate_imdb_query_url(self, movie):
        encoded_name = urllib.parse.quote_plus(movie["movie_name"])
        query_url_imdb = "{}/find?q={}&ref_=nv_sr_sm".format(IMDb_URL, encoded_name)
        return query_url_imdb

    def process_query_results(self, soup):
        anchor = soup.find("a", {"class": "ipc-metadata-list-summary-item__t"})
        if anchor != None:
            return "{}{}".format(IMDb_URL, anchor["href"])

        anchor = soup.find("td", {"class":"result_text"}).find("a")
        if anchor != None:
            return "{}{}".format(IMDb_URL, anchor["href"])

        with open("imdb_query_results.html", "w") as f:
            f.write(str(soup))
        logging.error("Link not found in results. File Writed to debug imdb_query_results.html")

        # TODO Analyze this links

    def get_raiting(self, soup, movie):
        div = soup.find("div", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
        return div.find("span").get_text()

    def process_content_review(self, soup, movie):
        ul = soup.find("ul", {"data-testid":"reviewContent-all-reviews"})
        user_reviews_li, critic_reviews_li, critic_rating_li = ul.find_all("li")
        #critic_rating_ul.find("span", {"class":"score"})
        #print(critic_rating_ul)

        # TODO Request user_reviews_ul.find("a")["href"] to get exact value

        movie["user_reviews"] = user_reviews_li.find("span", {"class": "score"}).get_text()
        movie["critic_reviews"] = critic_reviews_li.find("span", {"class":"score"}).get_text()
        movie["critic_rating"] = critic_rating_li.find("span", {"class":"score-meta"}).get_text()
        return movie


    def process_movie_page(self, soup, movie):
        movie["user_raiting"] = self.get_raiting(soup, movie)
        movie = self.process_content_review(soup, movie)

        return movie

    def scrape_movie(self, movie):
        query_url_imdb = self.generate_imdb_query_url(movie)
        status_code, text_response = self.request(query_url_imdb)

        if status_code != 200:
            self.logger.error("Status code {} in {}".format(status_code, movie))
            return None

        start_time_parsing = time.time()
        soup = BeautifulSoup(text_response, "html.parser")

        movie["url_imdb"] = self.process_query_results(soup)
        status_code, text_response = self.request(movie["url_imdb"])

        if status_code != 200:
            self.logger.error("Status code {}, URL {}, Movie {}".format(status_code, movie["url_imdb"], movie))
            return None

        soup = BeautifulSoup(text_response, "html.parser")
        movie = self.process_movie_page(soup, movie)


        return movie