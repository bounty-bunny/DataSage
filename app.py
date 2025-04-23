import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sweetviz as sv
import sqlite3
from db import create_connection, initialize_database, check_user, add_user

DB_PATH = 'your_database.db'

# Initialize DB connection
conn = create_connection(DB_PATH)
if conn:
    initialize_database(conn)

# Initialize session state
if 'form_mode' not in st.session_state:
    st.session_state.form_mode = 'login'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'df' not in st.session_state:
    st.session_state.df = None

# Sign Up
def sign_up():
    st.markdown("<h2 style='text-align: center;'>Sign Up</h2>", unsafe_allow_html=True)
    username = st.text_input("Create Username", key="signup_username")
    password = st.text_input("Create Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

    if password != confirm_password:
        st.error("Passwords do not match.")
    elif st.button("Sign Up", key="signup_button"):
        if check_user(conn, username):
            st.error("Username already exists.")
        else:
            add_user(conn, username, password)
            st.success("Account created successfully. Please log in.")
            st.session_state.form_mode = 'login'
            st.experimental_rerun()

# Login
def login():
    st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", key="login_button"):
        user = check_user(conn, username)
        if user and user[2] == password:
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
        else:
            st.error("Incorrect username or password.")

# Sample Data
def create_sample_data():
    return pd.DataFrame({
        "ID": range(1, 11),
        "Name": ["Alice", "Bob", "Charlie", "David", "Eva", "Frank", "Grace", "Hannah", "Ivy", "Jack"],
        "Age": np.random.randint(20, 60, size=10),
        "Salary": np.random.randint(30000, 120000, size=10),
        "Department": ["HR", "IT", "Finance", "Marketing", "IT", "HR", "Marketing", "Finance", "IT", "HR"]
    })

# EDA Report
def generate_sweetviz_report(df):
    report = sv.analyze(df)
    report.show_html("sweetviz_report.html", open_browser=False)
    with open("sweetviz_report.html", "r", encoding="utf-8") as f:
        html = f.read()
    st.components.v1.html(html, height=1000, scrolling=True)

# Dashboard Visualizations
def show_dashboard(df):
    st.subheader("📊 Data Dashboard")
    selected_metrics = st.multiselect("Select Metrics to Visualize", df.columns.tolist(), default=df.columns.tolist())
    chart_type = st.selectbox("Select Chart Type", ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"])

    if selected_metrics:
        if chart_type == "Bar Chart":
            for col in selected_metrics:
                if df[col].dtype in ['int64', 'float64']:
                    st.plotly_chart(px.bar(df, x=col, title=f"Bar Chart of {col}"))
        elif chart_type == "Line Chart":
            for col in selected_metrics:
                if df[col].dtype in ['int64', 'float64']:
                    st.plotly_chart(px.line(df, y=col, title=f"Line Chart of {col}"))
        elif chart_type == "Pie Chart":
            for col in selected_metrics:
                if df[col].dtype == 'object':
                    st.plotly_chart(px.pie(df, names=col, title=f"Pie Chart of {col}"))
        elif chart_type == "Scatter Plot" and len(selected_metrics) == 2:
            st.plotly_chart(px.scatter(df, x=selected_metrics[0], y=selected_metrics[1],
                                       title=f"Scatter Plot: {selected_metrics[0]} vs {selected_metrics[1]}"))
    else:
        st.warning("Please select at least one metric.")

# Main App
if not st.session_state.authenticated:
    if st.session_state.form_mode == 'login':
        login()
        if st.button("Don't have an account? Sign Up"):
            st.session_state.form_mode = 'signup'
            st.experimental_rerun()
    else:
        sign_up()
        if st.button("Already have an account? Login"):
            st.session_state.form_mode = 'login'
            st.experimental_rerun()
else:
    st.sidebar.header("📂 Upload or Connect")
    option = st.sidebar.radio("Choose Action", ["Upload File", "Connect SQL", "Data Insights", "Dashboard"])

    # Upload File
    if option == "Upload File":
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                st.session_state.df = df
                st.success("Upload successful!")
                st.dataframe(df)
            except Exception as e:
                st.error(f"File load error: {e}")

    # Connect SQL
    elif option == "Connect SQL":
        st.subheader("🔌 Connect SQL")
        db_type = st.selectbox("DB Type", ["SQLite", "PostgreSQL", "MySQL"])

        if db_type == "SQLite":
            sqlite_file = st.file_uploader("Upload SQLite DB", type="db")
            if sqlite_file:
                try:
                    sql_conn = sqlite3.connect(sqlite_file.name)
                    tables = [t[0] for t in sql_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                    table = st.selectbox("Choose Table", tables)
                    if table:
                        df = pd.read_sql_query(f"SELECT * FROM {table}", sql_conn)
                        st.session_state.df = df
                        st.success("Data fetched from SQLite")
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"SQLite error: {e}")
        else:
            st.info(f"{db_type} support is coming soon.")

    # Data Insights
    elif option == "Data Insights":
        st.subheader("📈 Sweetviz EDA Report")
        df = st.session_state.df or create_sample_data()
        cols = st.multiselect("Choose columns for EDA", df.columns)
        selected_df = df[cols] if cols else df
        if st.button("🔍 Generate Report"):
            generate_sweetviz_report(selected_df)

    # Dashboard
    elif option == "Dashboard":
        if st.session_state.df is not None:
            show_dashboard(st.session_state.df)
        else:
            st.warning("Upload or connect to data first.")
