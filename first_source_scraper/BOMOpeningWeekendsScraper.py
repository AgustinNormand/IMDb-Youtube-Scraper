import requests
from fake_headers import Headers
from bs4 import BeautifulSoup
import time
import logging
import constants


class BOMOpeningWeekendsScraper:
    def __init__(self):
        self.logger = logging.getLogger("FirstSourceScraper")
        self.total_pages_scraped = 0
        self.incremental_id = 0
        self.time_elapsed_parsing = 0
        self.time_elapsed_waiting_http_response = 0
        self.last_request_timestamp = time.time()

    def sleep_if_needed(self):
        remaining_to_second_between_requests = constants.SECONDS_TO_SLEEP_BETWEEN_REQUESTS - (time.time() - self.last_request_timestamp)
        if remaining_to_second_between_requests > 0:
            time.sleep(remaining_to_second_between_requests)

    def request_mojo_page(self, offset):
        url_with_offset = "{}?offset={}".format(self.url, offset)
        start_time_waiting_response = time.time()

        self.sleep_if_needed()
        time_between_requests = time.time() - self.last_request_timestamp
        r = requests.get(headers=Headers().generate(), url=url_with_offset)
        self.last_request_timestamp = time.time()
        time_elapsed = time.time() - start_time_waiting_response
        self.time_elapsed_waiting_http_response += time_elapsed

        self.logger.debug("New request of page effectuated, "
                          "URL {}, "
                          "Status Code {}, "
                          "Requested with offset {}, "
                          "Response len {}, "
                          "Time elapsed waiting response {}, "
                          "Time between requests {}".format(url_with_offset, r.status_code, offset, len(r.text), time_elapsed, time_between_requests))
        return [r.status_code, r.text]

    def parse_response_page_mojo(self, html_response):
        soup = BeautifulSoup(html_response, "html.parser")
        table = soup.find("div", {"id": "table"})
        release_fields = table.find_all("td", {"class": "mojo-field-type-release"})

        movies = []
        for release_field in release_fields:
            movie_name = release_field.text
            movie = {}
            movie["uniqueID"] = self.incremental_id
            movie["movie_name"] = movie_name
            movie["url_bom"] = constants.BOX_OFFICE_MOJO_BASE_URL + release_field.a["href"]
            self.incremental_id += 1
            movies.append(movie)
        return movies

    def scrape_opening_weekends_pages(self, url):
        self.url = url
        movies = []
        for offset in [0, 200, 400, 600, 800]:
            status_code, text_response = self.request_mojo_page(offset)
            if status_code != 200:
                self.logger.error("Status code {} in offset {}".format(status_code, offset))
                break

            start_time_parsing = time.time()
            movies.extend(self.parse_response_page_mojo(text_response))
            self.time_elapsed_parsing += (time.time() - start_time_parsing)

        self.total_pages_scraped += len(movies)

        return movies

    def get_times(self):
        return [self.time_elapsed_waiting_http_response, self.time_elapsed_parsing]

    def get_total_pages_scraped(self):
        return self.total_pages_scraped
