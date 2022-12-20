import logging
import time
from fp.fp import FreeProxy
from fake_headers import Headers
from requests.adapters import HTTPAdapter, Retry
import requests
from bs4 import BeautifulSoup
import json

import constants

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="

class YoutubeVideoScraper():
    def __init__(self):
        self.logger = logging.getLogger("ThirdSourceScraper")

        self.configure_session()

        r = self.session.get("https://www.youtube.com/?persist_gl=1&gl=AU")
        self.logger.debug("Set Location Status Code {}".format(r.status_code))

    def get_proxy(self):
        try:
            proxy = FreeProxy(country_id=['AU'], rand=True, timeout=0.5).get()
            self.proxies = {
                "http": proxy
            }
        except Exception as e:
            try:
                proxy = FreeProxy( rand=True, timeout=0.5).get()
                self.proxies = {
                    "http": proxy
                }
            except Exception as e:
                time.sleep(20)
                self.get_proxy()

    def configure_session(self):
        retry = Retry(total=5, connect=5, backoff_factor=0.1, status_forcelist=[413, 429, 503, 500])
        adapter = HTTPAdapter(max_retries=retry)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.headers = Headers().generate()
        self.headers["Accept-Language"] = "en-US"
        self.session.headers.update(self.headers)
        self.get_proxy()
        self.last_request_timestamp = time.time()

    def request(self, url):
        remaining_to_second_between_requests = 0.1 - (
                time.time() - self.last_request_timestamp)
        if remaining_to_second_between_requests > 0:
            time.sleep(remaining_to_second_between_requests)

        try:
            r = self.session.get(url=url, proxies=self.proxies)
            text = r.text
            status_code = r.status_code
            #self.logger.debug("New request to {}".format(url))
        except Exception as e:
            self.logger.error("Exception {} in {}".format(e, url))
            return None

        if status_code != 200:
            self.logger.error("Status code {} in {}".format(status_code, url))
            return None

        self.last_request_timestamp = time.time()
        return text

    def extract_json_data_from_script(self, text):
        soup = BeautifulSoup(text, "html.parser")
        for script in soup.find_all("script"):
            script_text = script.get_text()
            if "var ytInitialData" in script_text:
                youtube_json = script_text.replace("var ytInitialData = ", "").replace(";", "")
                return json.loads(youtube_json)
        return None

    def ampliate(self, top_k):
        ampliated_top_k = []
        for video in top_k:
            title, channel, video_id = video
            date = self.scrape_video(video_id)
            if date != None:
                ampliated_top_k.append([title, channel, video_id, date])
            #break
        return ampliated_top_k

    def parse_json_data(self, data):
        str_date = "UNDEFINED"
        try:
            str_date = data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0]["videoPrimaryInfoRenderer"]["dateText"]["simpleText"]
            str_date = str_date.lower()
            str_date = str_date.replace(",", "").replace("premiered", "")
            #str_date = str_date.replace(",", "").replace("streamed live on", "")
            #str_date = str_date.replace(",", "").replace("started streaming", "")
            month, day, year = str_date.split()
            month = constants.MONTHS[month.lower()]
            date = "{}/{}/{}".format(month, day, year)
            return date
        except Exception as e:
            self.logger.warning("Error {}. Str Date {}".format(e, str_date))
            return None


    def scrape_video(self, video_id):
        try:
            video_url = YOUTUBE_VIDEO_URL + video_id
            text = self.request(video_url)
            json_data = self.extract_json_data_from_script(text)
            json_data_parsed = self.parse_json_data(json_data)
            return json_data_parsed
        except Exception as e:
            self.logger.error("Error {} in {}".format(e, video_id))
            return None