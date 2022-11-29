import logging

from first_source_scraper.FirstSourceScraper import FirstSourceScraper
from second_source_scraper.SecondSourceScraper import SecondSourceScraper
from third_source_scraper.ThirdSourceScraper import ThirdSourceScraper
import pandas as pd

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

def export_results(movies):
    data = pd.DataFrame.from_dict(movies, orient='index')
    data.insert(0, "uniqueID", list(movies.keys()))
    data.to_csv("results.csv", index=False)

if __name__ == "__main__":
    first_source_scraper = FirstSourceScraper()
    movies = first_source_scraper.start()
    first_source_scraper.log_measurements()

    #second_source_scraper = SecondSourceScraper()
    #movies = second_source_scraper.start(movies)

    #third_source_scraper = ThirdSourceScraper()
    #third_source_scraper.start(movies)

    export_results(movies)