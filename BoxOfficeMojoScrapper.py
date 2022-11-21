# -*- coding: utf-8 -*-

import requests
from fake_headers import Headers
from bs4 import BeautifulSoup
import time
import logging

BOX_OFFICE_MOJO_BASE_URL = "https://www.boxofficemojo.com"
BOX_OFFICE_MOJO_OPENINGS_URL = BOX_OFFICE_MOJO_BASE_URL+"/chart/top_opening_weekend/"
SECONDS_TO_SLEEP_BETWEEN_REQUESTS = 0
SAVE_HTMLS = False
LOGGING_LEVEL = logging.DEBUG
LOG_FILENAME = './app.log'

#logging.basicConfig(level=LOGGING_LEVEL, filename=LOG_FILENAME, filemode='w', format='%(name)s - %(levelname)s - %(message)s')
logging.basicConfig(level=LOGGING_LEVEL)

def request_mojo(offset):
  url_with_offset = "{}?offset={}".format(BOX_OFFICE_MOJO_OPENINGS_URL, offset)
  r = requests.get(headers=Headers().generate(), url=url_with_offset)
  return [r.status_code, r.text]

def parse_response_page_mojo(html_response):
  soup = BeautifulSoup(html_response, "html.parser")
  table = soup.find("div", {"id":"table"})
  release_fields = table.find_all("td", {"class": "mojo-field-type-release"})

  movies = {}
  for release_field in release_fields:
    movies[release_field.text] = {}
    movies[release_field.text]["link"] = BOX_OFFICE_MOJO_BASE_URL+release_field.a["href"]
  print(len(movies.keys()))
  #trs_of_table = table.find_all("tr")
  #table_headers = trs_of_table[0]
  #trs_of_table = trs_of_table[1:]
  #print(trs_of_table.find_all("mojo-field-type-release"))

  #table_keys = []
  #for th in trs_of_table[0]:
  #  table_keys.append(th.span.text)
  #logging.debug("Table Keys {}".format(table_keys))

  #incremental_id = 1
  #for tr in trs_of_table[1:]:
  #  rank = tr.find("td")
  #  print()
    #for td in tr.find_all("td"):
      #print(td)
  #  break
    #if incremental_id == 5:
#      break
#    incremental_id += 1

for offset in [0, 200, 400, 600, 800]:
  status_code, text_response = request_mojo(offset)
  logging.debug("New request of page efectuated")
  logging.debug("Status Code {}".format(status_code))
  logging.debug("Requested with offset {} ".format(offset))
  logging.debug("Response len {}".format(len(text_response)))
  parse_response_page_mojo(text_response)

  if SAVE_HTMLS:
    filename = "./initial_html_responses/offset_{}.html".format(offset)
    logging.debug("Saving as {}".format(filename))
    with open(filename, 'w') as f:
      f.write(text_response)

  if SECONDS_TO_SLEEP_BETWEEN_REQUESTS > 0:
    logging.debug("Sleeping {} second to avoid bans".format(SECONDS_TO_SLEEP_BETWEEN_REQUESTS))
    time.sleep(SECONDS_TO_SLEEP_BETWEEN_REQUESTS)

  break