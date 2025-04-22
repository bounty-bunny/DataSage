import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sweetviz as sv
import sqlite3
import sqlalchemy
import os

# --- Database Setup ---
def init_user_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def user_exists(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()

def validate_user(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# --- Initialize user DB ---
init_user_db()

# --- Session State ---
if 'form_mode' not in st.session_state:
    st.session_state.form_mode = 'login'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'df' not in st.session_state:
    st.session_state.df = None

# --- Auth Forms ---
def sign_up():
    st.markdown("<h2 style='text-align: center;'>Sign Up</h2>", unsafe_allow_html=True)
    username = st.text_input("Create Username")
    password = st.text_input("Create Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("Passwords do not match.")
        elif user_exists(username):
            st.error("Username already exists.")
        else:
            create_user(username, password)
            st.success("Account created! Please log in.")
            st.session_state.form_mode = 'login'
            st.experimental_rerun()

def login():
    st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if validate_user(username, password):
            st.session_state.authenticated = True
            st.success("Login successful!")
        else:
            st.error("Invalid credentials.")

# --- Auth Flow ---
if not st.session_state.authenticated:
    if st.session_state.form_mode == 'login':
        login()
        if st.button("Don't have an account? Sign Up"):
            st.session_state.form_mode = 'signup'
            st.experimental_rerun()
    elif st.session_state.form_mode == 'signup':
        sign_up()
        if st.button("Already have an account? Login"):
            st.session_state.form_mode = 'login'
            st.experimental_rerun()
else:
    # --- Data Interface ---
    st.sidebar.header("📂 Upload or Connect")
    menu_option = st.sidebar.radio("Choose Data Source", ["Upload File", "Connect SQL", "Data Insights", "Dashboard"])

    def create_sample_data():
        return pd.DataFrame({
            "ID": range(1, 11),
            "Name": ["Alice", "Bob", "Charlie", "David", "Eva", "Frank", "Grace", "Hannah", "Ivy", "Jack"],
            "Age": np.random.randint(20, 60, size=10),
            "Salary": np.random.randint(30000, 120000, size=10),
            "Department": ["HR", "IT", "Finance", "Marketing", "IT", "HR", "Marketing", "Finance", "IT", "HR"]
        })

    if menu_option == "Upload File":
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.session_state.df = df
                st.success("File uploaded!")
                st.dataframe(df)
            except Exception as e:
                st.error(f"File Error: {e}")

    elif menu_option == "Connect SQL":
        st.subheader("🔌 Connect to SQL Database")
        db_type = st.selectbox("Database Type", ["SQLite", "PostgreSQL", "MySQL"])

        if db_type == "SQLite":
            sqlite_file = st.file_uploader("Upload SQLite DB", type=["db", "sqlite"])
            if sqlite_file:
                try:
                    with open("temp_uploaded.db", "wb") as f:
                        f.write(sqlite_file.read())
                    conn = sqlite3.connect("temp_uploaded.db")
                    cursor = conn.cursor()
                    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")]
                    table = st.selectbox("Select Table", tables)
                    if table:
                        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                        st.session_state.df = df
                        st.success("Data loaded.")
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"SQLite Error: {e}")
        else:
            st.warning("Only SQLite is supported in this demo.")

    elif menu_option == "Data Insights":
        st.subheader("📈 Sweetviz EDA Report")
        df = st.session_state.df or create_sample_data()
        st.session_state.df = df
        columns_to_analyze = st.multiselect("Select columns for EDA", df.columns)
        filtered_df = df[columns_to_analyze] if columns_to_analyze else df

        if st.button("🔍 Generate Report"):
            report = sv.analyze(filtered_df)
            report.show_html("report.html", open_browser=False)
            with open("report.html", "r", encoding="utf-8") as f:
                html_report = f.read()
            st.components.v1.html(html_report, height=1000, scrolling=True)

    elif menu_option == "Dashboard":
        st.subheader("📊 Visual Dashboard")
        df = st.session_state.df or create_sample_data()
        st.session_state.df = df

        selected_metrics = st.multiselect("Select Metrics", df.columns.tolist())
        chart_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"])

        if selected_metrics:
            if chart_type == "Bar Chart":
                for metric in selected_metrics:
                    if pd.api.types.is_numeric_dtype(df[metric]):
                        st.plotly_chart(px.bar(df, x=metric, title=f"{metric} Distribution"))

            elif chart_type == "Line Chart":
                for metric in selected_metrics:
                    if pd.api.types.is_numeric_dtype(df[metric]):
                        st.plotly_chart(px.line(df, x=df.index, y=metric, title=f"{metric} Trend"))

            elif chart_type == "Pie Chart":
                for metric in selected_metrics:
                    st.plotly_chart(px.pie(df, names=metric, title=f"{metric} Breakdown"))

            elif chart_type == "Scatter Plot" and len(selected_metrics) > 1:
                x = st.selectbox("X-axis", selected_metrics)
                y = st.selectbox("Y-axis", selected_metrics)
                st.plotly_chart(px.scatter(df, x=x, y=y, title=f"{x} vs {y}"))

    # --- Export Options ---
    if st.session_state.df is not None:
        st.sidebar.subheader("💾 Export")
        if st.sidebar.button("Export as CSV"):
            st.sidebar.download_button(
                "Download CSV",
                data=st.session_state.df.to_csv(index=False),
                file_name="export.csv",
                mime="text/csv"
            )
        if st.sidebar.button("Export as Excel"):
            st.sidebar.download_button(
                "Download Excel",
                data=st.session_state.df.to_excel(index=False),
                file_name="export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
