import logging
import time
from fp.fp import FreeProxy
from fake_headers import Headers
from requests.adapters import HTTPAdapter, Retry
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
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
            attributes = self.scrape_video(video_id)
            video.extend(attributes)
            ampliated_top_k.append(video)

        return ampliated_top_k

    def get_date(self, data, video_id):
        initial_str_date = "UNDEFINED"
        str_date = "UNDEFINED"

        try:
            initial_str_date = data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0][
                "videoPrimaryInfoRenderer"]["dateText"]["simpleText"]

            str_date = initial_str_date.lower()

            premiered = ("premiered" in str_date) or ("premieres" in str_date)
            stream = ("streamed" in str_date) or ("streaming" in str_date)

            if "hours ago" in str_date or "hour ago" in str_date or "minutes ago" in str_date or "minute ago" in str_date:
                date = "{}/{}/{}".format(12, 20, 2022)
            else:
                str_date = str_date.replace(",", "")
                str_date = str_date.replace("premieres", "")
                str_date = str_date.replace("premiered", "")
                str_date = str_date.replace("streamed live on", "")
                str_date = str_date.replace("started streaming", "")
                month, day, year = str_date.split()
                month = constants.MONTHS[month.lower()]
                date = "{}/{}/{}".format(month, day, year)
            return [date, premiered, stream]

        except Exception as e:
            dt = datetime.now()
            filename = "{}.json".format(dt)
            self.logger.warning("Error {}, Video Id {}, Initial Str Date {}, Str Date {}, Saving as {}".format(e, video_id, initial_str_date, str_date, filename))
            with open("./error_files/"+filename, "w") as f:
                f.write(json.dumps(data))

            return [None, False, False]

    def get_subscribers(self, data, video_id):
        initial_subscribers = "UNDEFINED"

        try:
            initial_subscribers = data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1]["videoSecondaryInfoRenderer"]["owner"]["videoOwnerRenderer"]["subscriberCountText"]["simpleText"]
            subscribers = initial_subscribers.replace("subscribers", "")
            subscribers = subscribers.replace(" ", "")
            subscribers.strip()
            return subscribers

        except Exception as e:
            dt = datetime.now()
            filename = "{}.json".format(dt)
            self.logger.warning("Error {}, Video Id {}, Initial Subscribers {}, Saving as {}".format(e, video_id, initial_subscribers, filename))
            with open("./error_files/"+filename, "w") as f:
                f.write(json.dumps(data))
            return None

    def get_views(self, data, video_id):
        initial_views = "UNDEFINED"

        try:
            initial_views = data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0][
                "videoPrimaryInfoRenderer"]["viewCount"]["videoViewCountRenderer"]["viewCount"]["simpleText"]
            views = initial_views.replace("views", "")
            views = views.replace(" ", "")
            return views

        except Exception as e:
            dt = datetime.now()
            filename = "{}.json".format(dt)
            self.logger.warning("Error {}, Video Id {}, Initial Views {}, Saving as {}".format(e, video_id, initial_views, filename))
            with open("./error_files/"+filename, "w") as f:
                f.write(json.dumps(data))
            return None

    def get_initial_likes(self, data):
        try:
            return data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0][
                "videoPrimaryInfoRenderer"]["videoActions"]["menuRenderer"]["topLevelButtons"][0][
                "segmentedLikeDislikeButtonRenderer"]["likeButton"]["toggleButtonRenderer"]["defaultText"][
                "accessibility"]["accessibilityData"]["label"]
        except Exception as e:
            pass

        try:
            return data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][0][
                "videoPrimaryInfoRenderer"]["videoActions"]["menuRenderer"]["topLevelButtons"][0]["toggleButtonRenderer"][
                "defaultText"][
                "accessibility"]["accessibilityData"]["label"]
        except Exception as e:
            pass

        raise Exception("initial likes error")

    def try_get_verified(self, data):
        try:
            return data["contents"]["twoColumnWatchNextResults"]["results"]["results"]["contents"][1]["videoSecondaryInfoRenderer"]["owner"]["videoOwnerRenderer"]["badges"][0]["metadataBadgeRenderer"]["accessibilityData"]["label"]
        except Exception as e:
            pass
        raise Exception("verified error")



    def get_likes(self, data, video_id):
        initial_likes = "UNDEFINED"

        try:

            initial_likes = self.get_initial_likes(data)

            likes = initial_likes.replace("likes", "")
            likes = likes.replace(" ", "")
            return likes

        except Exception as e:
            dt = datetime.now()
            filename = "{}.json".format(dt)
            self.logger.warning("Error {}, Video Id {}, Initial Likes {}, Saving as {}".format(e, video_id, initial_likes, filename))
            with open("./error_files/"+filename, "w") as f:
                f.write(json.dumps(data))
            return None

    def get_verified(self, data, video_id):
        verified = False

        try:
            verified = self.try_get_verified(data)
            #verified = verified.lower()
            if verified == "verified":
                return "verified"
            else:
                return "not verified"

        except Exception as e:
            dt = datetime.now()
            filename = "{}.json".format(dt)
            self.logger.warning("Error {}, Video Id {}, Verified {}, Saving as {}".format(e, video_id, verified, filename))
            with open("./error_files/"+filename, "w") as f:
                f.write(json.dumps(data))
            return None


    def parse_json_data(self, data, video_id):
        date, premiered, stream = self.get_date(data, video_id)
        subscribers = self.get_subscribers(data, video_id)
        views = self.get_views(data, video_id)
        likes = self.get_likes(data, video_id)
        verified = self.get_verified(data, video_id)
        return [date, premiered, stream, subscribers, views, likes, verified]

    def scrape_video(self, video_id):
        try:
            video_url = YOUTUBE_VIDEO_URL + video_id
            text = self.request(video_url)
            json_data = self.extract_json_data_from_script(text)
            attributes = self.parse_json_data(json_data, video_id)
            return attributes
        except Exception as e:
            self.logger.error("Error {} in {}".format(e, video_id))
            return None