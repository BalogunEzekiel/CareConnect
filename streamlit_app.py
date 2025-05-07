
import streamlit as st
import sqlite3
import pandas as pd

st.title("🏥 Hospital Appointment & Patient Analysis")

# Connect to DB
conn = sqlite3.connect("data/hospital.db")
cursor = conn.cursor()

st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to", ["Patients", "Doctors", "Appointments", "Reports"])

if section == "Patients":
    st.subheader("Registered Patients")
    df = pd.read_sql_query("SELECT * FROM patients", conn)
    st.dataframe(df)

elif section == "Doctors":
    st.subheader("Doctors on Staff")
    df = pd.read_sql_query("SELECT * FROM doctors", conn)
    st.dataframe(df)

elif section == "Appointments":
    st.subheader("Appointments Record")
    df = pd.read_sql_query("""
        SELECT a.appointment_id, p.name AS patient, d.name AS doctor, a.appointment_date, a.status, a.diagnosis
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        JOIN doctors d ON a.doctor_id = d.doctor_id
    """, conn)
    st.dataframe(df)

elif section == "Reports":
    st.subheader("Quick Reports")
    count_patients = pd.read_sql_query("SELECT COUNT(*) AS total_patients FROM patients", conn)
    count_doctors = pd.read_sql_query("SELECT COUNT(*) AS total_doctors FROM doctors", conn)
    count_appointments = pd.read_sql_query("SELECT COUNT(*) AS total_appointments FROM appointments", conn)
    st.metric("Total Patients", count_patients.iloc[0, 0])
    st.metric("Total Doctors", count_doctors.iloc[0, 0])
    st.metric("Total Appointments", count_appointments.iloc[0, 0])

conn.close()
