import dash
import dash_bootstrap_components as dbc
import os
import ssl
import time
from curl_cffi import requests

# Fix for Render environment
if 'RENDER' in os.environ:
    print("🖥️ Environnement Render détecté")
    ssl._create_default_https_context = ssl._create_unverified_context
    import socket
    socket.setdefaulttimeout(60)

# Session setup
http_session = requests.Session(impersonate="chrome")

# Cache buster
cache_buster = str(int(time.time()))

# App initialization
app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],
    external_stylesheets=[dbc.themes.DARKLY, '/assets/premium.css'],
    suppress_callback_exceptions=True
)

server = app.server
server.secret_key = os.environ.get("SECRET_KEY", "super-secret-key")
