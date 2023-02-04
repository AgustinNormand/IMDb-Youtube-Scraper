from googleapiclient.discovery import build
from dotenv import dotenv_values
import logging
import time
from fp.fp import FreeProxy
from fake_headers import Headers
from requests.adapters import HTTPAdapter, Retry
import requests
import urllib.parse
from bs4 import BeautifulSoup
import json

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="

save_files = False

class YoutubeSearchScraper():

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
        except Exception as e:
            self.logger.error("Exception {} in {}".format(e, url))
            return None

        if status_code != 200:
            self.logger.error("Status code {} in {}".format(status_code, url))
            return None

        self.last_request_timestamp = time.time()
        return text

    def get_search_top(self, top_k, movie):
        if top_k == -1:
            return self.get_search_results(movie)
        else:
            return self.get_search_results(movie)[:top_k]

    def extract_json_data_from_script(self, text):
        soup = BeautifulSoup(text, "html.parser")
        for script in soup.find_all("script"):
            script_text = script.get_text()
            if "var ytInitialData" in script_text:
                youtube_json = script_text.replace("var ytInitialData = ", "").replace(";", "")
                return json.loads(youtube_json)
        return None

    def get_primary_results(self, contents):
        primary_results = None
        for content in contents:
            try:
                if len(content["itemSectionRenderer"]["contents"]) > 15:
                    primary_results = content["itemSectionRenderer"]["contents"]
                    break
            except Exception as e:
                pass
        return primary_results

    def get_title_and_channel_From_video_renderer(self, result):
        title = result["videoRenderer"]["title"]["runs"][0]["text"]
        channel = result["videoRenderer"]["longBylineText"]["runs"][0]["text"]
        return [title, channel]

    def parse_json_data_primay(self, data):
        contents = data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"][
            "contents"]
        self.logger.debug("Len of contents {}".format(len(contents)))

        primary_results = self.get_primary_results(contents)

        if primary_results == None:
            self.logger.error("Search without primary results ?")
            results = []
        else:
            self.logger.debug("Len of primary results {}".format(len(primary_results)))
            results = []
            for result in primary_results:
                try:
                    title = result["videoRenderer"]["title"]["runs"][0]["text"]
                    channel = result["videoRenderer"]["longBylineText"]["runs"][0]["text"]
                    video_id = result["videoRenderer"]["videoId"]
                    results.append([title, channel, video_id])
                except Exception as e:
                    #self.logger.warning("Exception {} extracting title and channel".format(e))
                    pass
        return results

    """
    def parse_json_data_secondary(self, data):
        results = []
        try:
            secondary_results = \
            data["contents"]["twoColumnSearchResultsRenderer"]["secondaryContents"]["secondarySearchContainerRenderer"][
                "contents"]
            self.logger.debug("Len of secondary results {}".format(len(secondary_results)))
            for content in secondary_results:
                self.logger.debug("Secondary Results Keys {}".format(content.keys()))
                results = []
                for item in \
                content["universalWatchCardRenderer"]["sections"][0]["watchCardSectionSequenceRenderer"]["lists"][0][
                    "verticalWatchCardListRenderer"]['items']:
                    title = item["watchCardCompactVideoRenderer"]["title"]["simpleText"]
                    url = \
                    item["watchCardCompactVideoRenderer"]["navigationEndpoint"]["commandMetadata"]["webCommandMetadata"][
                        "url"]
                    channel = item["watchCardCompactVideoRenderer"]["byline"]["runs"][0]["text"]
                    results.append([title, channel])
        except Exception as e:
            self.logger.warning("Exception {} parsing data secondary".format(e))
            pass
        return results
    """

    def get_search_results(self, movie):
        trailer_name = "{} Official Trailer".format(movie["movie_name"])
        query_url = "https://www.youtube.com/results?search_query={}".format(
            urllib.parse.quote_plus(trailer_name.lower()))

        movie["query_url"] = query_url

        youtube_results_html = self.request(query_url)
        if save_files:
            with open("/home/agustin/PycharmProjects/IMDb-Youtube-Scraper/third_source_scraper/htmls/{}.html".format(
                    movie["movie_name"].replace("/", "_")), "w") as f:
                f.write(youtube_results_html)

        json_data = self.extract_json_data_from_script(youtube_results_html)
        if json_data == None:
            return None

        if save_files:
            with open("/home/agustin/PycharmProjects/IMDb-Youtube-Scraper/third_source_scraper/jsons/{}.json".format(
                    movie["movie_name"].replace("/", "_")), "w") as f:
                f.write(json.dumps(json_data))

        #movie["trailer_primary_results"] = self.parse_json_data_primay(json_data)
        #movie["trailer_secondary_results"] = self.parse_json_data_secondary(json_data)

        return self.parse_json_data_primay(json_data)