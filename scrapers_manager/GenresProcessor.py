class GenresProcessor:
    def __init__(self):
        self.unique_genres = []

    def obtain_unique_genres_list(self, movies):
        for movie in movies:
            if "genres" in movie.keys():
                for genre in movie["genres"]:
                    if genre not in self.unique_genres:
                        self.unique_genres.append(genre)

    def create_genres_columns(self, movies):
        for index, movie in enumerate(movies):
            for genre in self.unique_genres:
                if "genres" in movie.keys():
                    if genre not in movie["genres"]:
                        movies[index][genre] = 0
                    else:
                        movies[index][genre] = 1
                else:
                    movies[index][genre] = 0
        return movies

    def drop_genres_column(self, movies):
        for movie in movies:
            if "genres" in movie.keys():
                movie.pop("genres")
        return movies

    def process_genres(self, movies):
        self.obtain_unique_genres_list(movies)
        movies = self.create_genres_columns(movies)
        movies = self.drop_genres_column(movies)
        return movies