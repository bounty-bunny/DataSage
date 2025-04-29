import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sweetviz as sv
import sqlite3
import sqlalchemy
from db import (
    create_connection,
    create_user_table,
    create_workspace_table,
    create_dashboard_tables,
    create_dashboard_sharing_and_history,
    create_comments_table,
    add_user,
    check_user,
    get_user_by_username,
    get_user_dashboards,
)

# After all your imports and db functions
st.set_page_config(page_title="DataSage", layout="wide")

# Initialize session state
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"
if "form_mode" not in st.session_state:
    st.session_state.form_mode = "login"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ------------------ AUTH SECTION ------------------

# Sign Up Logic
def sign_up():
    st.markdown("### Sign Up")
    username = st.text_input("Create Username")
    password = st.text_input("Create Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Sign Up"):
        if password != confirm_password:
            st.error("Passwords do not match.")
        else:
            conn = create_connection('your_database.db')
            if conn:
                create_user_table(conn)
                if get_user_by_username(conn, username):
                    st.error("Username already exists.")
                else:
                    add_user(conn, username, password)
                    st.success("Account created. Please log in.")
                    st.session_state.form_mode = 'login'
                    st.experimental_rerun()

# Login Logic
def login():
    st.markdown("### Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            conn = create_connection('your_database.db')
            if conn:
                user = check_user(conn, username, password)
                if user and user[2] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_id = user[0]
                    st.experimental_rerun()
                else:
                    st.error("Incorrect credentials.")

# ------------------ MAIN APP ------------------

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
    # ---------- DATABASE INITIALIZATION ----------
    conn = create_connection('your_database.db')
    if conn:
        create_user_table(conn)
        create_workspace_table(conn)
        create_dashboard_tables(conn)
        create_dashboard_sharing_and_history(conn)
        create_comments_table(conn)

    # ---------- SIDEBAR STRUCTURE ----------
    st.sidebar.image("https://img.icons8.com/external-flat-juicy-fish/64/data-analytics.png", width=40)
    st.sidebar.title("📊 DataSage")
    sidebar_option = st.sidebar.selectbox("Choose Activity", [
        "📁 Data Manager", 
        "📈 Data Insights", 
        "📊 Dashboard Manager",
        "🚪 Logout"
    ])

    # ---------- FILE / DB UPLOAD ----------
    if sidebar_option == "📁 Data Manager":
        st.subheader("📁 Upload or Connect Data")
        menu = st.radio("Source", ["Upload File", "Connect SQL"], horizontal=True)

        if menu == "Upload File":
            uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                    st.session_state.df = df
                    st.success(f"{uploaded_file.name} uploaded!")
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Error: {e}")

        elif menu == "Connect SQL":
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
                        engine_str = (
                            f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
                            if db_type == "PostgreSQL"
                            else f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}"
                        )
                        engine = sqlalchemy.create_engine(engine_str)
                        tables = sqlalchemy.inspect(engine).get_table_names()
                        table = st.selectbox("Select Table", tables)
                        if table:
                            df = pd.read_sql(f"SELECT * FROM {table} LIMIT 100", engine)
                            st.session_state.df = df
                            st.success("Data loaded.")
                            st.dataframe(df)
                    except Exception as e:
                        st.error(f"Connection failed: {e}")

    # ---------- SWEETVIZ REPORT ----------
    elif sidebar_option == "📈 Data Insights":
        st.subheader("📊 Sweetviz Report")
        df = st.session_state.df if "df" in st.session_state else None
        if df is not None:
            columns = st.multiselect("Choose columns", df.columns)
            if st.button("Generate Report"):
                with st.spinner("Analyzing..."):
                    report = sv.analyze(df[columns] if columns else df)
                    report.show_html("sweetviz_report.html", open_browser=False)
                    with open("sweetviz_report.html", "r", encoding="utf-8") as f:
                        st.components.v1.html(f.read(), height=800, scrolling=True)
        else:
            st.warning("Upload or connect to a dataset first.")

    # ---------- DASHBOARD MANAGER ----------
    elif sidebar_option == "📊 Dashboard Manager":
        st.subheader("📊 Visual Dashboard")
        df = st.session_state.df if "df" in st.session_state else None
        if df is not None and not df.empty:
            action = st.radio("Action", ["Create New", "View Existing"], horizontal=True)
            if action == "Create New":
                dashboard_name = st.text_input("Dashboard Name")
                cols = st.multiselect("Select Columns", df.columns.tolist())
                chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Pie", "Scatter"])
                if st.button("Save Dashboard"):
                    if dashboard_name and cols:
                        save_dashboard(conn, st.session_state.user_id, dashboard_name, cols, chart_type)
                        st.success(f"Dashboard '{dashboard_name}' saved!")
                        st.experimental_rerun()
                    else:
                        st.warning("Please provide a dashboard name and select columns.")
            elif action == "View Existing":
                dashboards = get_user_dashboards(conn, st.session_state.user_id)
                dashboard_map = {name: id for id, name in dashboards}
                selected_dashboard_name = st.selectbox("Select Dashboard", list(dashboard_map.keys()))
                if selected_dashboard_name:
                    dashboard_id = dashboard_map[selected_dashboard_name]
                    data = load_dashboard(conn, dashboard_id)
                    if data:
                        _, _, name, columns_json, chart_type, _ = data
                        selected_cols = json.loads(columns_json)
                        st.success(f"Loaded Dashboard: {name}")
                        # Chart rendering
                        if chart_type == "Bar":
                            for col in selected_cols:
                                if df[col].dtype in ['int64', 'float64']:
                                    st.plotly_chart(px.bar(df, x=col))
                        elif chart_type == "Line":
                            for col in selected_cols:
                                if df[col].dtype in ['int64', 'float64']:
                                    st.plotly_chart(px.line(df, y=col))
                        elif chart_type == "Pie":
                            for col in selected_cols:
                                if df[col].dtype == "object":
                                    st.plotly_chart(px.pie(df, names=col))
                        elif chart_type == "Scatter" and len(selected_cols) >= 2:
                            st.plotly_chart(px.scatter(df, x=selected_cols[0], y=selected_cols[1]))

                        if st.button("Delete This Dashboard"):
                            delete_dashboard(conn, dashboard_id)
                            st.success("Dashboard deleted.")
                            st.experimental_rerun()
        else:
            st.warning("Upload or connect to a dataset first.")

    # ---------- LOGOUT ----------
    elif sidebar_option == "🚪 Logout":
        st.session_state.authenticated = False
        st.session_state.clear()
        st.experimental_rerun()
