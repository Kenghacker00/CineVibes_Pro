import sqlite3

class Movie:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_movie_by_id(self, movie_id):
        with sqlite3.connect(self.db_path) as conn:
            movie = conn.execute('SELECT * FROM movies WHERE id = ?', (movie_id,)).fetchone()
        return movie

    def add_movie(self, movie_data, available: int = 1, video_link: str | None = None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO movies (
                    imdb_id, title, year, poster, director, runtime, plot, language, country, awards, actors, genres, imdb_rating, release_date, available, video_link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                movie_data.get('imdbID') or movie_data.get('imdb_id'),
                movie_data.get('Title') or movie_data.get('title'),
                movie_data.get('Year') or movie_data.get('year'),
                movie_data.get('Poster') or movie_data.get('poster'),
                movie_data.get('Director') or movie_data.get('director'),
                movie_data.get('Runtime') or movie_data.get('runtime'),
                movie_data.get('Plot') or movie_data.get('plot'),
                movie_data.get('Language') or movie_data.get('language'),
                movie_data.get('Country') or movie_data.get('country'),
                movie_data.get('Awards') or movie_data.get('awards'),
                movie_data.get('Actors') or movie_data.get('actors'),
                movie_data.get('Genre') or movie_data.get('genres'),
                movie_data.get('imdbRating') or movie_data.get('imdb_rating'),
                movie_data.get('Released') or movie_data.get('release_date'),
                available,
                video_link,
            ))
            conn.commit()

    def get_all_movies(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            movies = conn.execute('SELECT imdb_id FROM movies').fetchall()
        return [movie['imdb_id'] for movie in movies]
