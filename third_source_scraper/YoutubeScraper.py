from googleapiclient.discovery import build
from dotenv import dotenv_values
import logging

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="

class YoutubeScraper():

    def __init__(self):
        self.logger = logging.getLogger("__main__")
        config = dotenv_values(".env")
        self.youtube = build('youtube', 'v3', developerKey=config.get("API_KEY"))

    def get_trailer_video(self, movie):
        trailer_name = "{} Official Trailer".format(movie["movie_name"])
        max_results = 1 # TODO
        request = self.youtube.search().list(
            part="snippet",
            maxResults=max_results,
            q=trailer_name,
            type="video",
            regionCode="AU"
        )

        response = request.execute()

        print("Youtube Request for max_results {}".format(trailer_name, max_results))
        print("kind {}".format(response["kind"]))
        print("etag {}".format(response["etag"]))
        print("nextPageToken {}".format(response["nextPageToken"]))
        print("regionCode {}".format(response["regionCode"]))
        print("pageInfo {}".format(response["pageInfo"]))
        print("Items Len {}".format(len(response["items"])))

        return response["items"][0]

    def extract_info_from_trailer_video(self, trailer_video, movie):
        video_id = trailer_video['id']["videoId"]
        video_url = YOUTUBE_VIDEO_URL + video_id
        movie["url_youtube"] = video_url
        movie["trailer_release"] = trailer_video["snippet"]["publishedAt"]
        return movie

    def get_statistics(self, video_id):
        request = self.youtube.videos().list(
            part="statistics",
            id=video_id
        )
        response = request.execute()
        return response["items"][0]

    def extract_info_from_statistics(self, statistics, movie):
        movie["trailer_view"] = statistics["statistics"]["viewCount"]
        movie["trailer_like"] = statistics["statistics"]["likeCount"]
        movie["trailer_favorite"] = statistics["statistics"]["favoriteCount"]
        movie["trailer_comment"] = statistics["statistics"]["commentCount"]

        return movie



    def scrape_movie(self, movie):
        trailer_video = self.get_trailer_video(movie)
        movie = self.extract_info_from_trailer_video(trailer_video, movie)

        statistics = self.get_statistics(trailer_video['id']["videoId"])
        movie = self.extract_info_from_statistics(statistics, movie)

        return movie
