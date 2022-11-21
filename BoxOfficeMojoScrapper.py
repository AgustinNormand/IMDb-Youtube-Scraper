# -*- coding: utf-8 -*-

import requests
from fake_headers import Headers
from bs4 import BeautifulSoup
import time
import logging

BOX_OFFICE_MOJO_BASE_URL = "https://www.boxofficemojo.com"
BOX_OFFICE_MOJO_OPENINGS_URL = BOX_OFFICE_MOJO_BASE_URL+"/chart/top_opening_weekend/"
SECONDS_TO_SLEEP_BETWEEN_REQUESTS = 0.2
SAVE_HTMLS = False
LOGGING_LEVEL = logging.WARNING
LOG_FILENAME = './app.log'

#logging.basicConfig(level=LOGGING_LEVEL, filename=LOG_FILENAME, filemode='w', format='%(name)s - %(levelname)s - %(message)s')
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
  table = soup.find("div", {"id":"table"})
  release_fields = table.find_all("td", {"class": "mojo-field-type-release"})

  for release_field in release_fields:
    movie_name = release_field.text
    movies[incremental_id] = {}
    movies["movie_name"] = movie_name
    movies[incremental_id]["link"] = BOX_OFFICE_MOJO_BASE_URL+release_field.a["href"]
    incremental_id += 1

incremental_id = 0
movies = {}
for offset in [0, 200, 400, 600, 800]:
  status_code, text_response = request_mojo_page(offset)
  logging.debug("New request of page efectuated")
  logging.debug("Status Code {}".format(status_code))
  logging.debug("Requested with offset {} ".format(offset))
  logging.debug("Response len {}".format(len(text_response)))
  parse_response_page_mojo(text_response, movies, incremental_id)

  if SAVE_HTMLS:
    filename = "./initial_html_responses/offset_{}.html".format(offset)
    logging.debug("Saving as {}".format(filename))
    with open(filename, 'w') as f:
      f.write(text_response)

  if SECONDS_TO_SLEEP_BETWEEN_REQUESTS > 0:
    logging.debug("Sleeping {} second to avoid bans".format(SECONDS_TO_SLEEP_BETWEEN_REQUESTS))
    time.sleep(SECONDS_TO_SLEEP_BETWEEN_REQUESTS)
  break #Delete this to query all pages #TODO

logging.debug("Scraped {} movies from initial 5-pages".format(len(movies)))

def parse_movie_detail_page(html_response, movies, movie_id):
  soup = BeautifulSoup(html_response, "html.parser")
  #release_group = soup.find("div", {"id": "release-group-refiner"}).find("span", {"class": "a-dropdown-prompt"}) ##No está el boton de "Original Release" eso es JS.
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

  #print(titles)
  #print(gross_summary_table)

for movie_id in movies:
  print(movies[movie_id])
  r = do_request(movies[movie_id]["link"])
  if r.status_code != 200:
    logging.warning("Status code != 200 in {}, Movie name {}".format(movies[movie_id]["link"], movies[movie_id]["movie_name"]))
  parse_movie_detail_page(r.text, movies, movie_id)
  break

