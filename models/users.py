import sqlite3
from werkzeug.security import generate_password_hash

class User:
    def __init__(self, db_path):
        self.db_path = db_path

    def create_user(self, nickname, email, password, verification_code):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (nickname, email, password, verification_code, is_verified)
                VALUES (?, ?, ?, ?, ?)
            ''', (nickname, email, generate_password_hash(password), verification_code, False))
            return cursor.lastrowid

    def get_user_by_email(self, email):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            return cursor.fetchone()

    def set_user_verified(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('UPDATE users SET is_verified = TRUE WHERE id = ?', (user_id,))

    def get_user_by_id(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            return cursor.fetchone()

    def update_profile_pic(self, user_id, profile_pic_path):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'UPDATE users SET profile_pic = ? WHERE id = ?',
                (profile_pic_path, user_id)
            )
            conn.commit()
