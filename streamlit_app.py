import streamlit as st
import sqlite3
import pandas as pd
import bcrypt

# --- Helper Functions ---
def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)

def check_password(input_password, stored_hashed_password):
    return bcrypt.checkpw(input_password.encode(), stored_hashed_password)

def reset_password(username, new_password, conn):
    hashed = hash_password(new_password)
    conn.execute("UPDATE users SET password = ? WHERE username = ?", (hashed, username))
    conn.commit()

# --- Configuration ---
st.set_page_config(page_title="CareConnect - Hospital Dashboard", layout="wide")

# --- Connect to Database ---
@st.cache_resource
def get_connection():
    return sqlite3.connect("data/careconnect.db", check_same_thread=False)

conn = get_connection()

# --- Initialize Database ---
def init_db():
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password BLOB,
        role TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        contact TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        specialty TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER,
        doctor_id INTEGER,
        appointment_date DATE,
        status TEXT,
        diagnosis TEXT,
        FOREIGN KEY(patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(doctor_id)
    )''')
    conn.commit()

init_db()

# --- Session Setup ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- Login/Register Logic ---
def login(username, password):
    cursor = conn.execute("SELECT password, role FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if result and check_password(password, result[0]):
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = result[1]
        st.success("Login successful!")
    else:
        st.error("Invalid username or password")

def register(username, password, role):
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        st.error("Username already exists.")
    else:
        hashed = hash_password(password)
        conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
        conn.commit()
        st.success("Registered successfully! You can now log in.")

# --- Authentication UI ---
if not st.session_state.authenticated:
    tab1, tab2, tab3 = st.tabs(["Login", "Register", "Reset Password"])
    
    with tab1:
        st.title("🔐 Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            login(username, password)

    with tab2:
        st.title("📝 Register")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        role = st.selectbox("Role", ["admin]()
