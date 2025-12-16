
import os
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import requests
from flask import session
import firebase_admin
from firebase_admin import credentials, auth
import sys

# Load environment variables if needed
# Load environment variables
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
env_path = os.path.join(root_dir, '.env')
load_dotenv(env_path)

from utility.user_manager import user_manager

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")

# Validation warning on startup
if not FIREBASE_API_KEY:
    print("⚠️ WARNING: FIREBASE_API_KEY not found in environment variables or .env file.")

def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Construct path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(current_dir, "the_key.json")
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized")
        else:
            print(f"⚠️ Firebase key not found at {cred_path}")

def auth_layout():
    """
    Layout for the authentication page.
    Reconstructed based on standard Dash login forms since original definition was referenced but not found.
    """
    # Removed inline dictionary styles to use CSS classes from premium.css

    return html.Div([
        # Background Animation (From Site)
        html.Div([
            html.Div(className="blob blob-1"),
            html.Div(className="blob blob-2")
        ], className="background-blobs"),

        dbc.Container([
            dcc.Location(id="url", refresh=True), # Fix for callback error
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H2("Gradient System", className="text-center mb-4", style={"color": "white", "fontWeight": "bold"}), # Keep specific white for header if needed, or use text-primary from dark theme
                            html.P("Login / Register", className="text-center mb-4 text-muted"),
                            
                            dbc.Label("Email", className="text-light"),
                            dbc.Input(id="email", placeholder="Enter your email", type="email", className="mb-3 form-control"),
                            
                            dbc.Label("Password", className="text-light"),
                            dbc.Input(id="password", placeholder="Enter password", type="password", className="mb-3 form-control"),
                            
                            dbc.RadioItems(
                                id="auth-mode",
                                options=[
                                    {"label": "Login", "value": "login"},
                                    {"label": "Register", "value": "register"},
                                ],
                                value="login",
                                inline=True,
                                className="mb-3 text-light",
                                style={"color": "white"}
                            ),
                            
                            dbc.Button("Submit", id="submit-btn", color="primary", className="w-100 btn-success", style={"fontWeight": "bold"}), # btn-success has the gradient
                            
                            dbc.Alert(id="feedback", is_open=False, dismissable=True, color="danger", className="mt-3 text-center"),
                            
                            html.Div([
                                html.A("Forgot Password?", id="forgot-password-link", href="#", className="text-info small")
                            ], className="mt-3 text-center"),
                            
                            # Forgot password section
                            html.Div([
                                dbc.Input(id="reset-email", placeholder="Enter email to reset", type="email", className="mb-2 mt-3 form-control"),
                                dbc.Button("Send Reset Email", id="send-reset-email", color="secondary", size="sm", className="w-100"),
                                html.Div(id="reset-feedback", className="mt-2 small text-light")
                            ], id="forgot-password-container", style={"display": "none"})
                        ])
                    ], className="card shadow-lg", style={"maxWidth": "400px", "margin": "auto", "marginTop": "100px"})
                ])
            ])
        ], fluid=True, style={"minHeight": "100vh", "backgroundColor": "transparent"}) # Make transparent for blobs
    ])

def register_auth_callbacks(app):
    """Register all authentication related callbacks"""
    
    # Callback to handle login/register
    @app.callback(
        Output("feedback", "children"),
        Output("feedback", "is_open"),
        Output("url", "pathname"),
        Input("submit-btn", "n_clicks"),
        State("email", "value"),
        State("password", "value"),
        State("auth-mode", "value"),
        prevent_initial_call=True
    )
    def handle_auth(n_clicks, email, password, mode):
        if not n_clicks or not email or not password:
            return "Email and password are required.", True, dash.no_update

        if not FIREBASE_API_KEY:
             return "❌ Configuration Error: FIREBASE_API_KEY is missing. Please check your .env file.", True, dash.no_update

        endpoint = {
            "login": f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
            "register": f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}",
        }

        # Create session if needed
        http_session = requests.Session()

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            response = http_session.post(endpoint[mode], json=payload)
            result = response.json()

            if response.status_code != 200:
                error_message = result.get("error", {}).get("message", "Authentication failed.")
                return f"{mode.capitalize()} failed: {error_message}", True, dash.no_update

            id_token = result["idToken"]
            email = result["email"]
            
            # Verify the token with Firebase Admin
            try:
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token["uid"]
                
                # Create user profile if it doesn't exist (Default: Individual)
                # In a real app, you might ask for role during registration
                if mode == "register":
                    user_manager.create_user_if_not_exists(uid, email, role='individual')
                
                # Load profile and permissions into session
                profile = user_manager.get_user_profile(uid)
                
                session["user_id"] = uid
                session["email"] = email
                session["role"] = profile.get("role", "individual") if profile else "individual"
                
                return f"{mode.capitalize()} successful!", True, "/app"
                
            except Exception as e:
                return f"Token verification failed: {e}", True, dash.no_update
            
        except Exception as e:
            print(f"Auth error: {e}")
            return f"{mode.capitalize()} failed: {e}", True, dash.no_update

    # Callback for forgot password toggle
    @app.callback(
        Output("forgot-password-container", "style"),
        Input("forgot-password-link", "n_clicks"),
        prevent_initial_call=False
    )
    def toggle_forgot_password(n_clicks):
        if not n_clicks:
            return {"display": "none"}
        else:
            return {"display": "block"}

    # Callback for sending reset email
    @app.callback(
        Output("reset-feedback", "children"),
        Input("send-reset-email", "n_clicks"),
        State("reset-email", "value"),
        prevent_initial_call=True
    )
    def send_reset_email(n_clicks, email):
        if not email:
            return "❗ Please enter a valid email."

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return "✅ Password reset email sent! Please check your inbox or spam folder"
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                return f"❌ Error: {error_msg}"
        except Exception as e:
            return f"⚠️ Request failed: {str(e)}"
