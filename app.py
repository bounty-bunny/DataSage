import streamlit as st
import pandas as pd
import sqlalchemy
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
from pandas_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report

st.set_page_config(page_title="DataSage – Smart Data Tool", layout="wide")
st.title("📊 DataSage – Smart Data Uploader & Analyzer")

# Sidebar Menu
st.sidebar.header("📂 Data Operations")
menu_option = st.sidebar.radio("Choose Operation", [
    "Upload File", 
    "Connect SQL", 
    "Data Profiling", 
    "Visualize Data", 
    "Download Data"
])

# Session cache
if "df" not in st.session_state:
    st.session_state.df = None

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

# Data Profiling
elif menu_option == "Data Profiling":
    if st.session_state.df is not None:
        st.subheader("🔎 Data Profiling Report")
        profile = ProfileReport(st.session_state.df, minimal=True)
        st_profile_report(profile)
    else:
        st.warning("No data loaded. Please upload or connect to a dataset.")

# Visualizations
elif menu_option == "Visualize Data":
    if st.session_state.df is not None:
        st.subheader("📈 Data Visualization")
        columns = st.multiselect("Select Columns", st.session_state.df.columns)

        if len(columns) == 1:
            col = columns[0]
            fig, ax = plt.subplots()
            sns.histplot(st.session_state.df[col].dropna(), kde=True, ax=ax)
            st.pyplot(fig)

        elif len(columns) == 2:
            x, y = columns
            fig, ax = plt.subplots()
            sns.scatterplot(data=st.session_state.df, x=x, y=y, ax=ax)
            st.pyplot(fig)

        if st.checkbox("Show Correlation Heatmap"):
            corr = st.session_state.df.select_dtypes(include='number').corr()
            fig, ax = plt.subplots()
            sns.heatmap(corr, annot=True, cmap='coolwarm', ax=ax)
            st.pyplot(fig)
    else:
        st.warning("No data loaded. Please upload or connect to a dataset.")

# Download
elif menu_option == "Download Data":
    if st.session_state.df is not None:
        st.sidebar.subheader("💾 Save / Export")
        st.download_button(
            label="Download CSV",
            data=st.session_state.df.to_csv(index=False),
            file_name="data_export.csv",
            mime="text/csv"
        )
    else:
        st.warning("No data loaded to download.")
