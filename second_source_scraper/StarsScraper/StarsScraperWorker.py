from threading import Thread
import logging
import time

class StarsScraperWorker(Thread):
    def __init__(self, worker_number, tasks_queue, scraped_actors):
        Thread.__init__(self)
        self.worker_number = worker_number
        self.tasks_queue = tasks_queue
        self.logger = logging.getLogger("StarsScraper")
        self.scraped_actors = scraped_actors

    def run(self):
        while True:
            if self.worker_number == 0:
                print(self.scraped_actors)
                time.sleep(10)
            if self.worker_number == 1:
                self.scraped_actors["algo"] = "Hola"
        #print(self.worker_number)
