import logging
import constants
from fake_headers import Headers
import requests
from bs4 import BeautifulSoup


def request_movie_page(url):
    r = requests.get(headers=Headers().generate(), url=url)
    return [r.status_code, r.text]

class BOMMoviePageScraper:
    def __init__(self):
        self.logger = logging.getLogger("__main__")
        self.time_elapsed_parsing = 0  # TODO
        self.time_elapsed_waiting_http_response = 0  # TODO
        self.total_time_elapsed = 0  # TODO
        # Maybe this is different from time_elapsed_parsing+time_elapsed_waiting_http_response
        # I can know "other times" elapsed

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

            movie[final_gross_atribute_name] = processed_gross_value

    def other_table_process(self, soup, movie):
        other_table = soup.find("div", {"class": "mojo-summary-values"})

        spans = other_table.find_all("span")
        previous_span = spans[0].text.lower()
        for span in spans[1:]:
            if previous_span == "distributor":
                movie[previous_span] = span.next
            if previous_span == "opening":
                movie["opening_box"] = span.next.text.replace("$", "").replace(",", "")
                movie["opening_theater"] = span.next.nextSibling.nextSibling.text.strip() \
                    .replace("theaters", "") \
                    .replace(",", "") \
                    .replace("\n", "") \
                    .replace(" ", "")
            if previous_span == "budget":
                movie["budget"] = span.text.replace("$", "").replace(",", "")
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
                movie["release_length"] = span.text.split("days")[0]
            previous_span = span.text.lower()

    def summary_process(self, soup, movie):
        heading_summary = soup.find("div", {"class": "mojo-heading-summary"})
        summary = heading_summary.find("p", {"class": "a-size-medium"}).text
        movie["summary"] = summary

    def scrape_movie_details(self, movie):
        status_code, text_response = request_movie_page(movie["url_bom"])
        if status_code != 200:
            self.logger.error("Status code {} in {}".format(status_code, movie))
            return None
        soup = BeautifulSoup(text_response, "html.parser")
        self.gross_table_process(soup, movie)
        self.other_table_process(soup, movie)
        self.summary_process(soup, movie)
        return movie
