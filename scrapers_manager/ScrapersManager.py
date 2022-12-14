from first_source_scraper.FirstSourceScraper import FirstSourceScraper
from scrapers_manager.ResultsProcessor import ResultsProcessor
from second_source_scraper.SecondSourceScraper import SecondSourceScraper
from third_source_scraper.ThirdSourceScraper import ThirdSourceScraper
import threading
import queue
import time
import logging
import csv
import ast


class ScrapersManager():

    def __init__(self):
        self.firstScraperQueue = queue.Queue()
        self.first_source_scraper = FirstSourceScraper(self.firstScraperQueue)

        self.secondScraperQueue = queue.Queue()
        self.second_source_scraper = SecondSourceScraper(self.firstScraperQueue, self.secondScraperQueue)

        self.thirdScraperQueue = queue.Queue()
        self.third_source_scraper = ThirdSourceScraper(self.secondScraperQueue, self.thirdScraperQueue)

        self.results_processor = ResultsProcessor(self.thirdScraperQueue)

        self.logger = logging.getLogger("ScrapersManager")

    def begin_scrape(self):
        start_time = time.time()

        first_source_scraper_thread = threading.Thread(target=self.first_source_scraper.begin_scrape, daemon=True)
        first_source_scraper_thread.start()

        second_source_scraper_thread = threading.Thread(target=self.second_source_scraper.begin_scrape, daemon=True)
        second_source_scraper_thread.start()

        second_source_scraper_thread2 = threading.Thread(target=self.second_source_scraper.begin_scrape, daemon=True)
        second_source_scraper_thread2.start()

        third_source_scraper_thread = threading.Thread(target=self.third_source_scraper.begin_scrape, daemon=True)
        third_source_scraper_thread.start()

        results_processor_thread = threading.Thread(target=self.results_processor.process_results, daemon=True)
        results_processor_thread.start()

        first_source_scraper_thread.join()
        second_source_scraper_thread.join()
        second_source_scraper_thread2.join()
        third_source_scraper_thread.join()
        results_processor_thread.join()

        self.first_source_scraper.log_measurements()
        self.second_source_scraper.log_measurements()
        self.third_source_scraper.log_measurements()
        self.results_processor.log_measurements()

        total_time_elapsed = time.time() - start_time

        self.logger.info("Total time whole scraping {:.3g} minutes".format(total_time_elapsed/60))

    def begin_scrape_from_third_scraper(self):
        start_time = time.time()

        third_source_scraper_thread = threading.Thread(target=self.third_source_scraper.begin_scrape, daemon=True)
        third_source_scraper_thread.start()

        results_processor_thread = threading.Thread(target=self.results_processor.process_results, daemon=True)
        results_processor_thread.start()

        csv_filename = 'checkpoint.csv'
        with open(csv_filename) as f:
            reader = csv.DictReader(f)
            lst = list(reader)
        for item in lst:
            item["actors"] = ast.literal_eval(item["actors"])
            if item["writers"] == "":
                item["writers"] = []
            else:
                item["writers"] = ast.literal_eval(item["writers"])

            if item["directors"] == "":
                item["directors"] = []
            else:
                item["directors"] = ast.literal_eval(item["directors"])
            self.secondScraperQueue.put(item)

        self.secondScraperQueue.put("NO_MORE_MOVIES")
        print("File Readed")

        third_source_scraper_thread.join()
        results_processor_thread.join()

        self.third_source_scraper.log_measurements()
        self.results_processor.log_measurements()

        total_time_elapsed = time.time() - start_time

        self.logger.info("Total time whole scraping {:.3g} minutes".format(total_time_elapsed/60))