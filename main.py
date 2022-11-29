import logging

from scrapers_manager.ScrapersManager import ScrapersManager

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
    sm = ScrapersManager()
    sm.begin_scrape()