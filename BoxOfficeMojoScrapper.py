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

for movie_id in movies:
  r = do_request(movies[movie_id]["link"])
  if r.status_code != 200:
    logging.warning("Status code != 200 in {}, Movie name {}".format(movies[movie_id]["link"], movies[movie_id]["movie_name"]))
  print(r.text)
  break

