import sys
import os
import secrets
from flask import Flask, session
from flask_session import Session
from server import app, server
from _dash.dash_layout import dash_layout
from authentification.auth_handler import auth_layout, init_firebase
from utility.user_manager import user_manager
import _dash.callbacks  # Registers callbacks

# Initialize Firebase
init_firebase()

# Configure Server Side Session
app.server.config["SESSION_PERMANENT"] = False
app.server.config["SESSION_TYPE"] = "filesystem"
app.server.config["SECRET_KEY"] = secrets.token_hex(32)
Session(app.server)

# Set the layout dynamically based on session
def serve_layout():
    user_id = session.get("user_id")
    print(f"DEBUG: serve_layout called. User ID: {user_id}")
    if user_id:
        return dash_layout()
    return auth_layout()

app.layout = serve_layout

if __name__ == '__main__':
    # Use 0.0.0.0 for easier access if running in container/vm, but 127.0.0.1 is standard for local
    app.run(host="127.0.0.1", port=8050, debug=True)
