import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import uuid
import time


# --- Helper Functions ---
def hash_password(password):
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(input_password, stored_hashed_password):
    """Check if the input password matches the stored hashed password."""
    return hash_password(input_password) == stored_hashed_password

def create_reset_token():
    """Generate a unique token for password reset."""
    return str(uuid.uuid4())

def reset_password(username, new_password, conn):
    """Reset password for a user."""
    hashed_password = hash_password(new_password)
    query = "UPDATE users SET password = ? WHERE username = ?"
    conn.execute(query, (hashed_password, username))
    conn.commit()

# --- Configuration ---
st.set_page_config(page_title="CareConnect - Hospital Dashboard", layout="wide")

# --- Connect to Database ---
@st.cache_resource
def get_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect("data/careconnect.db", check_same_thread=False)

conn = get_connection()

# --- Initialize Database (if not exist) ---
def init_db():
    """Initialize the database tables if they do not exist."""
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS patients (
        patient_id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        gender TEXT,
        contact TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS doctors (
        doctor_id INTEGER PRIMARY KEY,
        name TEXT,
        specialty TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS appointments (
        appointment_id INTEGER PRIMARY KEY,
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

# --- User Registration ---
def register_user(username, password, role, conn):
    """Register a new user in the database."""
    hashed_password = hash_password(password)
    query = "INSERT INTO users (username, password, role) VALUES (?, ?, ?)"
    conn.execute(query, (username, hashed_password, role))
    conn.commit()

# --- User Login / Session ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- Login Screen ---
if not st.session_state.authenticated:
    st.title("🔒 CareConnect Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    login_button = st.button("Login")
    if login_button:
        query = "SELECT * FROM users WHERE username = ?"
        user = conn.execute(query, (username,)).fetchone()
        
        if user and check_password(password, user[1]):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.role = user[2]  # Role is stored in user[2]
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials. Please try again.")

    if st.checkbox("Don't have an account? Register here"):
        with st.form("registration_form"):
            reg_username = st.text_input("Create Username")
            reg_password = st.text_input("Create Password", type="password")
            reg_role = st.selectbox("Select Role", ["Admin", "Doctor", "Patient"])
            submit_button = st.form_submit_button("Register")

            if submit_button:
                try:
                    register_user(reg_username, reg_password, reg_role, conn)
                    st.success("Registration successful!")
                    st.session_state.authenticated = True
                    st.session_state.username = reg_username
                    st.session_state.role = reg_role
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username already exists. Please choose a different one.")
    st.stop()

# --- Logout Button ---
st.sidebar.markdown(f"👋 Welcome, `{st.session_state.username}`")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

# --- Role-Based Access Control ---
def check_access(required_role):
    """Check if the current user has the required role."""
    if st.session_state.role != required_role and st.session_state.role != "Admin":
        st.error("You do not have permission to access this section.")
        st.stop()

# --- Sections ---
section = st.sidebar.radio("📂 Go to", ["Patients", "Doctors", "Appointments", "Reports", "Password Reset"])

if section == "Patients":
    check_access("Doctor")
    st.title("🧍 Registered Patients")
    df = pd.read_sql_query("SELECT * FROM patients", conn)
    st.dataframe(df, use_container_width=True)

elif section == "Doctors":
    check_access("Admin")
    st.title("🩺 Doctors on Staff")
    df = pd.read_sql_query("SELECT * FROM doctors", conn)
    st.dataframe(df, use_container_width=True)

elif section == "Appointments":
    check_access("Doctor")
    st.title("📅 Appointments Record")
    df = pd.read_sql_query("SELECT * FROM appointments", conn)
    st.dataframe(df, use_container_width=True)

elif section == "Reports":
    check_access("Admin")
    st.title("📊 Quick Summary Reports")
    total_patients = pd.read_sql("SELECT COUNT(*) FROM patients", conn).iloc[0, 0]
    total_doctors = pd.read_sql("SELECT COUNT(*) FROM doctors", conn).iloc[0, 0]
    total_appointments = pd.read_sql("SELECT COUNT(*) FROM appointments", conn).iloc[0, 0]

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total Patients", total_patients)
    col2.metric("🩺 Total Doctors", total_doctors)
    col3.metric("📅 Total Appointments", total_appointments)

elif section == "Password Reset":
    st.title("🔄 Reset Your Password")
    username_reset = st.text_input("Enter your username for password reset")
    new_password = st.text_input("New Password", type="password")
    if st.button("Reset Password"):
        reset_password(username_reset, new_password, conn)
        st.success("Password reset successful!")
