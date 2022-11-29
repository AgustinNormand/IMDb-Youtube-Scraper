from first_source_scraper.FirstSourceScraper import FirstSourceScraper
from scrapers_manager.ResultsProcessor import ResultsProcessor
from second_source_scraper.SecondSourceScraper import SecondSourceScraper
from third_source_scraper.ThirdSourceScraper import ThirdSourceScraper
import threading
import queue
import time
import logging

class ScrapersManager():

    def __init__(self):
        self.firstScraperQueue = queue.Queue()
        self.first_source_scraper = FirstSourceScraper(self.firstScraperQueue)

        self.secondScraperQueue = queue.Queue()
        self.second_source_scraper = SecondSourceScraper(self.firstScraperQueue, self.secondScraperQueue)

        self.thirdScraperQueue = queue.Queue()
        self.third_source_scraper = ThirdSourceScraper(self.secondScraperQueue, self.thirdScraperQueue)

        self.results_processor = ResultsProcessor(self.thirdScraperQueue)

        self.logger = None
        self.configure_logger()

    def configure_logger(self):
        self.logger = logging.getLogger("ScrapersManager")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler('./scrapers_manager/ScrapersManager.log', mode='w')
        file_handler.setFormatter(formatter)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)


    def begin_scrape(self):
        start_time = time.time()

        first_source_scraper_thread = threading.Thread(target=self.first_source_scraper.begin_scrape, daemon=True)
        first_source_scraper_thread.start()

        second_source_scraper_thread = threading.Thread(target=self.second_source_scraper.begin_scrape, daemon=True)
        second_source_scraper_thread.start()

        third_source_scraper_thread = threading.Thread(target=self.third_source_scraper.begin_scrape, daemon=True)
        third_source_scraper_thread.start()

        results_processor_thread = threading.Thread(target=self.results_processor.process_results, daemon=True)
        results_processor_thread.start()

        first_source_scraper_thread.join()
        second_source_scraper_thread.join()
        third_source_scraper_thread.join()
        results_processor_thread.join()

        self.first_source_scraper.log_measurements()
        self.second_source_scraper.log_measurements()
        self.third_source_scraper.log_measurements()
        self.results_processor.log_measurements()

        total_time_elapsed = time.time() - start_time

        #self.logger.info("Total time whole scraping {:.3g} seconds".format(total_time_elapsed))
