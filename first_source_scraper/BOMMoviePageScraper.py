import logging
from fake_headers import Headers
import requests
from bs4 import BeautifulSoup
import time
from requests.adapters import HTTPAdapter, Retry

import constants


class BOMMoviePageScraper:
    def __init__(self):
        self.logger = logging.getLogger("FirstSourceScraper")
        self.time_elapsed_parsing = 0
        self.time_elapsed_waiting_http_response = 0
        self.total_movie_pages_scraped = 0
        self.last_request_timestamp = time.time()

        self.session = requests.Session()
        retry = Retry(connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update(Headers().generate())
        #print(self.session.get('https://httpbin.org/headers').text)

    def sleep_if_needed(self):
        remaining_to_second_between_requests = constants.SECONDS_TO_SLEEP_BETWEEN_REQUESTS - (time.time() - self.last_request_timestamp)
        if remaining_to_second_between_requests > 0:
            time.sleep(remaining_to_second_between_requests)

    def request_movie_page(self, url):
        start_time_waiting_response = time.time()

        self.sleep_if_needed()
        time_between_requests = time.time() - self.last_request_timestamp
        r = self.session.get(url=url)
        self.last_request_timestamp = time.time()
        time_elapsed = time.time() - start_time_waiting_response
        self.time_elapsed_waiting_http_response += time_elapsed
        self.logger.debug("New request of movie page effectuated, "
                          "URL {}, "
                          "Status Code {}, "
                          "Response len {}, "
                          "Time elapsed waiting response {}, "
                          "Time between requests {}".format(url, r.status_code, len(r.text), time_elapsed, time_between_requests))
        return [r.status_code, r.text]

    def gross_table_process(self, soup, movie):
        gross_summary_table = soup.find("div", {"class": "mojo-performance-summary-table"})
        gross_titles = gross_summary_table.find_all("span", {"class": "a-size-small"})
        gross_values = gross_summary_table.find_all("span", {"class": "a-size-medium"})
        for gross_value, gross_title in zip(gross_values, gross_titles):
            processed_gross_title = gross_title.text.strip().split(" ")[0].lower()
            processed_gross_value = gross_value.text.strip().replace("$", "").replace(",", "")
            final_gross_atribute_name = None
            if processed_gross_title == "domestic":
                final_gross_atribute_name = "gross_dom"
            elif processed_gross_title == "international":
                final_gross_atribute_name = "gross_int"
            elif processed_gross_title == "worldwide":
                final_gross_atribute_name = "gross_worldwide"

            if final_gross_atribute_name == None:
                logging.error("Final Gross Atribute Name not assigned, summary table missing?")

            if processed_gross_value == "–":
                movie[final_gross_atribute_name] = None
            else:
                movie[final_gross_atribute_name] = int(processed_gross_value)

        return movie

    def other_table_process(self, soup, movie):
        other_table = soup.find("div", {"class": "mojo-summary-values"})

        spans = other_table.find_all("span")
        previous_span = spans[0].text.lower()
        for span in spans[1:]:
            if previous_span == "distributor":
                movie[previous_span] = span.next
            if previous_span == "opening":
                movie["opening_box"] = int(span.next.text.replace("$", "").replace(",", ""))
                movie["opening_theater"] = int(span.next.nextSibling.nextSibling.text.strip() \
                    .replace("theaters", "") \
                    .replace(",", "") \
                    .replace("\n", "") \
                    .replace(" ", ""))
            if previous_span == "budget":
                movie["budget"] = int(span.text.replace("$", "").replace(",", ""))
            if previous_span == "release date":
                a_tags = span.find_all("a")
                if len(a_tags) == 2:  # Has Release Start and Release End
                    release_start, release_end = a_tags
                    release_start = release_start.text.lower().replace(",", "").split()
                    release_end = release_end.text.lower().replace(",", "").split()
                    release_start[0] = str(constants.MONTHS[release_start[0]])
                    release_end[0] = str(constants.MONTHS[release_end[0]])
                    movie["release_start"] = "/".join(release_start)
                    movie["release_end"] = "/".join(release_end)
                else:
                    release_start = a_tags[0]
                    release_start = release_start.text.lower().replace(",", "").split()
                    release_start[0] = str(constants.MONTHS[release_start[0]])
                    movie["release_start"] = "/".join(release_start)
                    movie["release_end"] = None

            if previous_span == "mpaa":
                movie["mpaa"] = span.text
            if previous_span == "running time":
                hours = int(span.text.split("hr")[0])
                mins = 0
                if "min" in span.text.split("hr")[1]:
                    mins = int(span.text.split("hr")[1].split("min")[0])
                movie["run_time"] = hours * 60 + mins
            if previous_span == "genres":
                movie["genres"] = span.text.replace(" ", "").split("\n\n")
            if previous_span == "in release":
                movie["release_length"] = int(span.text.split("days")[0].replace(",", ""))
            if previous_span.replace("\n", "").strip() == "imdbpro":
                movie["url_imdb"] = span.find("a")["href"].replace("pro.imdb.com", "imdb.com")
            previous_span = span.text.lower()

        return movie

    def summary_process(self, soup, movie):
        try:
            heading_summary = soup.find("div", {"class": "mojo-heading-summary"})
            summary = heading_summary.find("p", {"class": "a-size-medium"}).text
            movie["summary"] = summary
        except Exception as e:
            movie["summary"] = None
        return movie

    def get_page_with_right_release(self, url):
        status_code, text_response = self.request_movie_page(url)
        if status_code != 200:
            self.logger.error("Status code {} in {}".format(status_code, url))
            return None
        soup = BeautifulSoup(text_response, "html.parser")

        all_releases_selected = False
        original_release_path = None
        original_release_selected = False
        release_group_select = soup.find("select", {"name":"releasegroup-picker-navSelector"})
        for option in release_group_select.find_all("option"):
            label = option.get_text()
            selected = option.has_attr("selected")
            if label == "All Releases" and selected:
                all_releases_selected = True
            if label == "Original Release":
                if selected:
                    original_release_selected = True
                else:
                    original_release_path = constants.BOX_OFFICE_MOJO_BASE_URL + option["value"]

        if not original_release_selected:
            self.logger.debug("Original release is not selected, should request {}".format(original_release_path))
            return self.get_page_with_right_release(original_release_path)
        else:
            self.logger.debug("Original release is selected, need to see the other one")

        if not all_releases_selected:
            self.logger.warning("All Releases was always selected but not in this movie {}".format(url))

        domestic_release_path = None
        domestic_release_selected = False
        release_select = soup.find("select", {"name": "release-picker-navSelector"})
        for option in release_select.find_all("option"):
            label = option.get_text()
            selected = option.has_attr("selected")
            if label == "Domestic":
                if selected:
                    domestic_release_selected = True
                else:
                    domestic_release_path = constants.BOX_OFFICE_MOJO_BASE_URL + option["value"]

        if not domestic_release_selected:
            self.logger.debug("Domestic release is not selected, should request {}".format(domestic_release_path))
            return self.get_page_with_right_release(domestic_release_path)
        else:
            self.logger.debug("Domestic release is selected, this is the right page")
        return text_response

    def scrape_movie_details(self, movie):
        text_response = None
        try:
            text_response = self.get_page_with_right_release(movie["url_bom"])

            start_time_parsing = time.time()
            soup = BeautifulSoup(text_response, "html.parser")
            movie = self.gross_table_process(soup, movie)
            movie = self.other_table_process(soup, movie)
            movie = self.summary_process(soup, movie)
            self.time_elapsed_parsing += (time.time() - start_time_parsing)
            self.total_movie_pages_scraped += 1

            self.log_scrape()
        except Exception as e:
            self.logger.error("Exception {} scraping movie details, Writing text_response.html if is defined".format(e))
            if text_response != None:
                with open("./first_source_scraper/text_response.html", "w") as f:
                    f.write(text_response)
            return None

        return movie

    def log_scrape(self):
        pass

    def get_times(self):
        return [self.time_elapsed_waiting_http_response, self.time_elapsed_parsing]

    def get_total_movie_pages_scraped(self):
        return self.total_movie_pages_scraped
