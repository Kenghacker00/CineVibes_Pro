CineVibes Favicon Pack
Generated: 1754856540

Place files in your Flask /static directory. Suggested <head> tags:

<link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='favicon.ico') }}">
<link rel="icon" type="image/png" sizes="32x32" href="{{ url_for('static', filename='favicon-32.png') }}">
<link rel="icon" type="image/png" sizes="16x16" href="{{ url_for('static', filename='favicon-16.png') }}">
<link rel="apple-touch-icon" sizes="180x180" href="{{ url_for('static', filename='apple-touch-icon.png') }}">
<link rel="manifest" href="{{ url_for('static', filename='site.webmanifest') }}">
<meta name="theme-color" content="#111111">
