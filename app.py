import streamlit as st
import pandas as pd
import sqlalchemy
import sqlite3
import sweetviz as sv
import numpy as np
import plotly.express as px
import requests
from requests.auth import HTTPBasicAuth
from authlib.integrations.requests_client import OAuth2Session

# SSO (OAuth) Integration Setup using Auth0
# For simplicity, use a mock SSO flow here - replace with actual Auth0/Okta/SSO configurations in production
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
AUTHORIZATION_URL = "https://your-auth0-domain/authorize"
TOKEN_URL = "https://your-auth0-domain/oauth/token"
REDIRECT_URI = "http://localhost:8501"

def authenticate_user():
    oauth = OAuth2Session(CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI)
    authorization_url, state = oauth.authorization_url(AUTHORIZATION_URL)
    st.write(f"Please [Login](%s) to continue" % authorization_url)
    # After login, the user is redirected here and we fetch the token to verify
    if 'code' in st.experimental_get_query_params():
        oauth.fetch_token(TOKEN_URL, authorization_response=st.experimental_get_query_params()['code'])
        st.session_state.authenticated = True
        st.success("Logged in successfully!")
    else:
        st.session_state.authenticated = False

# Streamlit Page Configuration
st.set_page_config(page_title="DataSage – Smart Data Tool", layout="wide")
st.title("📊 DataSage – Smart Data Uploader & Connector")

# Sidebar Menu
st.sidebar.header("📂 Upload or Connect")
menu_option = st.sidebar.radio(
    "Choose Data Source",
    ["Upload File", "Connect SQL", "Connect SharePoint (Coming Soon)", "Data Insights", "Dashboard", "ServiceNow Integration"]
)

# Check Authentication
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    authenticate_user()

if st.session_state.authenticated:
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
