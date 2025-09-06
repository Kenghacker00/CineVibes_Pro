from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g, abort
from werkzeug.security import check_password_hash
from controllers.auth import AuthController
from controllers.movie import MovieController
from controllers.review import ReviewController
from utils.email import send_verification_email, send_movie_request_email
from utils.imdb import get_movie_details_by_title
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField
from config import Config
from pathlib import PurePosixPath
import time, uuid
import os, shutil
import random
import sqlite3
from database import db
from math import ceil
from datetime import timedelta
from flask_caching import Cache
from utils.db_adapter import connect, using_postgres
from utils.supabase_storage import is_enabled as storage_enabled, upload_bytes as storage_upload, delete_object as storage_delete, public_url as storage_public_url
try:
    from flask_compress import Compress
except ImportError:
    Compress = None

# -------------------------
# App & Config
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = int(os.getenv('STATIC_MAX_AGE', '3600'))

from werkzeug.exceptions import RequestEntityTooLarge

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash('El archivo es demasiado grande. Máximo 2 MB y solo JPG/PNG.', 'error')
    return redirect(url_for('profile'))  # redirige al perfil

# Caché (simple para empezar; cambia a Redis/Memcached en prod)
cache = Cache(app, config={'CACHE_TYPE': os.getenv('CACHE_TYPE', 'simple')})
if Compress is not None:
    Compress(app)

# Context processor para año actual
@app.context_processor
def inject_current_year():
    from datetime import datetime as _dt
    return {"current_year": _dt.now().year}

# -------------------------
# Controllers
# -------------------------
db_path = Config.DATABASE
os.makedirs(os.path.dirname(db_path), exist_ok=True)
if not os.path.exists(db_path) and os.path.exists("database/cinevibes.db"):
    shutil.copy("database/cinevibes.db", db_path)
auth_controller = AuthController(db_path)
movie_controller = MovieController(db_path)
review_controller = ReviewController(db_path)

# -------------------------
# Forms
# -------------------------
class ProfileForm(FlaskForm):
    profile_pic = FileField('Foto de Perfil', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Solo se permiten imágenes.')
    ])
    submit = SubmitField('Actualizar')

# -------------------------
# Helpers optimizados
# -------------------------

def _get_conn():
    """Usa la misma conexión por request cuando sea posible."""
    conn = getattr(g, '_db_conn', None)
    if conn is None:
        # if DATABASE_URL present use Postgres, else SQLite
        if using_postgres():
            conn = connect(None)
        else:
            conn = db.get_db()
            conn.row_factory = sqlite3.Row
        g._db_conn = conn
    return conn

@cache.memoize(timeout=60)
def load_user_profile_cached(user_id: int):
    """Cargar el perfil del usuario con caché corto (60s)."""
    if not user_id:
        return None
    return auth_controller.get_user_profile(user_id)

@app.before_request
def load_user_into_g():
    """Cargar el usuario en g.user usando caché."""
    # Evita tocar DB para archivos estáticos (mejora rendimiento y evita 500 en assets)
    if request.endpoint == 'static':
        return
    uid = session.get('user_id')
    g.user = load_user_profile_cached(uid) if uid else None

@app.teardown_appcontext
def close_connection(exception):
    conn = getattr(g, '_db_conn', None)
    if conn is not None:
        # db.get_db() maneja contexto, pero cerramos explícito si abrimos directo
        try:
            conn.close()
        except Exception:
            pass

# ---- Paginación cacheada (solo datos, no usuario) ----

@cache.memoize(timeout=60)
def get_total_movies_cached():
    conn = _get_conn()
    row = conn.execute('SELECT COUNT(*) FROM movies').fetchone()
    if isinstance(row, (tuple, list)):
        return row[0]
    try:
        # dict-like from Postgres
        return next(iter(row.values()))
    except Exception:
        return 0

@cache.memoize(timeout=60)
def get_movies_page_cached(per_page: int, page: int):
    """Devuelve lista de filas de movies para la página dada."""
    conn = _get_conn()
    offset = (page - 1) * per_page
    rows = conn.execute(
        'SELECT * FROM movies ORDER BY release_date DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    return rows

# -------------------------
# Rutas
# -------------------------
@app.get("/health")
def health(): return "ok", 200

@app.route('/user/<int:user_id>', endpoint='user_profile')
def user_profile(user_id):
    user_public = auth_controller.get_user_profile(user_id)
    if user_public is None:
        abort(404)
    reviews = review_controller.get_user_reviews_with_movies(user_id)
    return render_template('user_profile.html', user=user_public, reviews=reviews)

@app.route('/')
def index():
    user = g.user
    per_page = 6
    page = request.args.get('page', 1, type=int)

    try:
        total_movies = get_total_movies_cached()
        total_pages = max(ceil(total_movies / per_page), 1)
        recent_movies = get_movies_page_cached(per_page, page)
    except sqlite3.OperationalError:
        recent_movies = []
        total_pages = 1

    return render_template(
        'index.html',
        movies=recent_movies,
        user=user,
        total_pages=total_pages,
        current_page=page
    )

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user = g.user
    if user is None:
        flash('Debes iniciar sesión para editar tu perfil', 'error')
        return redirect(url_for('login'))

    form = ProfileForm()
    if request.method == 'POST':
        nickname = (request.form.get('nickname') or '').strip()
        email = (request.form.get('email') or '').strip()
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not nickname or not email:
            flash('El nickname y el email son obligatorios', 'error')
        else:
            # Permite actualizar nickname/email incluso si la contraseña no coincide
            password_to_set = None
            password_note = None
            if new_password:
                if new_password != (confirm_password or ''):
                    password_note = 'La contraseña no se cambió: las contraseñas no coinciden.'
                else:
                    password_to_set = new_password

            success = auth_controller.update_user_profile(
                user['id'], nickname, email, password_to_set
            )
            if success:
                # Invalida caché de perfil para reflejar cambios
                cache.delete_memoized(load_user_profile_cached, user['id'])
                # Borrado amplio por si la clave memoizada cambió
                try:
                    cache.delete_memoized(load_user_profile_cached)
                except Exception:
                    pass
                # Actualiza g.user para esta request
                try:
                    if isinstance(g.user, dict):
                        g.user['nickname'] = nickname
                        g.user['email'] = email
                except Exception:
                    pass
                if password_note:
                    flash(f'Perfil actualizado. {password_note}', 'warning')
                else:
                    flash('Perfil actualizado con éxito', 'success')
                return redirect(url_for('profile'))
            else:
                flash('No se pudo actualizar el perfil. Verifica que el email no esté en uso.', 'error')

    return render_template('edit_profile.html', user=user, form=form)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = g.user
    if user is None:
        flash('Debes iniciar sesión para ver tu perfil', 'error')
        return redirect(url_for('login'))

    form = ProfileForm()
    reviews = review_controller.get_user_reviews_with_movies(user['id'])
    review_count = review_controller.get_user_review_count(user['id'])

    if form.validate_on_submit() and form.profile_pic.data:
        file = form.profile_pic.data

        # --- Validaciones anti-“chistoso” ---
        filename_raw = file.filename or ''
        ext = (filename_raw.rsplit('.', 1)[-1] if '.' in filename_raw else '').lower()
        allowed_exts = {'jpg', 'jpeg', 'png'}
        if ext not in allowed_exts:
            flash('Formato no permitido. Solo imágenes JPG/PNG.', 'error')
            return redirect(url_for('profile'))

        if not (file.mimetype or '').startswith('image/'):
            flash('El archivo no es una imagen válida.', 'error')
            return redirect(url_for('profile'))

        # --- Borra la foto anterior (opcional) ---
        old_ref = (user.get('profile_pic') or '').replace('\\', '/')
        # Si usamos Supabase, old_ref será una URL pública; si es local, es ruta relativa 'uploads/profile_pics/...'
        # Intentamos limpiar según el backend
        try:
            if storage_enabled() and old_ref and old_ref.startswith(storage_public_url('')):
                # extrae ruta relativa dentro del bucket
                base = storage_public_url('')
                rel = old_ref[len(base):].lstrip('/')
                storage_delete(rel)
            elif old_ref:
                static_dir = os.path.join(app.root_path, 'static')
                upload_dir = os.path.abspath(os.path.join(static_dir, 'uploads', 'profile_pics'))
                candidate = os.path.abspath(os.path.join(static_dir, old_ref))
                if candidate.startswith(upload_dir) and os.path.isfile(candidate):
                    os.remove(candidate)
        except Exception:
            pass

        # --- Genera nombre único ---
        unique_name = f"user_{session['user_id']}_{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"

        # Subir a Supabase Storage si está configurado; si no, a disco local
        if storage_enabled():
            # RUTA dentro del bucket: profile_pics/<unique>
            object_path = f"profile_pics/{secure_filename(unique_name)}"
            # Leer bytes del file stream
            data = file.read()
            # Inferir content-type
            content_type = file.mimetype or 'image/jpeg'
            url = storage_upload(object_path, data, content_type)
            relative_path = url  # guardamos URL pública directa
        else:
            upload_folder = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'profile_pics')
            os.makedirs(upload_folder, exist_ok=True)
            abs_path = os.path.join(upload_folder, secure_filename(unique_name))
            file.save(abs_path)
            relative_path = str(PurePosixPath('uploads', 'profile_pics', unique_name))

        # Actualiza en BD
        auth_controller.update_profile_pic(session['user_id'], relative_path)

        # 💥 invalida caché del usuario para que no vuelva el perfil viejo
        cache.delete_memoized(load_user_profile_cached, session['user_id'])

    # 🧠 actualiza el user actual en memoria para esta misma request
        try:
            if isinstance(g.user, dict):
                g.user['profile_pic'] = relative_path
        except Exception:
            pass

        flash('Foto de perfil actualizada con éxito', 'success')
        return redirect(url_for('profile', _=int(time.time())))

    return render_template('profile.html', user=user, reviews=reviews, form=form, review_count=review_count)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        nickname = data.get('nickname')
        email = data.get('email')
        password = data.get('password')

        error = validate_registration(nickname, email, password)
        if error:
            return handle_registration_error(error, request.is_json)

        auth_controller.register(nickname, email, password)

        if request.is_json:
            return jsonify({'success': True, 'message': 'Registro exitoso. Se ha enviado un código de verificación a tu email.'})
        flash('Registro exitoso. Se ha enviado un código de verificación a tu email.', 'success')
        return redirect(url_for('verify', email=email))

    return render_template('register.html', user=g.user)

def validate_registration(nickname, email, password):
    if not nickname:
        return 'Se requiere un nickname.'
    if not email:
        return 'Se requiere un email.'
    if not password:
        return 'Se requiere una contraseña.'
    # Use unified connection to support Postgres
    if _get_conn().execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
        return f'El email {email} ya está registrado.'
    return None

def handle_registration_error(error, is_json):
    if is_json:
        return jsonify({'success': False, 'message': error})
    flash(error, 'error')
    return redirect(url_for('register'))

@app.route('/verify/<email>', methods=['GET', 'POST'])
def verify(email):
    user = g.user
    if request.method == 'POST':
        code = request.form.get('code')
        if auth_controller.verify_code(email, code):
            flash('Cuenta verificada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        flash('Código de verificación incorrecto.', 'error')

    return render_template('verify.html', email=email, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = g.user
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')

        error, user_data = validate_login(email, password)
        if error:
            return handle_login_error(error, request.is_json)

        session.clear()
        session['user_id'] = user_data['id']
        # invalida caché de perfil para el nuevo usuario logueado
        cache.delete_memoized(load_user_profile_cached, user_data['id'])
        if request.is_json:
            return jsonify({'success': True, 'message': 'Inicio de sesión exitoso'})
        return redirect(url_for('index'))

    return render_template('login.html', user=user)

def validate_login(email, password):
    conn = _get_conn()
    user_data = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if user_data is None:
        return 'Email incorrecto.', None
    pwd_hash = user_data['password'] if not isinstance(user_data, (tuple, list)) else user_data[3]
    if not check_password_hash(pwd_hash, password):
        return 'Contraseña incorrecta.', None
    is_verified = user_data['is_verified'] if not isinstance(user_data, (tuple, list)) else bool(user_data[5])
    if not is_verified:
        return 'Por favor verifica tu email antes de iniciar sesión.', None
    # Normalize return to dict
    if isinstance(user_data, (tuple, list)):
        # Minimal fields used later
        return None, {'id': user_data[0], 'email': email}
    return None, user_data

def handle_login_error(error, is_json):
    if is_json:
        return jsonify({'success': False, 'message': error})
    flash(error, 'error')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    uid = session.pop('user_id', None)
    if uid:
        cache.delete_memoized(load_user_profile_cached, uid)
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('index'))

# Player: no se cachea porque depende de DB y comentarios
@app.route('/movie/player/<string:movie_id>')
def movie_player(movie_id):
    user = g.user
    movie = movie_controller.get_movie_details(movie_id)
    if movie is None:
        return "Película no encontrada", 404

    reviews = review_controller.get_movie_reviews(movie_id)
    return render_template('movie_player.html', movie=movie, reviews=reviews, user=user)

@app.route('/movie/<string:movie_id>/review', methods=['POST'])
def add_review(movie_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para dejar un comentario.', 'error')
        return redirect(url_for('login'))

    content = request.form['content']
    rating = request.form['rating']
    review_controller.add_review(session['user_id'], movie_id, content, rating)
    flash('Tu comentario ha sido añadido.', 'success')
    return redirect(url_for('movie_player', movie_id=movie_id))

@app.route('/review/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para editar un comentario.'}), 401

    content = request.form.get('content')
    rating = request.form.get('rating')
    result = review_controller.update_review(review_id, session['user_id'], content, rating)
    return (jsonify(result), 200) if result['success'] else (jsonify(result), 400)

@app.route('/review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para eliminar un comentario.'}), 401

    result = review_controller.delete_review(review_id, session['user_id'])
    return (jsonify(result), 200) if result['success'] else (jsonify(result), 400)

@app.route('/ver_peliculas', methods=['GET'])
def ver_peliculas():
    user = g.user
    # Esta lista puede venir de DB; si quisieras cachear, hazlo dentro del controller con una ventana corta
    available_movies = movie_controller.get_available_movies()
    return render_template('ver_peliculas.html', movies=available_movies, user=user)

@app.route('/search', methods=['GET'])
def search():
    user = g.user
    query = request.args.get('q', '')
    if query:
        # Para AJAX en tiempo real (no cacheamos porque cambia mucho)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            movies = movie_controller.search_movies_realtime(query)
            return jsonify(movies)
        else:
            movies = movie_controller.search_movies(query)
            return render_template('search_results.html', movies=movies.get('Search', []), query=query, user=user)

    recommendations = movie_controller.get_random_recommendations()
    return render_template('search.html', user=user, recommendations=recommendations)

@app.route('/movie/<string:movie_id>')
def movie_detail(movie_id):
    user = g.user
    movie = movie_controller.get_movie_details(movie_id)
    if movie is None:
        flash('Película no encontrada', 'error')
        return redirect(url_for('index'))
    return render_template('movie_detail.html', movie=movie, user=user)

@app.route('/request-movie', methods=['GET', 'POST'])
def request_movie():
    user = g.user
    movie_title = request.args.get('title', '').strip()
    movie_year = request.args.get('year', '')

    if request.method == 'POST':
        if user is None:
            flash('Debes iniciar sesión para enviar una solicitud de película.', 'error')
            return redirect(url_for('login'))

        user_email = (request.form.get('user_email') or '').strip()
        movie_title = (request.form.get('movie_title') or '').strip()
        movie_year = (request.form.get('movie_year') or '').strip()
        additional_info = request.form.get('additional_info', '')

        if not movie_title:
            flash('El título de la película es obligatorio.', 'error')
            return redirect(url_for('request_movie', title=movie_title, year=movie_year))

        if not user_email:
            flash('El correo electrónico es obligatorio.', 'error')
            return redirect(url_for('request_movie', title=movie_title, year=movie_year))

        # Try to enrich email with OMDb details by title/year, but don't fail if API errors
        details = get_movie_details_by_title(movie_title, movie_year or None)
        # If OMDb returns error, just proceed with minimal email content
        try:
            send_movie_request_email('vibescine10@gmail.com', movie_title, user_email, additional_info)
            flash('Tu solicitud de película ha sido enviada.', 'success')
        except Exception as e:
            # Do not 500; inform user and continue
            flash('Solicitud recibida, pero hubo un problema enviando el correo. Intentaremos reenviar más tarde.', 'warning')
        return redirect(url_for('index'))

    user_email = user['email'] if user else ''
    return render_template('request_movie.html', title=movie_title, year=movie_year, user_email=user_email, user=user)

@app.route('/resend-verification-code/<email>', methods=['POST'])
def resend_verification_code(email):
    verification_code = ''.join(random.choices('0123456789', k=6))
    send_verification_email(email, verification_code)
    flash('Se ha reenviado el código de verificación a tu correo.', 'success')
    return redirect(url_for('verify', email=email))

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    user = g.user
    if not user:
        flash('Debes iniciar sesión para obtener recomendaciones personalizadas.', 'warning')
        return redirect(url_for('login'))

    genres = movie_controller.get_all_genres()
    actors = movie_controller.get_top_actors(limit=100)
    directors = movie_controller.get_top_directors(limit=50)

    recommendations = []
    if request.method == 'POST':
        genre = request.form.get('genre')
        actor = request.form.get('actor')
        director = request.form.get('director')

        recommendations = movie_controller.get_recommendations(
            user_id=user['id'],
            genre=genre,
            actor=actor,
            director=director
        )

        if not recommendations:
            flash('No se encontraron recomendaciones basadas en tus preferencias. Intenta con diferentes opciones.', 'info')

    return render_template('recommendations.html', user=user, recommendations=recommendations,
                           genres=genres, actors=actors, directors=directors)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', user=getattr(g, 'user', None)), 404

@app.errorhandler(500)
def internal_server_error(e):
    # g.user puede no estar presente si el error ocurre muy temprano
    return render_template('500.html', user=getattr(g, 'user', None)), 500

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.permanent_session_lifetime = timedelta(days=30)
    # Estáticos con cache agresivo en dev
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600
    app.run(debug=True)
