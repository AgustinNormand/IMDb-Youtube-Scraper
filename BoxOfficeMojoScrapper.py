# -*- coding: utf-8 -*-

import requests
from fake_headers import Headers
from bs4 import BeautifulSoup
import time
import logging
import pandas as pd
#import numpy as np

start = time.time()

BOX_OFFICE_MOJO_BASE_URL = "https://www.boxofficemojo.com"
BOX_OFFICE_MOJO_OPENINGS_URL = BOX_OFFICE_MOJO_BASE_URL + "/chart/top_opening_weekend/"
SECONDS_TO_SLEEP_BETWEEN_REQUESTS = 0
SAVE_HTMLS = False
LOGGING_LEVEL = logging.DEBUG
LOG_FILENAME = './app.log'

months = {
    'jan': 1,
    'feb': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12
}

# logging.basicConfig(level=LOGGING_LEVEL, filename=LOG_FILENAME, filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=LOGGING_LEVEL)


def do_request(url):
    r = requests.get(headers=Headers().generate(), url=url)
    return r


def request_mojo_page(offset):
    url_with_offset = "{}?offset={}".format(BOX_OFFICE_MOJO_OPENINGS_URL, offset)
    r = do_request(url_with_offset)
    return [r.status_code, r.text]


def parse_response_page_mojo(html_response, movies, incremental_id):
    soup = BeautifulSoup(html_response, "html.parser")
    table = soup.find("div", {"id": "table"})
    release_fields = table.find_all("td", {"class": "mojo-field-type-release"})

    for release_field in release_fields:
        movie_name = release_field.text
        movies[incremental_id] = {}
        movies[incremental_id]["movie_name"] = movie_name
        movies[incremental_id]["link"] = BOX_OFFICE_MOJO_BASE_URL + release_field.a["href"]
        incremental_id += 1
    return incremental_id


incremental_id = 0
movies = {}
for offset in [0, 200, 400, 600, 800]:
    status_code, text_response = request_mojo_page(offset)
    logging.debug("New request of page efectuated")
    logging.debug("Status Code {}".format(status_code))
    logging.debug("Requested with offset {} ".format(offset))
    logging.debug("Response len {}".format(len(text_response)))
    incremental_id = parse_response_page_mojo(text_response, movies, incremental_id)

    if SECONDS_TO_SLEEP_BETWEEN_REQUESTS > 0:
        logging.debug("Sleeping {} second to avoid bans".format(SECONDS_TO_SLEEP_BETWEEN_REQUESTS))
        time.sleep(SECONDS_TO_SLEEP_BETWEEN_REQUESTS)

logging.debug("Scraped {} movies from initial 5-pages".format(len(movies)))

def gross_table_process(soup, movies, movie_id):
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

        movies[movie_id][final_gross_atribute_name] = processed_gross_value


def other_table_process(soup, movies, movie_id):
    other_table = soup.find("div", {"class": "mojo-summary-values"})

    spans = other_table.find_all("span")
    previous_span = spans[0].text.lower()
    for span in spans[1:]:
        if previous_span == "distributor":
            movies[movie_id][previous_span] = span.next
        if previous_span == "opening":
            movies[movie_id]["opening_box"] = span.next.text.replace("$", "").replace(",", "")
            movies[movie_id]["opening_theater"] = span.next.nextSibling.nextSibling.text.strip() \
                                                                        .replace("theaters", "") \
                                                                        .replace(",", "") \
                                                                        .replace("\n", "") \
                                                                        .replace(" ", "")
        if previous_span == "budget":
            movies[movie_id]["budget"] = span.text.replace("$", "").replace(",", "")
        if previous_span == "release date":
            a_tags = span.find_all("a")
            if len(a_tags) == 2: #Has Release Start and Release End
              release_start, release_end = a_tags
              release_start = release_start.text.lower().replace(",", "").split()
              release_end = release_end.text.lower().replace(",", "").split()
              release_start[0] = str(months[release_start[0]])
              release_end[0] = str(months[release_end[0]])
              movies[movie_id]["release_start"] = "/".join(release_start)
              movies[movie_id]["release_end"] = "/".join(release_end)
            else:
              release_start = a_tags[0]
              release_start = release_start.text.lower().replace(",", "").split()
              release_start[0] = str(months[release_start[0]])
              movies[movie_id]["release_start"] = "/".join(release_start)
              movies[movie_id]["release_end"] = None

        if previous_span == "mpaa":
          movies[movie_id]["mpaa"] = span.text
        if previous_span == "running time":
          hours = int(span.text.split("hr")[0])
          mins = 0
          if "min" in span.text.split("hr")[1]:
            mins = int(span.text.split("hr")[1].split("min")[0])
          movies[movie_id]["run_time"] = hours*60+mins
        if previous_span == "genres":
          movies[movie_id]["genres"] = span.text.replace(" ", "").split("\n\n")
        if previous_span == "in release":
          movies[movie_id]["release_length"] = span.text.split("days")[0]
        previous_span = span.text.lower()

def summary_process(soup, movies, movie_id):
  heading_summary = soup.find("div", {"class": "mojo-heading-summary"})
  summary = heading_summary.find("p", {"class": "a-size-medium"}).text
  movies[movie_id]["summary"] = summary

def parse_movie_detail_page(html_response, movies, movie_id):
    soup = BeautifulSoup(html_response, "html.parser")
    gross_table_process(soup, movies, movie_id)
    other_table_process(soup, movies, movie_id)
    summary_process(soup, movies, movie_id)

for movie_id in movies:
    logging.debug("Processing movie_id {}, movie_name {}".format(movie_id, movies[movie_id]))
    r = do_request(movies[movie_id]["link"])
    if r.status_code != 200:
        logging.warning(
            "Status code != 200 in {}, Movie name {}".format(movies[movie_id]["link"], movies[movie_id]["movie_name"]))
    parse_movie_detail_page(r.text, movies, movie_id)
    logging.debug("Movie Processed {}".format(movies[movie_id]))


end = time.time()
print("Elapsed execution time {}".format(end - start))

data = pd.DataFrame.from_dict(movies, orient='index')
data.insert(0, "uniqueID", list(movies.keys()))
data.to_csv("results.csv", index=False)
