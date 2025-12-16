import streamlit as st
import pandas as pd
import numpy as np
import firebase_admin
from firebase_admin import auth, credentials, firestore
cert_path = "../authentification/backtestsbs-firebase-adminsdk-fbsvc-f5c13c27d3.json"
ticker = "TTE"
# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(cert_path)
    firebase_admin.initialize_app(cred)
db = firestore.client()

def calculate_sma(data, window):    
    return data['Close'].rolling(window=window).mean()

def calculate_rsi(data, window=14):
    delta = data['Close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def login_user(email, password):
    try:
        user = auth.get_user_by_email(email) 
        st.session_state['user'] = user.uid
        return True
    except:
        return False

def register_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        st.session_state['user'] = user.uid
        return True
    except:
        return False

# Streamlit UI
st.title("Trading Strategy Backtester")

# Authentication
if "user" not in st.session_state:
    auth_mode = st.radio("Login / Register", ["Login", "Register"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Submit"):
        if auth_mode == "Login":
            if login_user(email, password):
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Login failed.")
        else:
            if register_user(email, password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Registration failed.")
else:
    st.success("Logged in as: " + st.session_state['user'])
    
    # File upload
    uploaded_file = st.file_uploader("Upload CSV (with 'Date' & 'Close' columns)", type=["csv"])
    
    if uploaded_file:
        data = pd.read_csv(uploaded_file, parse_dates=['Date'])
        data = data.sort_values('Date')
        st.write("### Raw Data:")
        st.dataframe(data.head())
        
        strategy = st.selectbox("Select Strategy", ["SMA", "RSI"])
        window = st.slider("Select Window Size", 5, 50, 14)
        
        if strategy == "SMA":
            data['SMA'] = calculate_sma(data, window)
        elif strategy == "RSI":
            data['RSI'] = calculate_rsi(data, window)
        
        st.write("### Backtest Results:")
        if strategy == "SMA":
            st.line_chart(data[['Close', 'SMA']]) 
        else:
            st.line_chart(data['Close'])
            st.line_chart(data['RSI'])
# Charting trading view
# ---------------------
#         st.components.v1.html(f"""
# <iframe src="https://s.tradingview.com/embed-widget/advanced-chart/?symbol={ticker}&theme=dark" 
#         width="100%" height="500px" frameborder="0" allowfullscreen></iframe>
# """, height=500)
        st.dataframe(data.tail())
