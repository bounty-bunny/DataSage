import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sweetviz as sv
import sqlite3
import sqlalchemy
from db import create_connection, create_user_table, check_user, add_user

# Initialize session state
if 'form_mode' not in st.session_state:
    st.session_state.form_mode = 'login'
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Sign Up Logic
def sign_up():
    st.markdown("### Sign Up")
    username = st.text_input("Create Username")
    password = st.text_input("Create Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if password != confirm_password:
        st.error("Passwords do not match.")
    elif st.button("Sign Up"):
        conn = create_connection('your_database.db')
        if conn:
            create_user_table(conn)
            if check_user(conn, username):
                st.error("Username already exists.")
            else:
                add_user(conn, username, password)
                st.success("Account created. Please log in.")
                st.session_state.form_mode = 'login'
                st.experimental_rerun()
        else:
            st.error("DB connection failed.")

# Login Logic
def login():
    st.markdown("### Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        conn = create_connection('your_database.db')
        if conn:
            user = check_user(conn, username)
            if user and user[2] == password:
                st.session_state.authenticated = True
                st.success("Login successful.")
            else:
                st.error("Incorrect username or password.")
        else:
            st.error("DB connection failed.")

# Main Auth Flow
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
    st.sidebar.title("📂 Data Menu")
    menu = st.sidebar.radio("Choose Option", ["Upload File", "Connect SQL", "Data Insights", "Dashboard"])
    if "df" not in st.session_state:
        st.session_state.df = None

    def create_sample_data():
        return pd.DataFrame({
            "ID": range(1, 11),
            "Name": ["Alice", "Bob", "Charlie", "David", "Eva", "Frank", "Grace", "Hannah", "Ivy", "Jack"],
            "Age": np.random.randint(20, 60, 10),
            "Salary": np.random.randint(30000, 120000, 10),
            "Department": ["HR", "IT", "Finance", "Marketing", "IT", "HR", "Marketing", "Finance", "IT", "HR"]
        })

    if menu == "Upload File":
        uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.session_state.df = df
                st.success(f"{uploaded_file.name} uploaded!")
                st.dataframe(df)
            except Exception as e:
                st.error(f"Error: {e}")

    elif menu == "Connect SQL":
        st.subheader("🔌 SQL Connection")
        db_type = st.selectbox("DB Type", ["PostgreSQL", "MySQL", "SQLite"])

        if db_type == "SQLite":
            sqlite_file = st.file_uploader("Upload SQLite DB", type="db")
            if sqlite_file:
                try:
                    conn = sqlite3.connect(sqlite_file.name)
                    cursor = conn.cursor()
                    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                    table = st.selectbox("Select Table", tables)
                    if table:
                        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                        st.session_state.df = df
                        st.success("Table loaded.")
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"SQLite Error: {e}")
        else:
            host = st.text_input("Host", "localhost")
            port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
            dbname = st.text_input("Database")
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
                    table = st.selectbox("Table", tables)
                    if table:
                        df = pd.read_sql(f"SELECT * FROM {table} LIMIT 100", engine)
                        st.session_state.df = df
                        st.success("Data loaded.")
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"Connection failed: {e}")

    elif menu == "Data Insights":
        st.subheader("📊 Sweetviz Report")
        df = st.session_state.df or create_sample_data()
        st.session_state.df = df
        columns = st.multiselect("Choose columns", df.columns)
        if st.button("Generate Report"):
            with st.spinner("Analyzing..."):
                report = sv.analyze(df[columns] if columns else df)
                report.show_html("sweetviz_report.html", open_browser=False)
                with open("sweetviz_report.html", "r", encoding="utf-8") as f:
                    st.components.v1.html(f.read(), height=800, scrolling=True)

    elif menu == "Dashboard":
        st.subheader("📈 Visual Dashboard")
        df = st.session_state.df
        if df is not None:
            cols = st.multiselect("Select Columns", df.columns, default=df.columns)
            chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Pie", "Scatter"])
            if chart_type == "Bar":
                for col in cols:
                    if df[col].dtype in ['int64', 'float64']:
                        fig = px.bar(df, x=col)
                        st.plotly_chart(fig)
            elif chart_type == "Line":
                for col in cols:
                    if df[col].dtype in ['int64', 'float64']:
                        fig = px.line(df, y=col)
                        st.plotly_chart(fig)
            elif chart_type == "Pie":
                for col in cols:
                    if df[col].dtype == "object":
                        fig = px.pie(df, names=col)
                        st.plotly_chart(fig)
            elif chart_type == "Scatter" and len(cols) == 2:
                fig = px.scatter(df, x=cols[0], y=cols[1])
                st.plotly_chart(fig)
        else:
            st.warning("Please upload or connect to a dataset first.")
