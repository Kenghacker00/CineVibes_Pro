import sqlite3
import random
import string
from werkzeug.security import generate_password_hash
from datetime import datetime
from utils.email import send_verification_email
from utils.db_adapter import connect

class AuthController:
    def __init__(self, db_path):
        self.db_path = db_path

    def register(self, nickname, email, password):
        # Generar un código de verificación
        verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Guardar el usuario con el código de verificación
        with connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (nickname, email, password, verification_code, is_verified)
                VALUES (?, ?, ?, ?, ?)
            ''', (nickname, email, generate_password_hash(password), verification_code, False))
            user_id = cursor.lastrowid

        # Enviar el correo de verificación
        send_verification_email(email, verification_code)

        return user_id

    def verify_code(self, email, code):
        with connect(self.db_path) as conn:
            cursor = conn.cursor()
            user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            # user can be dict or tuple
            vcode = None
            uid = None
            if user is not None:
                if isinstance(user, (tuple, list)):
                    # indexes: id, nickname, email, password, verification_code, is_verified, profile_pic, created_at
                    uid = user[0]
                    vcode = user[4] if len(user) > 4 else None
                else:
                    uid = user.get('id')
                    vcode = user.get('verification_code')
            if user and vcode == code:
                # Marcar al usuario como verificado
                cursor.execute('UPDATE users SET is_verified = TRUE WHERE id = ?', (uid,))
                conn.commit()
                return True
        return False

    def get_user_profile(self, user_id):
        with connect(self.db_path) as conn:
            # Use conn.execute to ensure placeholder normalization on Postgres
            user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            if user:
                # user can be sqlite Row (dict-like) or dict (PG adapter)
                raw_created = user['created_at'] if not isinstance(user, (tuple, list)) else None
                formatted_date = None
                if raw_created:
                    try:
                        # intentos comunes de formato
                        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
                            try:
                                formatted_date = datetime.strptime(raw_created, fmt).strftime('%d/%m/%Y')
                                break
                            except ValueError:
                                continue
                    except Exception:
                        formatted_date = None

                if isinstance(user, (tuple, list)):
                    # Fallback in unlikely tuple case: map by index (assuming schema order)
                    uid, nickname, email = user[0], user[1], user[2]
                    profile_pic = user[6] if len(user) > 6 else None
                    is_verified = bool(user[5]) if len(user) > 5 else False
                    return {
                        'id': uid,
                        'nickname': nickname,
                        'email': email,
                        'profile_pic': profile_pic,
                        'is_verified': is_verified,
                        'created_at': formatted_date or ''
                    }
                else:
                    return {
                        'id': user.get('id'),
                        'nickname': user.get('nickname'),
                        'email': user.get('email'),
                        'profile_pic': user.get('profile_pic'),
                        'is_verified': user.get('is_verified'),
                        'created_at': formatted_date or ''
                    }
        return None

    def update_profile_pic(self, user_id, profile_pic_path):
        with connect(self.db_path) as conn:
            conn.execute(
                'UPDATE users SET profile_pic = ? WHERE id = ?',
                (profile_pic_path, user_id)
            )
            conn.commit()

    def update_user_profile(self, user_id, nickname, email, password):
        with connect(self.db_path) as conn:
            try:
                # Actualizar nickname y email
                conn.execute('UPDATE users SET nickname = ?, email = ? WHERE id = ?', (nickname, email, user_id))

                # Si se proporciona una nueva contraseña, actualizarla
                if password:
                    hashed_password = generate_password_hash(password)
                    conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))
                conn.commit()
                # Considera éxito si no hubo excepción
                return True
            except Exception as e:
                # sqlite dup or postgres unique violation
                msg = str(e).lower()
                if isinstance(e, sqlite3.IntegrityError) or 'unique' in msg or 'duplicate' in msg or '23505' in msg:
                    # Señal explícita para email duplicado u otro campo único
                    return False
                raise
        return False
