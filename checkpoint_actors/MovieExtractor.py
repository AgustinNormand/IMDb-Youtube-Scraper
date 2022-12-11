with open("StarsScraper(0RaitingMovies).log", "r") as f:
    with  open("checkpoint_actor_movies_scraped.csv", "w") as f2:
        lines = f.readlines()
        for line in lines:
            if "requested" in line and "raiting" in line:
                first_split = line.split("requested")[1]
                href, rest = first_split.split(",")
                href = href.strip()
                raiting = float(rest.split("raiting ")[1].replace("\n", ""))
                f2.write("{},{}\n".format(href, raiting))

# TODO Agregar del nuevo log las peticiones de raiting 0
