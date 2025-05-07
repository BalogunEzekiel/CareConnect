import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Hospital Dashboard", layout="wide")
st.title("🏥 Hospital Appointment & Patient Analysis")

# Function to connect to database safely
def connect_db(db_path="data/hospital.db"):
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        st.error(f"Database connection failed: {e}")
        return None

# Load data safely
def load_data(query, conn):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Failed to execute query: {e}")
        return pd.DataFrame()

# Main app logic
conn = connect_db()

if conn:
    st.sidebar.header("Navigation")
    section = st.sidebar.radio("Go to", ["Patients", "Doctors", "Appointments", "Reports"])

    if section == "Patients":
        st.subheader("Registered Patients")
        df = load_data("SELECT * FROM patients", conn)
        st.dataframe(df)

    elif section == "Doctors":
        st.subheader("Doctors on Staff")
        df = load_data("SELECT * FROM doctors", conn)
        st.dataframe(df)

    elif section == "Appointments":
        st.subheader("Appointments Record")
        query = """
            SELECT a.appointment_id, p.name AS patient, d.name AS doctor,
                   a.appointment_date, a.status, a.diagnosis
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors d ON a.doctor_id = d.doctor_id
        """
        df = load_data(query, conn)
        st.dataframe(df)

    elif section == "Reports":
        st.subheader("Quick Reports")
        count_patients = load_data("SELECT COUNT(*) AS total_patients FROM patients", conn)
        count_doctors = load_data("SELECT COUNT(*) AS total_doctors FROM doctors", conn)
        count_appointments = load_data("SELECT COUNT(*) AS total_appointments FROM appointments", conn)

        if not count_patients.empty and not count_doctors.empty and not count_appointments.empty:
            st.metric("Total Patients", count_patients.iloc[0, 0])
            st.metric("Total Doctors", count_doctors.iloc[0, 0])
            st.metric("Total Appointments", count_appointments.iloc[0, 0])
        else:
            st.warning("Unable to load one or more metrics.")

    # Close the connection at the end
    conn.close()
else:
    st.stop()
