import logging

from first_source_scraper.FirstSourceScraper import FirstSourceScraper
from second_source_scraper.SecondSourceScraper import SecondSourceScraper
from third_source_scraper.ThirdSourceScraper import ThirdSourceScraper

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='debug.log',
                    filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)


if __name__ == "__main__":
    first_source_scraper = FirstSourceScraper()
    movies = first_source_scraper.start()
    first_source_scraper.log_measurements()

    third_source_scraper = ThirdSourceScraper()
    third_source_scraper.start(movies)
