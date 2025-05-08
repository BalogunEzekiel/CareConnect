import bcrypt
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --- Helper Functions ---
# Hashing the password with bcrypt
def hash_password(password):
    salt = bcrypt.gensalt()  # Generates a salt
    return bcrypt.hashpw(password.encode(), salt).decode('utf-8')  # Hash the password

# Check if the input password matches the stored hashed password
def check_password(input_password, stored_hashed_password):
    # Ensure stored_hashed_password is bytes if it's a string
    if isinstance(stored_hashed_password, str):
        stored_hashed_password = stored_hashed_password.encode('utf-8')
    return bcrypt.checkpw(input_password.encode(), stored_hashed_password)

# Reset the password in the database
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
        password TEXT, 
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
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "🔄 Reset Password"])

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
        role = st.selectbox("Role", ["admin", "doctor", "receptionist"])
        if st.button("Register"):
            register(new_user, new_pass, role)

    with tab3:
        st.title("🔄 Reset Password")
        user_reset = st.text_input("Enter your Username", key="reset_user")
        new_pass = st.text_input("New Password", type="password", key="reset_pass")
        if st.button("Reset Password"):
            cursor = conn.execute("SELECT * FROM users WHERE username = ?", (user_reset,))
            if cursor.fetchone():
                reset_password(user_reset, new_pass, conn)
                st.success("Password reset successfully!")
            else:
                st.error("Username does not exist.")

# --- Main Dashboard ---
else:
    st.sidebar.success(f"Logged in as {st.session_state.username} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.role = None
        st.rerun()

    st.title("🏥 CareConnect Hospital Dashboard")
    tab1, tab2, tab3 = st.tabs(["Patients", "Doctors", "Appointments"])

    # --- Patients Tab ---
    with tab1:
        st.header("👩‍⚕️ Patient Records")
        if st.button("Show All Patients"):
            df = pd.read_sql_query("SELECT * FROM patients", conn)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "patients.csv", "text/csv")

        if st.session_state.role in ["admin", "receptionist"]:
            with st.form("add_patient_form"):
                st.subheader("Add New Patient")
                name = st.text_input("Name")
                age = st.number_input("Age", min_value=0, max_value=120)
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                contact = st.text_input("Contact")
                submitted = st.form_submit_button("Add Patient")
                if submitted:
                    conn.execute("INSERT INTO patients (name, age, gender, contact) VALUES (?, ?, ?, ?)",
                                 (name, age, gender, contact))
                    conn.commit()
                    st.success("Patient added successfully!")

    # --- Doctors Tab ---
    with tab2:
        st.header("👩‍⚕️ Doctor Records")
        if st.button("Show All Doctors"):
            df = pd.read_sql_query("SELECT * FROM doctors", conn)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "doctors.csv", "text/csv")

        if st.session_state.role in ["admin"]:
            with st.form("add_doctor_form"):
                st.subheader("Add New Doctor")
                name = st.text_input("Doctor Name")
                specialty = st.text_input("Specialty")
                submitted = st.form_submit_button("Add Doctor")
                if submitted:
                    conn.execute("INSERT INTO doctors (name, specialty) VALUES (?, ?)",
                                 (name, specialty))
                    conn.commit()
                    st.success("Doctor added successfully!")

    # --- Appointments Tab ---
    with tab3:
        st.header("🗓️ Appointments")
        if st.button("Show All Appointments"):
            query = '''
            SELECT a.appointment_id, p.name AS patient, d.name AS doctor, 
                   a.appointment_date, a.status, a.diagnosis
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
            '''
            df = pd.read_sql_query(query, conn)
            st.dataframe(df)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "appointments.csv", "text/csv")

        if st.session_state.role in ["admin", "receptionist"]:
            with st.form("add_appointment_form"):
                st.subheader("Book Appointment")
                patients = conn.execute("SELECT patient_id, name FROM patients").fetchall()
                doctors = conn.execute("SELECT doctor_id, name FROM doctors").fetchall()
                patient_choice = st.selectbox("Select Patient", patients, format_func=lambda x: x[1])
                doctor_choice = st.selectbox("Select Doctor", doctors, format_func=lambda x: x[1])
                appointment_date = st.date_input("Appointment Date", value=date.today())
                status = st.selectbox("Status", ["Scheduled", "Completed", "Cancelled"])
                diagnosis = st.text_input("Diagnosis")
                submitted = st.form_submit_button("Book Appointment")
                if submitted:
                    conn.execute("""INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, diagnosis)
                                    VALUES (?, ?, ?, ?, ?)""",
                                    (patient_choice[0], doctor_choice[0], appointment_date, status, diagnosis))
                    conn.commit()
                    st.success("Appointment booked successfully!")
