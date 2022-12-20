def get_trailer_video_api(self, movie):
    trailer_name = "{} Official Trailer".format(movie["movie_name"])
    max_results = 10  # TODO
    request = self.youtube.search().list(
        part="snippet",
        maxResults=max_results,
        q=trailer_name,
        type="video",
        regionCode="AU"
    )

    response = request.execute()

    self.logger.debug("Youtube Request for max_results {}".format(trailer_name, max_results))
    self.logger.debug("kind {}".format(response["kind"]))
    self.logger.debug("etag {}".format(response["etag"]))
    self.logger.debug("nextPageToken {}".format(response["nextPageToken"]))
    self.logger.debug("regionCode {}".format(response["regionCode"]))
    self.logger.debug("pageInfo {}".format(response["pageInfo"]))
    self.logger.debug("Items Len {}".format(len(response["items"])))
    self.logger.debug("Items {}".format(response["items"]))

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