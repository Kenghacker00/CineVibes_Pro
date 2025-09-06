import sqlite3
from utils.db_adapter import connect

class ReviewController:
    def __init__(self, db):
        # db here is a path string used to connect directly in this controller
        self.db = db

    def add_review(self, user_id, movie_id, review_text, rating):
        """
        Añade una nueva reseña
        """
        with connect(self.db) as conn:
            conn.execute(
                'INSERT INTO reviews (user_id, movie_id, review_text, rating) VALUES (?, ?, ?, ?)',
                (user_id, movie_id, review_text, rating)
            )
            conn.commit()
        return {'success': True, 'message': 'Reseña enviada.'}

    def get_user_reviews(self, user_id):
        """
        Obtiene todas las reseñas de un usuario específico
        """
        with connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, m.title as movie_title
                FROM reviews r
                JOIN movies m ON r.movie_id = m.imdb_id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC
            ''', (user_id,))
            reviews = cursor.fetchall()

            # Convertir los resultados a una lista de diccionarios
            return [{
                'id': review['id'],
                'movie_title': review['movie_title'],
                'review_text': review['review_text'],
                'rating': review['rating'],
                'created_at': review['created_at']
            } for review in reviews]

    def get_movie_reviews(self, movie_id):
        """
        Obtiene todas las reseñas de una película específica
        """
        with connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, u.nickname as user_nickname, u.profile_pic as user_profile_pic
                FROM reviews r
                JOIN users u ON r.user_id = u.id
                WHERE r.movie_id = ?
                ORDER BY r.created_at DESC
            ''', (movie_id,))
            reviews = cursor.fetchall()

            # Convertir los resultados a una lista de diccionarios
            return [{
                'id': review['id'],
                'user_nickname': review['user_nickname'],
                'user_profile_pic': review['user_profile_pic'],
                'review_text': review['review_text'],
                'rating': review['rating'],
                'created_at': review['created_at'],
                'user_id': review['user_id']  # Asegúrate de incluir el user_id
            } for review in reviews]

    def delete_review(self, review_id, user_id):
        """
        Elimina una reseña específica (solo si pertenece al usuario)
        """
        with connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM reviews WHERE id = ? AND user_id = ?',
                (review_id, user_id)
            )
            conn.commit()
            if cursor.rowcount > 0:
                return {'success': True, 'message': 'Reseña eliminada.'}
            return {'success': False, 'message': 'No se pudo eliminar la reseña.'}

    def update_review(self, review_id, user_id, review_text, rating):
        """
        Actualiza una reseña existente
        """
        with connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reviews
                SET review_text = ?, rating = ?
                WHERE id = ? AND user_id = ?
            ''', (review_text, rating, review_id, user_id))
            conn.commit()
            if cursor.rowcount > 0:
                return {'success': True, 'message': 'Reseña actualizada.'}
            return {'success': False, 'message': 'No se pudo actualizar la reseña.'}

    def get_user_reviews_with_movies(self, user_id):
        with connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, m.title as movie_title, m.poster as movie_poster, m.imdb_id
                FROM reviews r
                JOIN movies m ON r.movie_id = m.imdb_id
                WHERE r.user_id = ?
                ORDER BY r.created_at DESC
            ''', (user_id,))
            reviews = cursor.fetchall()

        return [{
            'id': review['id'],
            'movie_title': review['movie_title'],
            'movie_poster': review['movie_poster'],
            'imdb_id': review['movie_id'],
            'review_text': review['review_text'],
            'rating': review['rating'],
            'created_at': review['created_at']
        } for review in reviews]

    def get_user_review_count(self, user_id):
        """
        Obtiene el número total de reseñas hechas por un usuario
        """
        with connect(self.db) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM reviews WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if isinstance(row, (tuple, list)):
                return row[0]
            try:
                return next(iter(row.values()))
            except Exception:
                return 0


