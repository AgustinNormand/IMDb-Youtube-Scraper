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

from third_source_scraper.YoutubeSearchScraper import YoutubeSearchScraper
from third_source_scraper.YoutubeVideoScraper import YoutubeVideoScraper

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="

class YoutubeScraper():

    def __init__(self):
        self.logger = logging.getLogger("ThirdSourceScraper")
        self.yss = YoutubeSearchScraper()
        self.yvs = YoutubeVideoScraper()

#    def remove_videos_before(self, release_start, ampliated_top_k):


    def scrape_movie(self, movie):
        try:
            top_k = self.yss.get_search_top(15, movie)
            #movie["trailers"] = top_k

            ampliated_top_k = self.yvs.ampliate(top_k)
            movie["trailers"] = ampliated_top_k



           # before_release_start_videos = self.remove_videos_before(movie["release_start"], ampliated_top_k)
            #pending secondary results


            #movie = self.get_trailer_video(movie)
            #trailer_video = self.get_trailer_video(movie)
            #trailer_video = self.get_trailer_video(movie)
            #movie = self.extract_info_from_trailer_video(trailer_video, movie)
            #statistics = self.get_statistics(trailer_video['id']["videoId"])
            #movie = self.extract_info_from_statistics(statistics, movie)

            return movie
        except Exception as e:
            self.logger.error("Exception {} in {}".format(e, movie))
            return None


