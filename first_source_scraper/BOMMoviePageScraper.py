import logging
from first_source_scraper import constants
from fake_headers import Headers
import requests
from bs4 import BeautifulSoup
import time

class BOMMoviePageScraper:
    def __init__(self):
        self.logger = logging.getLogger("FirstSourceScraper")
        self.time_elapsed_parsing = 0
        self.time_elapsed_waiting_http_response = 0
        self.total_movie_pages_scraped = 0
        self.last_request_timestamp = 0

    def sleep_if_needed(self):
        remaining_to_second_between_requests = 1 - (time.time() - self.last_request_timestamp)
        if remaining_to_second_between_requests > 0:
            time.sleep(remaining_to_second_between_requests)

    def request_movie_page(self, url):
        start_time_waiting_response = time.time()

        self.sleep_if_needed()
        self.last_request_timestamp = time.time()
        r = requests.get(headers=Headers().generate(), url=url)
        time_elapsed = time.time() - start_time_waiting_response
        self.time_elapsed_waiting_http_response += time_elapsed
        self.logger.debug("New request of movie page effectuated, "
                          "URL {}, "
                          "Status Code {}, "
                          "Response len {}, "
                          "Time elapsed waiting response {}".format(url, r.status_code, len(r.text), time_elapsed))
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

            if processed_gross_value == "-":
                #self.logger.debug("processed_gross_value == - in {}".format())
                processed_gross_value = None

            movie[final_gross_atribute_name] = int(processed_gross_value)

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
                movie["release_length"] = int(span.text.split("days")[0])

            if previous_span.replace("\n", "").strip() == "imdbpro":
                movie["url_imdb"] = span.find("a")["href"].replace("pro.imdb.com", "imdb.com")
            previous_span = span.text.lower()

    def summary_process(self, soup, movie):
        heading_summary = soup.find("div", {"class": "mojo-heading-summary"})
        summary = heading_summary.find("p", {"class": "a-size-medium"}).text
        movie["summary"] = summary

    def scrape_movie_details(self, movie):
        text_response = None
        try:
            status_code, text_response = self.request_movie_page(movie["url_bom"])
            if status_code != 200:
                self.logger.error("Status code {} in {}".format(status_code, movie))
                return None

            start_time_parsing = time.time()
            soup = BeautifulSoup(text_response, "html.parser")
            self.gross_table_process(soup, movie)
            self.other_table_process(soup, movie)
            self.summary_process(soup, movie)
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
