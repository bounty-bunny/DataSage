import streamlit as st
import pandas as pd
import numpy as np
import sweetviz as sv
import plotly.express as px
import sqlite3
import sqlalchemy
from requests.auth import HTTPBasicAuth

# Streamlit Page Configuration
st.set_page_config(page_title="DataSage – Smart Data Tool", layout="wide")
st.title("📊 DataSage – Smart Data Uploader & Connector")

# In-memory user storage (for demo purposes)
if 'users' not in st.session_state:
    st.session_state.users = {}

# Helper functions for Sign Up and Login
def sign_up():
    st.subheader("📋 Sign Up")
    username = st.text_input("Create Username")
    password = st.text_input("Create Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if password != confirm_password:
        st.error("Passwords do not match.")
    elif st.button("Sign Up"):
        if username in st.session_state.users:
            st.error("Username already exists.")
        else:
            st.session_state.users[username] = password
            st.success("Account created successfully. Please log in.")
            st.session_state.authenticated = False
            st.experimental_rerun()

def login():
    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in st.session_state.users and st.session_state.users[username] == password:
            st.session_state.authenticated = True
            st.success("Logged in successfully!")
        else:
            st.error("Incorrect username or password.")

# Initialize session state if not already initialized
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Main flow: Check if user is authenticated
if not st.session_state.authenticated:
    # Two buttons to toggle between login and signup
    login_button, sign_up_button = st.columns(2)

    with login_button:
        if st.button("Login"):
            login()

    with sign_up_button:
        if st.button("Sign Up"):
            sign_up()

else:
    # Session cache
    if "df" not in st.session_state:
        st.session_state.df = None

    # Create a sample dataset when no file is uploaded
    def create_sample_data():
        data = {
            "ID": range(1, 11),
            "Name": ["Alice", "Bob", "Charlie", "David", "Eva", "Frank", "Grace", "Hannah", "Ivy", "Jack"],
            "Age": np.random.randint(20, 60, size=10),
            "Salary": np.random.randint(30000, 120000, size=10),
            "Department": ["HR", "IT", "Finance", "Marketing", "IT", "HR", "Marketing", "Finance", "IT", "HR"]
        }
        return pd.DataFrame(data)

    # Sidebar Menu
    st.sidebar.header("📂 Upload or Connect")
    menu_option = st.sidebar.radio(
        "Choose Data Source",
        ["Upload File", "Connect SQL", "Connect SharePoint (Coming Soon)", "Data Insights", "Dashboard", "ServiceNow Integration"]
    )

    # Upload File
    if menu_option == "Upload File":
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.session_state.df = df
                st.success(f"Uploaded `{uploaded_file.name}` successfully!")
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # Connect SQL
    elif menu_option == "Connect SQL":
        st.subheader("🔌 Connect to SQL Database")
        db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQLite"])

        if db_type == "SQLite":
            sqlite_file = st.file_uploader("Upload SQLite DB", type="db")
            if sqlite_file:
                try:
                    conn = sqlite3.connect(sqlite_file.name)
                    cursor = conn.cursor()
                    tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
                    table = st.selectbox("Select Table", tables)
                    if table:
                        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                        st.session_state.df = df
                        st.success("Data fetched!")
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"SQLite Error: {e}")
        else:
            host = st.text_input("Host", "localhost")
            port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
            dbname = st.text_input("Database Name")
            user = st.text_input("User")
            password = st.text_input("Password", type="password")

            if st.button("Connect"):
                try:
                    if db_type == "PostgreSQL":
                        engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}")
                    else:
                        engine = sqlalchemy.create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}")

                    inspector = sqlalchemy.inspect(engine)
                    tables = inspector.get_table_names()
                    table = st.selectbox("Select Table", tables)

                    if table:
                        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 100", engine)
                        st.session_state.df = df
                        st.success("Connected and Data Loaded!")
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"Connection Error: {e}")

    # Data Insights (Sweetviz)
    elif menu_option == "Data Insights":
        st.subheader("📈 Automated EDA Report with Sweetviz")
        if st.session_state.df is not None:
            df = st.session_state.df
        else:
            df = create_sample_data()
            st.session_state.df = df
            st.warning("Using sample data since no dataset was uploaded or connected.")

        columns_to_analyze = st.multiselect("Select columns for EDA", df.columns)
        if columns_to_analyze:
            filtered_df = df[columns_to_analyze]
        else:
            filtered_df = df
        if st.button("🔍 Generate EDA Report"):
            with st.spinner("Generating report..."):
                report = sv.analyze(filtered_df)
                report.show_html(filepath="sweetviz_report.html", open_browser=False)

                with open("sweetviz_report.html", "r", encoding="utf-8") as f:
                    html_report = f.read()

                st.components.v1.html(html_report, height=1000, scrolling=True)
        else:
            st.warning("Please upload or connect to a dataset first.")

    # Dashboard
    elif menu_option == "Dashboard":
        st.subheader("📊 Data Dashboard")
        if st.session_state.df is not None:
            df = st.session_state.df
            st.write("Select metrics to visualize:")
            metric = st.selectbox("Select Metric", df.columns)
            fig = px.histogram(df, x=metric)
            st.plotly_chart(fig)
        else:
            st.warning("Please upload or connect to a dataset first.")

    # ServiceNow Integration
    elif menu_option == "ServiceNow Integration":
        st.subheader("🔌 ServiceNow Data Fetch")
        def fetch_servicenow_data():
            url = "https://your-instance.service-now.com/api/now/table/incident"
            auth = HTTPBasicAuth('username', 'password')  #
