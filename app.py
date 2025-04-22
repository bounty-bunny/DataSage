import streamlit as st
import pandas as pd
import sqlalchemy
import sqlite3
import sweetviz as sv
import os

st.set_page_config(page_title="DataSage – Smart Data Tool", layout="wide")
st.title("📊 DataSage – Smart Data Uploader & Profiler")

# Sidebar Menu
st.sidebar.header("📂 Upload or Connect")
menu_option = st.sidebar.radio("Choose Data Source", ["Upload File", "Connect SQL", "Connect SharePoint (Coming Soon)"])

# Session cache
if "df" not in st.session_state:
    st.session_state.df = None

# Upload File
if menu_option == "Upload File":
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.session_state.df = df
        st.success(f"Uploaded `{uploaded_file.name}` successfully!")
        st.dataframe(df)

# Connect SQL
elif menu_option == "Connect SQL":
    st.subheader("🔌 Connect to SQL Database")
    db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQLite"])

    if db_type == "SQLite":
        sqlite_file = st.file_uploader("Upload SQLite DB", type="db")
        if sqlite_file:
            conn = sqlite3.connect(sqlite_file.name)
            cursor = conn.cursor()
            tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            table = st.selectbox("Select Table", tables)
            if table:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                st.session_state.df = df
                st.success("Data fetched!")
                st.dataframe(df)
    else:
        host = st.text_input("Host", "localhost")
        port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
        dbname = st.text_input("Database Name")
        user = st.text_input("User")
        password = st.text_input("Password", type="password")

        if st.button("Connect"):
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

# Profiling & Export
if st.session_state.df is not None:
    st.sidebar.subheader("🔍 Analyze & Export")
    if st.sidebar.button("Generate Data Report"):
        profile = sv.analyze(st.session_state.df)
        profile_path = "sweetviz_report.html"
        profile.show_html(profile_path, open_browser=False)
        with open(profile_path, "rb") as f:
            st.download_button("Download Report", f, "DataSage_Report.html")

    if st.sidebar.button("Export as CSV"):
        st.sidebar.download_button(
            label="Download CSV",
            data=st.session_state.df.to_csv(index=False),
            file_name="data_export.csv",
            mime="text/csv"
        )
