import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sweetviz as sv
import sqlite3
import sqlalchemy
import requests
from requests.auth import HTTPBasicAuth

# In-memory user storage (for demo purposes)
if 'users' not in st.session_state:
    st.session_state.users = {}

# Ensure form_mode is initialized
if 'form_mode' not in st.session_state:
    st.session_state.form_mode = 'login'  # Default to login form

# Helper functions for Sign Up and Login
def sign_up():
    # Centering the form using container and markdown
    with st.container():
        st.markdown("<h2 style='text-align: center;'>Sign Up</h2>", unsafe_allow_html=True)
        username = st.text_input("Create Username", key="signup_username")
        password = st.text_input("Create Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if password != confirm_password:
            st.error("Passwords do not match.")
        elif st.button("Sign Up", key="signup_button"):
            if username in st.session_state.users:
                st.error("Username already exists.")
            else:
                st.session_state.users[username] = password
                st.success("Account created successfully. Please log in.")
                st.session_state.form_mode = 'login'  # Switch back to login form after successful signup
                st.experimental_rerun()  # Re-run to refresh the state and show login form

def login():
    # Centering the form using container and markdown
    with st.container():
        st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.authenticated = True
                st.success("Logged in successfully!")
            else:
                st.error("Incorrect username or password.")

# Main flow: Check if user is authenticated
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Show login or sign-up form based on form_mode state
    if st.session_state.form_mode == 'login':
        login()
    elif st.session_state.form_mode == 'signup':
        sign_up()

    # Button to switch between forms
    if st.session_state.form_mode == 'login':
        if st.button("Don't have an account? Sign Up"):
            st.session_state.form_mode = 'signup'  # Switch to sign-up form
            st.experimental_rerun()  # Refresh to show the sign-up form
    elif st.session_state.form_mode == 'signup':
        if st.button("Already have an account? Login"):
            st.session_state.form_mode = 'login'  # Switch to login form
            st.experimental_rerun()  # Refresh to show the login form

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
            auth = HTTPBasicAuth('username', 'password')  # Replace with ServiceNow credentials
            headers = {"Accept": "application/json"}

            response = requests.get(url, auth=auth, headers=headers)
            if response.status_code == 200:
                incidents = response.json()['result']
                return pd.DataFrame(incidents)
            else:
                st.error("Error fetching data from ServiceNow")
                return None
        
        df = fetch_servicenow_data()
        if df is not None:
            st.write("Fetched Data from ServiceNow:")
            st.dataframe(df)

    # Display export/save options
    if st.session_state.df is not None:
        st.sidebar.subheader("💾 Save / Export")
        if st.sidebar.button("Export as CSV"):
            st.sidebar.download_button(
                label="Download CSV",
                data=st.session_state.df.to_csv(index=False),
                file_name="data_export.csv",
                mime="text/csv"
            )
        if st.sidebar.button("Export as Excel"):
            st.sidebar.download_button(
                label="Download Excel",
                data=st.session_state.df.to_excel(index=False),
                file_name="data_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
