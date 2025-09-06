from models.movie import Movie
from utils.imdb import get_movie_details, search_movies as search_movies_api
import sqlite3
from utils.db_adapter import connect

class MovieController:
    def __init__(self, db_path):
        self.movie_model = Movie(db_path)
        self.db_path = db_path
        self.available_movie_ids_cache = None  # Cache para IDs de películas disponibles

    def _get_available_movie_ids(self):
        if self.available_movie_ids_cache is None:
            with connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT imdb_id FROM movies WHERE available = 1')
                rows = cursor.fetchall()
                ids = set()
                for row in rows:
                    if isinstance(row, (tuple, list)):
                        ids.add(row[0])
                    else:
                        ids.add(row.get('imdb_id'))
                self.available_movie_ids_cache = ids  # Usar un set para búsquedas rápidas
        return self.available_movie_ids_cache

    def search_movies(self, query):
        results = search_movies_api(query)

        if 'Search' in results:
            filtered_results = [movie for movie in results['Search'] if movie['Type'] == 'movie']
            available_movies = self._get_available_movie_ids()

            for movie in filtered_results:
                movie['is_available'] = movie['imdbID'] in available_movies

            results['Search'] = filtered_results

        return results

    def get_movie_details(self, movie_id):
        # recoger video_link y available de nuestra DB primero
        with connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT video_link, available FROM movies WHERE imdb_id = ?', (movie_id,))
            row = cursor.fetchone()
            if row:
                # row may be tuple (sqlite) or dict (pg adapter)
                video_link = row[0] if isinstance(row, (tuple, list)) else row.get('video_link')
                if isinstance(row, (tuple, list)):
                    available = bool(row[1])
                else:
                    val = row.get('available')
                    available = bool(val)
            else:
                video_link, available = None, False

        movie_details = get_movie_details(movie_id)
        if 'errorMessage' in movie_details:
            return None

        return {
            'title': movie_details.get('Title', 'N/A'),
            'year': movie_details.get('Year', 'N/A'),
            'poster': movie_details.get('Poster', 'N/A'),
            'imdb_rating': movie_details.get('imdbRating', 'N/A'),
            'director': movie_details.get('Director', 'N/A'),
            'runtime': movie_details.get('Runtime', 'N/A'),
            'plot': movie_details.get('Plot', 'N/A'),
            'imdb_id': movie_id,
            'language': movie_details.get('Language', 'N/A'),
            'country': movie_details.get('Country', 'N/A'),
            'awards': movie_details.get('Awards', 'N/A'),
            'actors': movie_details.get('Actors', 'N/A'),
            'genre': movie_details.get('Genre', 'N/A'),
            'is_available': (video_link is not None) or available,
            'video_link': video_link
        }

    def get_all_movies(self):
        return self.movie_model.get_all_movies()

    def get_available_movies(self):
        available_movie_ids = self._get_available_movie_ids()
        movies = []
        for movie_id in available_movie_ids:
            details = self.get_movie_details(movie_id)
            if details:
                movies.append(details)
        return movies

    def search_movies_realtime(self, query):
        results = self.search_movies(query)
        return results.get('Search', [])[:5]

    def get_random_recommendations(self, count=16):
        # Pull lightweight data directly from DB to avoid many external API calls
        with connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT imdb_id, title, year, poster FROM movies WHERE available = 1 ORDER BY RANDOM() LIMIT ?', (count,))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                if isinstance(row, (tuple, list)):
                    imdb_id, title, year, poster = row[0], row[1], row[2], row[3]
                else:
                    imdb_id, title, year, poster = row.get('imdb_id'), row.get('title'), row.get('year'), row.get('poster')
                results.append({
                    'imdb_id': imdb_id,
                    'title': title,
                    'year': year,
                    'poster': poster or 'https://via.placeholder.com/300x450?text=No+Poster'
                })
            return results

    def get_all_genres(self):
        with connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT genres FROM movies WHERE genres IS NOT NULL AND genres != ''")
            genres = cursor.fetchall()
            all_genres = set()
            for genre_row in genres:
                value = genre_row[0] if isinstance(genre_row, (tuple, list)) else genre_row.get('genres')
                if value:
                    all_genres.update(genre.strip() for genre in value.split(','))
            return sorted(all_genres)

    def get_top_actors(self, limit=100):
        with connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT actors FROM movies WHERE actors IS NOT NULL AND actors != ''")
            actors = cursor.fetchall()
            all_actors = set()
            for actor_row in actors:
                value = actor_row[0] if isinstance(actor_row, (tuple, list)) else actor_row.get('actors')
                if value:
                    all_actors.update(actor.strip() for actor in value.split(','))
            return sorted(all_actors)[:limit]

    def get_top_directors(self, limit=50):
        with connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT director FROM movies WHERE director IS NOT NULL AND director != '' ORDER BY director ASC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                result.append(row[0] if isinstance(row, (tuple, list)) else row.get('director'))
            return result

    def get_recommendations(self, user_id, genre=None, actor=None, director=None):
        with connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = """
            SELECT DISTINCT m.*
            FROM movies m
            LEFT JOIN favorites f ON m.id = f.movie_id AND f.user_id = ?
            WHERE f.id IS NULL AND m.available = 1
            """
            params = [user_id]

            if genre:
                query += " AND m.genres LIKE ?"
                params.append(f"%{genre}%")
            if actor:
                query += " AND m.actors LIKE ?"
                params.append(f"%{actor}%")
            if director:
                query += " AND m.director LIKE ?"
                params.append(f"%{director}%")

            query += " ORDER BY m.imdb_rating DESC LIMIT 6"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            # normalize rows to dicts when possible
            return [dict(r) if hasattr(r, 'keys') else {
                'id': r[0], 'imdb_id': r[1], 'title': r[2], 'year': r[3], 'poster': r[4], 'plot': r[5],
                'director': r[6], 'actors': r[7], 'genres': r[8], 'imdb_rating': r[9], 'release_date': r[10],
                'runtime': r[11], 'language': r[12], 'country': r[13], 'awards': r[14], 'available': r[15], 'video_link': r[16]
            } for r in rows]