from googleapiclient.discovery import build
from dotenv import dotenv_values
import logging
import sys

YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v="

class ThirdSourceScraper:
    def __init__(self):
        self.logger = logging.getLogger("__main__")
        config = dotenv_values(".env")
        self.youtube = build('youtube', 'v3', developerKey = config.get("API_KEY"))

    def start(self, movies):
        for uniqueID in movies:
            self.scrape(movies[uniqueID])

    def scrape(self, movie):
        trailer_name = "{} Official Trailer".format(movie["movie_name"])
        max_results = 1
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

        for item in response["items"]:
            #print(item)
            if item["id"]["kind"] == 'youtube#video':
                video_id = item['id']["videoId"]
                print("Video ID {}".format(video_id))
                video_url = YOUTUBE_VIDEO_URL+video_id
                print("Video URL {}".format(video_url))
                print("Need comments before {}".format(movie["release_start"]))

                #videos().list()
                #request = self.youtube.videos().list(
                #    part="snippet",
                #    id=video_id
                #)
                #response = request.execute()
                #print("Response {}".format(response))

                request = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=100 #This is the max
                )
                response = request.execute()
                print("commentThreads Response")
                print("{}".format(response))
            else:
                print("Something that is not a video. {}".format(item["id"]["kind"]))

# https://www.youtube.com/watch?v=TcMBFSGVi1c