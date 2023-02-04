import ast
import csv
from threading import Thread
from datetime import datetime
from googleapiclient.discovery import build
import time
import queue
import logging

logging.basicConfig(filename='application.log', level=logging.INFO)

selected_trailers = []
with open('selected_trailers.csv') as f:
    reader = csv.DictReader(f)
    lst = list(reader)
    for item in lst:
        selected_trailers.append(item)
logging.info("Selected Trailers Len {}".format(len(selected_trailers)))

movies = []
with open('Output.csv') as f:
    reader = csv.DictReader(f)
    lst = list(reader)
    for item in lst:
        item["query_results"] = ast.literal_eval(item["query_results"])
        movies.append(item)
logging.info("Movies Len {}".format(len(movies)))

api_key0 = 'AIzaSyABtrfufYJyDa7VAS-bTEocGw6X-ASn6vI'  # normandagustin@gmail.com
api_key1 = 'AIzaSyAVwjhUGNdSmm479vjR4VOkfyR13DisbHo'  # agustinnormand@gmail.com
api_key2 = "AIzaSyDNN4TCrO3DbbR6Wy2TQOl_BZfwxW0aRR4"  # nose
api_key3 = "AIzaSyBwINC6HCOeZWT3QntGDOGJ_u78qib7J74"  # agustinabr232022@gmail.com
api_key4 = "AIzaSyCrWmLwtVonR2UTwS1VA_9TsIvEaVnEVrA"  # masivasrerun@gmail.cocm
api_key5 = "AIzaSyBYu73DBFR3oVQvwndInJjpPfkZPyld-_k"  # agustinnov12022@gmail.com
api_key6 = "AIzaSyC-aGIpGaKoIuVSymD3JK3X7e_QuWQuTBU"  # agustin6nov@gmail.com
api_key7 = "AIzaSyBlT7sw2FcIpmMlHqf6VBVm97MhzH3rrn0"  # agustinago62022@gmail.com
api_key8 = "AIzaSyCtLnGq8JX3mPWnJttPAn5WpwTjGyVewyU"  # agustindic192022@gmail.com
api_key9 = "AIzaSyAj7JlNuFJtj3r2Lxi8rH_47FvGz5KXCX8"  # agustinsep102022@gmail.com
api_key10 = "AIzaSyC03JdpBj1gJwDdPH-ybn4g0MtkO5M8Rtw"  # an2021dic15@gmail.com
api_key11 = "AIzaSyAXGKVsLpRsDJitNvZCFfowsV0oZ8sRO88"  # an2022ene9@gmail.com
# api_key12 = "AIzaSyCH8-nWnRE5wRWcFfJeQ7IiSEfjXi7hNKc"  # an2022ene10@gmail.com

api_keys = [api_key0, api_key1, api_key2, api_key3, api_key4, api_key5, api_key6, api_key7, api_key8, api_key9, api_key10, api_key11]

class CommentsScraperWorker(Thread):
    def __init__(self, worker_number, tasks_queue, api_key, movies):
        Thread.__init__(self)
        self.worker_number = worker_number
        self.tasks_queue = tasks_queue
        self.api_key = api_key
        self.movies = movies
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def get_posterior_counts(self, comments, movie):
        movie_date_object = datetime.strptime(movie["release_start"], "%m/%d/%Y")

        posterior_comments_count = 0
        posterior_reply_count = 0

        for comment in comments:
            comment_updatedAt = comment["snippet"]["topLevelComment"]["snippet"]["updatedAt"].replace("T", " ").replace(
                "Z",
                "")
            comment_date_object = datetime.strptime(comment_updatedAt, "%Y-%m-%d %H:%M:%S")

            comment_movie_days_diff = (comment_date_object - movie_date_object).days
            if comment_movie_days_diff >= 0:
                posterior_comments_count += 1

            for reply in comment["replies"]:
                reply_updatedAt = reply["snippet"]["updatedAt"].replace("T", " ").replace("Z", "")
                reply_date_object = datetime.strptime(reply_updatedAt, "%Y-%m-%d %H:%M:%S")
                reply_movie_days_diff = (reply_date_object - movie_date_object).days
                if reply_movie_days_diff >= 0:
                    posterior_reply_count += 1

        return posterior_comments_count, posterior_reply_count

    def get_comment_list(self, youtube, video_id, next_view_token):
        finish_succesfully = False
        retry_count = 0

        comment_list = {}
        comment_list["items"] = []

        while not finish_succesfully:
            try:
                if next_view_token == "":
                    comment_list = youtube.commentThreads().list(part='snippet',
                                                                 maxResults=100,
                                                                 videoId=video_id,
                                                                 order='time').execute()
                else:
                    comment_list = youtube.commentThreads().list(part='snippet',
                                                                 maxResults=100,
                                                                 videoId=video_id,
                                                                 order='time',
                                                                 pageToken=next_view_token).execute()

                finish_succesfully = True
            except Exception as e:
                if "commentsDisabled" in str(e):
                    logging.info("Worker Number {}, Comments disabled".format(self.worker_number))
                    break
                elif "quota" in str(e):
                    logging.info("Worker Number {}, Quota reached, sleeping 1 hour".format(self.worker_number))
                    time.sleep(3600)
                else:
                    logging.info("Worker Number {}, Error not contemplated {}".format(self.worker_number, str(e)))

                finish_succesfully = False
        return comment_list

    def get_replies_list(self, youtube, comment_id, next_view_token):
        finish_succesfully = False
        replies_list = []
        while not finish_succesfully:
            try:
                if next_view_token == "":
                    replies_list = youtube.comments().list(part='snippet',
                                                           maxResults=100,
                                                           parentId=comment_id).execute()
                else:
                    replies_list = youtube.comments().list(part='snippet',
                                                           maxResults=100,
                                                           parentId=comment_id,
                                                           pageToken=next_view_token).execute()

                finish_succesfully = True
            except Exception as e:
                if "quota" in str(e):
                    logging.info("Worker Number {}, Quota reached, sleeping 1 hour".format(self.worker_number))
                    time.sleep(3600)
                else:
                    logging.info("Worker Number {}, Error not contemplated {}".format(self.worker_number, str(e)))
                finish_succesfully = False

        return replies_list

    def get_delete_comments_count(self, youtube, video_id, movie):
        total_posterior_comments_count = 0
        total_posterior_reply_count = 0

        iterations_in_zero_count = 0

        next_view_token = ""
        while True:
            iteration_comments_count = 0
            iteration_replies_count = 0
            iteration_comments = []
            if next_view_token == '':
                # get the initial response
                comment_list = self.get_comment_list(youtube, video_id, "")
            else:
                # get the next page response
                comment_list = self.get_comment_list(youtube, video_id, next_view_token)

            for comment in comment_list['items']:
                # get number of replies
                reply_count = comment['snippet']['totalReplyCount']

                all_replies = []

                # if replies greater than 0
                if reply_count > 0:
                    # get first 100 replies
                    replies_list = self.get_replies_list(youtube, comment['id'], "")

                    for reply in replies_list['items']:
                        # add reply to list
                        all_replies.append(reply)
                        iteration_replies_count += 1

                    # check for more replies
                    while "nextPageToken" in replies_list:
                        token_reply = replies_list['nextPageToken']
                        # get next set of 100 replies
                        replies_list = self.get_replies_list(youtube, comment['id'], token_reply)

                        for reply in replies_list['items']:
                            # add reply to list
                            all_replies.append(reply)
                            iteration_replies_count += 1

                comment["replies"] = all_replies
                # add comment to list
                iteration_comments.append(comment)
                iteration_comments_count += 1

            posterior_comments_count, posterior_reply_count = self.get_posterior_counts(iteration_comments, movie)
            logging.info(
                "Worker Number {}, Iteration results: posterior_comments_count: {} from {}, posterior_reply_count: {} from {} ".format(
                    self.worker_number, posterior_comments_count, iteration_comments_count, posterior_reply_count, iteration_replies_count))

            if posterior_comments_count == 0 and posterior_reply_count == 0:
                iterations_in_zero_count += 1
            else:
                total_posterior_comments_count += posterior_comments_count
                total_posterior_reply_count += posterior_reply_count

            if iterations_in_zero_count >= 5:
                break

            if "nextPageToken" in comment_list:
                next_view_token = comment_list['nextPageToken']
            else:
                break

        return total_posterior_comments_count, total_posterior_reply_count

    def run(self):
        logging.info("Worker Number {}, Started, Api_key {} ".format(self.worker_number, self.api_key))
        while True:
            try:
                selected_trailer = self.tasks_queue.get()
                logging.info("Worker Number {}, Processing: Movie UniqueID {}, Trailer ID {}".format(self.worker_number, selected_trailer["uniqueID"],
                                                                                selected_trailer[
                                                                                    "trailer_id"]))
                founded_movie = None
                for movie in movies:
                    if movie["uniqueID"] == selected_trailer["uniqueID"]:
                        founded_movie = movie

                video_id = selected_trailer["video_url"].replace("https://www.youtube.com/watch?v=", "")
                total_posterior_comments_count, total_posterior_reply_count = self.get_delete_comments_count(
                    self.youtube,
                    video_id,
                    founded_movie)

                logging.info(
                    "Worker Number {}, From total comment count, must delete total_posterior_comments_count: {} + total_posterior_reply_count: {} ".format(
                        self.worker_number, total_posterior_comments_count, total_posterior_reply_count))
                self.tasks_queue.task_done()
            except Exception as e:
                logging.info("Worker Number {}, Exception {}".format(self.worker_number, str(e)))



tasks_queue = queue.Queue()

for selected_trailer in reversed(selected_trailers):
    tasks_queue.put(selected_trailer)
    break

workers = []

worker_number = 0
for api_key in api_keys:
    worker = CommentsScraperWorker(worker_number, tasks_queue, api_key, movies)
    worker.start()
    workers.append(worker)
    worker_number += 1

tasks_queue.join()
