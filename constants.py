SECONDS_TO_SLEEP_BETWEEN_REQUESTS = 0
BOX_OFFICE_MOJO_BASE_URL = "https://www.boxofficemojo.com"
BOX_OFFICE_MOJO_OPENINGS_URL = BOX_OFFICE_MOJO_BASE_URL + "/chart/top_opening_weekend/"
BOX_OFFICE_MOJO_WORST_OPENINGS_URL = BOX_OFFICE_MOJO_BASE_URL + "/chart/btm_wide_opening_weekend_theater_avg/"
IMDb_URL = "https://www.imdb.com"
ACTORS_IMDb_URL = "https://m.imdb.com"

START_FROM_CHECKPOINT_IMDb_SCRAPER = True

PROCESS_STARS = False
USE_MOVIES_CHECKPOINT_STAR_SCRAPER = True
USE_ACTORS_CHECKPOINT_STAR_SCRAPER = False

MONTHS = {
    'jan': 1,
    'feb': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12
}