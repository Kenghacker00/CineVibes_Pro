import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
from utils.imdb import get_movie_details_by_title

def send_verification_email(to_email, verification_code):
    subject = "Código de Verificación - CineVibes"
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            .header {{ background-color: #ff0000; color: white; padding: 10px; text-align: center; }}
            .content {{ padding: 20px; background-color: white; }}
            .code {{ font-size: 24px; font-weight: bold; color: #ff0000; text-align: center; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>CineVibes - Verificación de Cuenta</h1>
            </div>
            <div class="content">
                <p>Hola,</p>
                <p>Gracias por registrarte en CineVibes. Para completar tu registro, por favor utiliza el siguiente código de verificación:</p>
                <div class="code">{verification_code}</div>
                <p>Si no has solicitado este código, por favor ignora este correo.</p>
            </div>
            <div class="footer">
                <p>&copy; 2023 CineVibes. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """

    send_email(to_email, subject, html_content)

def send_movie_request_email(to_email, movie_title, user_email, additional_info=None):
    subject = f"Nueva Solicitud de Película: {movie_title}"

    # Obtener detalles de la película
    try:
        movie_details = get_movie_details_by_title(movie_title)
    except Exception:
        movie_details = {"Poster": "", "Year": "", "Director": "", "Actors": ""}

    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            .header {{ background-color: #ff0000; color: white; padding: 10px; text-align: center; }}
            .content {{ padding: 20px; background-color: white; }}
            .movie-title {{ font-size: 20px; font-weight: bold; color: #ff0000; margin: 10px 0; }}
            .info {{ margin-bottom: 10px; }}
            .poster {{ max-width: 200px; margin: 10px auto; display: block; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Nueva Solicitud de Película</h1>
            </div>
            <div class="content">
                <p>Se ha recibido una nueva solicitud de película:</p>
                <div class="movie-title">{movie_title}</div>
                <img src="{movie_details.get('Poster','')}" alt="Poster de {movie_title}" class="poster">
                <div class="info"><strong>Usuario:</strong> {user_email}</div>
                <div class="info"><strong>Año:</strong> {movie_details.get('Year','')}</div>
                <div class="info"><strong>Director:</strong> {movie_details.get('Director','')}</div>
                <div class="info"><strong>Actores:</strong> {movie_details.get('Actors','')}</div>
                <div class="info"><strong>Información adicional:</strong> {additional_info or 'No proporcionada'}</div>
                <p>Por favor, revisa esta solicitud y toma las acciones necesarias.</p>
            </div>
            <div class="footer">
                <p>&copy; 2023 CineVibes. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        send_email(to_email, subject, html_content)
    except Exception:
        # swallow to let caller handle fallback
        raise

    # Enviar correo al usuario
    user_subject = f"Confirmación de solicitud de película: {movie_title}"
    user_html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            .header {{ background-color: #ff0000; color: white; padding: 10px; text-align: center; }}
            .content {{ padding: 20px; background-color: white; }}
            .movie-title {{ font-size: 20px; font-weight: bold; color: #ff0000; margin: 10px 0; }}
            .info {{ margin-bottom: 10px; }}
            .poster {{ max-width: 200px; margin: 10px auto; display: block; }}
            .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #888; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Confirmación de Solicitud de Película</h1>
            </div>
            <div class="content">
                <p>Hemos recibido tu solicitud para la siguiente película:</p>
                <div class="movie-title">{movie_title}</div>
                <img src="{movie_details.get('Poster','')}" alt="Poster de {movie_title}" class="poster">
                <div class="info"><strong>Año:</strong> {movie_details.get('Year','')}</div>
                <div class="info"><strong>Director:</strong> {movie_details.get('Director','')}</div>
                <div class="info"><strong>Actores:</strong> {movie_details.get('Actors','')}</div>
                <p>Gracias por tu solicitud. La tomaremos en cuenta para añadirla pronto a nuestra colección.</p>
            </div>
            <div class="footer">
                <p>&copy; 2023 CineVibes. Todos los derechos reservados.</p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        send_email(user_email, user_subject, user_html_content)
    except Exception:
        # non-fatal for the flow
        pass

def send_email(to_email, subject, html_content):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_SENDER
    msg['To'] = to_email

    msg.attach(MIMEText(html_content, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
        server.starttls()
        server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
        server.send_message(msg)

# Nota: get_movie_details se importa desde utils.imdb
