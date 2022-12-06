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

    def perform_requests(self, names, urls, no_workers, movie_url, scraped_movies):
        class Worker(Thread):
            def __init__(self, request_queue):
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

            def get_movies_previous_to(self, movie_url, actor_movies):
                movie_url_title = movie_url.split("imdb.com")[1]
                found_movie = False
                previous_movies = []
                for actor_movie_url in actor_movies:
                    actor_movie_url_title = actor_movie_url.split("imdb.com")[1]
                    if found_movie:
                        previous_movies.append(actor_movie_url)
                    else:
                        if movie_url_title == actor_movie_url_title:
                            found_movie = True
                        else:
                            continue
                return previous_movies

            def scrape_previous_movies_raiting_until_75(self, previous_movies, scraped_movies):
                for previous_movie in previous_movies:
                    status_code, text = self.request(previous_movie)
                    soup = BeautifulSoup(text, "html.parser")
                    div = soup.find("div", {"data-testid": "hero-rating-bar__aggregate-rating__score"})
                    if div != None:
                        raiting = float(div.find("span").get_text())
                        scraped_movies[movie_url] = raiting
                        if raiting >= 7.5:
                            return True
                    else:
                        scraped_movies[movie_url] = None

                return False

            def any_previous_is_in_scraped_with_more_than_75(self, previous_movies, scraped_movies):
                print('Previous Movies {}'.format(previous_movies))
                print("Scraped Movies {}".format(scraped_movies))
                for previous_movie in previous_movies:
                    if previous_movie in scraped_movies.keys():
                        if scraped_movies[previous_movie] >= 7.5:
                            print("previous_is_in_scraped_with_more_than_75")
                            return True
                return False

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
                    actor_movies = self.parse_actor_page(text, url)
                    previous_movies = self.get_movies_previous_to(movie_url, actor_movies)
                    if self.any_previous_is_in_scraped_with_more_than_75(previous_movies, scraped_movies):
                        is_star = True
                    else:
                        is_star = self.scrape_previous_movies_raiting_until_75(previous_movies, scraped_movies)

                    self.results.append([name, actor_movies, is_star, scraped_movies])
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

    def scrape_actors(self, names, urls, scraped_actors, movie_url, scraped_movies):
        workers_responses = self.perform_requests(names, urls, 18, movie_url, scraped_movies)
        star_count = 0
        for worker_response in workers_responses:
            name, actor_movies, is_star, new_scraped_movies = worker_response
            if is_star:
                star_count += 1
            scraped_actors[name] = actor_movies
            #for movie_url in new_scraped_movies:
            #    scraped_movies[movie_url] = new_scraped_movies[movie_url]
            scraped_movies = new_scraped_movies
        return scraped_actors, scraped_movies, star_count


