from bs4 import BeautifulSoup
from fp.fp import FreeProxy
import queue
from threading import Thread
import requests
from fake_headers import Headers
from requests.adapters import HTTPAdapter, Retry
import constants
import time

class ActorScraper:

    def perform_requests(self, names, urls, no_workers):
        class Worker(Thread):
            def __init__(self, request_queue):
                #print("Worker started")
                Thread.__init__(self)
                self.queue = request_queue
                self.results = []
                self.session = requests.Session()
                retry = Retry(connect=5, backoff_factor=0.5)
                adapter = HTTPAdapter(max_retries=retry)
                self.session.mount('http://', adapter)
                self.session.mount('https://', adapter)
                self.session.headers.update(Headers().generate())
                self.last_request_timestamp = time.time()

            def sleep_if_needed(self):
                remaining_to_second_between_requests = constants.SECONDS_TO_SLEEP_BETWEEN_REQUESTS - (
                        time.time() - self.last_request_timestamp)
                if remaining_to_second_between_requests > 0:
                    time.sleep(remaining_to_second_between_requests)

            def request(self, url):
                self.sleep_if_needed()
                r = self.session.get(url=url, proxies=self.proxies)
                self.last_request_timestamp = time.time()
                return [r.status_code, r.text]

            def parse_actor_page(self, text, actor_url):
                soup = BeautifulSoup(text, "html.parser")
                movie_section = soup.find("section", {"id": "name-filmo-content"})
                divs_movies = movie_section.find_all("div", {"class": "col-xs-12"})
                if len(divs_movies) == 0:
                    if "actor" in actor_url:
                        actress_url = actor_url.replace("actor", "actress")
                        status_code, text = self.request(actress_url)
                        return self.parse_actor_page(text, actress_url)
                else:
                    movies = []
                    for div_movie in divs_movies:
                        href = div_movie.find("a", {"class": "subpage"})["href"].split("/?")[0]
                        url = constants.ACTORS_IMDb_URL + href
                        movies.append(url)
                    return movies

            def run(self):
                proxy = FreeProxy(country_id=['AR'], rand=True, timeout=0.5).get()
                self.proxies = {
                    "http": proxy
                }
                while True:
                    content = self.queue.get()
                    if content == "":
                        break
                    name, url = content
                    status_code, text = self.request(url)
                    #print("Requested {}".format(url))
                    self.results.append([name, self.parse_actor_page(text, url)])
                    self.queue.task_done()

        q = queue.Queue()
        for tuple in zip(names,urls):
            q.put([tuple[0], tuple[1]])

        for _ in range(no_workers):
            q.put("")

        workers = []
        for _ in range(no_workers):
            worker = Worker(q)
            worker.start()
            workers.append(worker)

        for worker in workers:
            worker.join()
        r = []

        for worker in workers:
            r.extend(worker.results)
        return r

    def scrape_actors(self, names, urls, scraped_actors):
        #print("In Scrape_Actors function")
        workers_responses = self.perform_requests(names, urls, 10)
        for worker_response in workers_responses:
            name, movies = worker_response
            #print("Response for {}, movies {}".format(name, movies))
            scraped_actors[name] = movies
        return scraped_actors


