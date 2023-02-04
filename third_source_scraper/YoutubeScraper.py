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
from datetime import date
import re

from third_source_scraper.YoutubeSearchScraper import YoutubeSearchScraper
from third_source_scraper.YoutubeVideoScraper import YoutubeVideoScraper

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="


def diff_dates(date1, date2):
    return abs(date2 - date1).days


def anterior(date1, date2):
    return (date2 - date1).days >= 0


def translate(to_translate):
    tabin = u'áéíóú'
    tabout = u'aeiou'
    tabin = [ord(char) for char in tabin]
    translate_table = dict(zip(tabin, tabout))
    return to_translate.translate(translate_table)


def remove_non_alphanumeric(result):
    return re.sub(r'[^a-zA-Z0-9]', '', result)


def normalize(token):
    result = token.lower()
    result = translate(result)
    result = remove_non_alphanumeric(result)
    return result


class YoutubeScraper():

    def __init__(self):
        self.logger = logging.getLogger("ThirdSourceScraper")
        self.yss = YoutubeSearchScraper()
        self.yvs = YoutubeVideoScraper()

    def remove_results_by_date(self, release_start, query_results):
        anterior_query_results = []
        for query_result in query_results:
            title, channel, video_id, result_date_str, premiered, stream, subscribers, views, likes, verified = query_result

            if release_start == None or result_date_str == None or release_start == "" or result_date_str == "":
                is_anterior = True
            else:
                #print("{} {}".format(repr(release_start), result_date_str))
                movie_moth, movie_day, movie_year = release_start.split("/")
                result_moth, result_day, result_year = result_date_str.split("/")
                movie_date = date(int(movie_year), int(movie_moth), int(movie_day))
                result_date = date(int(result_year), int(result_moth), int(result_day))
                is_anterior = anterior(result_date, movie_date)

            #self.logger.debug("Movie Date {},  Result Date {}, Diff {} Result Date Is Anterior? {}".format(release_start, result_date_str, diff_dates(movie_date, result_date), is_anterior))

            if is_anterior:
                anterior_query_results.append(query_result)
        return anterior_query_results

    def get_official_trailers(self, movie, anterior_query_results):
        official_traiers = []
        for anterior_query_result in anterior_query_results:
            title, channel, video_id, result_date_str, premiered, stream, subscribers, views, likes = anterior_query_result
            title_tokens = title.split(" ")
            channel_tokens = channel.split(" ")

            normalized_title_tokens = []
            for title_token in title_tokens:
                normalized_title_token = normalize(title_token)
                if len(normalized_title_token) > 1:
                    normalized_title_tokens.append(normalized_title_token)

            normalized_channel_tokens = []
            for channel_token in channel_tokens:
                normalized_channel_tokens.append(normalize(channel_token))

            query_tokens = "official trailer".format(movie["movie_name"]).split()
            normalized_query_tokens = []
            for query_token in query_tokens:
                normalized_query_token = normalize(query_token)
                if len(normalized_query_token) > 1:
                    normalized_query_tokens.append(normalized_query_token)

            flag = True
            for normalized_query_token in normalized_query_tokens:
                if normalized_query_token not in normalized_title_tokens:
                    flag = False
                    break
            if flag:
                official_traiers.append(anterior_query_result)
        return official_traiers

    def remove_results_by_channel(self, distributor, ampliated_top_k):
        pass

    def scrape_movie(self, movie):
        try:
            top_k = self.yss.get_search_top(-1, movie)
            ampliated_top_k = self.yvs.ampliate(top_k)
            movie["query_results"] = ampliated_top_k

            movie["anterior_query_results"] = self.remove_results_by_date(movie["release_start"], ampliated_top_k)

            if movie["anterior_query_results"] == []:
                movie["no_prerelease"] = 1
                return movie

            movie["no_prerelease"] = 0

            #known_channels_results = self.remove_results_by_channel(movie["distributor"], ampliated_top_k)

            #if anterior_query_results == []:
            #    self.logger.debug("Anterior query results empty, using top k")
            #    anterior_query_results = ampliated_top_k

            #self.logger.debug("Anterior Query Results {}".format(anterior_query_results))


            #movie["official_trailers"] = self.get_official_trailers(movie, anterior_query_results)

            #movie["non_official_trailer"] = []
            #if movie["official_trailers"] == []:
            #    movie["non_official_trailer"] = anterior_query_results[0]

            # before_release_start_videos = self.remove_videos_before(movie["release_start"], ampliated_top_k)
            # pending secondary results

            # movie = self.get_trailer_video(movie)
            # trailer_video = self.get_trailer_video(movie)
            # trailer_video = self.get_trailer_video(movie)
            # movie = self.extract_info_from_trailer_video(trailer_video, movie)
            # statistics = self.get_statistics(trailer_video['id']["videoId"])
            # movie = self.extract_info_from_statistics(statistics, movie)

            return movie
        except Exception as e:
            self.logger.error("Exception {} in {}".format(e, movie))
            return None
