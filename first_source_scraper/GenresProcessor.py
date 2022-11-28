class GenresProcessor:
    def __init__(self):
        self.unique_genres = []

    def obtain_unique_genres_list(self, movies):
        for uniqueID in movies:
            for genre in movies[uniqueID]["genres"]:
                if genre not in self.unique_genres:
                    self.unique_genres.append(genre)

    def create_genres_columns(self, movies):
        for uniqueID in movies:
            for genre in self.unique_genres:
                if genre not in movies[uniqueID]["genres"]:
                    movies[uniqueID][genre] = 0
                else:
                    movies[uniqueID][genre] = 1

    def drop_genres_column(self, movies):
        for uniqueID in movies:
            movies[uniqueID].pop("genres")

    def process_genres(self, movies):
        self.obtain_unique_genres_list(movies)
        self.create_genres_columns(movies)
        self.drop_genres_column(movies)
        return movies