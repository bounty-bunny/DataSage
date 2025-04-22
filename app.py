import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import sweetviz as sv
import sqlite3
from db import create_connection, create_user_table, check_user, add_user

# Initialize session state variables if they don't exist
if 'form_mode' not in st.session_state:
    st.session_state.form_mode = 'login'  # Default to 'login' mode
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Helper functions for Sign Up and Login
def sign_up():
    with st.container():
        st.markdown("<h2 style='text-align: center;'>Sign Up</h2>", unsafe_allow_html=True)
        username = st.text_input("Create Username", key="signup_username")
        password = st.text_input("Create Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if password != confirm_password:
            st.error("Passwords do not match.")
        elif st.button("Sign Up", key="signup_button"):
            if check_user(username):
                st.error("Username already exists.")
            else:
                add_user(username, password)
                st.success("Account created successfully. Please log in.")
                st.session_state.form_mode = 'DataSage'  # Switch to login mode
                st.experimental_rerun()  # Re-run the app to refresh

def login():
    with st.container():
        st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", key="login_button"):
            if check_user(username, password):
                st.session_state.authenticated = True
                st.success("Logged in successfully!")
            else:
                st.error("Incorrect username or password.")

# Main flow: Check if user is authenticated
if not st.session_state.authenticated:
    if st.session_state.form_mode == 'login':
        login()
    elif st.session_state.form_mode == 'signup':
        sign_up()

    if st.session_state.form_mode == 'login':
        if st.button("Don't have an account? Sign Up"):
            st.session_state.form_mode = 'signup'  # Switch to sign-up mode
            st.experimental_rerun()  # Re-run the app to refresh
    elif st.session_state.form_mode == 'signup':
        if st.button("Already have an account? Login"):
            st.session_state.form_mode = 'login'  # Switch to login mode
            st.experimental_rerun()  # Re-run the app to refresh

else:
    if "df" not in st.session_state:
        st.session_state.df = None

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
        ["Upload File", "Connect SQL", "Data Insights", "Dashboard"]
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
                st.success(f"Uploaded {uploaded_file.name} successfully!")
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

            # Container to show all metrics together
            with st.container():
                # Metric Selection
                selected_metrics = st.multiselect(
                    "Select Metrics to Visualize",
                    df.columns.tolist(),
                    default=df.columns.tolist()  # Default to all columns
                )

                # Chart Type Selection
                chart_type = st.selectbox(
                    "Select Chart Type",
                    ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot"]
                )

                # Show selected metrics
                if selected_metrics:
                    st.markdown("### Selected Metrics Visualization")

                    # Bar Chart
                    if chart_type == "Bar Chart":
                        for metric in selected_metrics:
                            if df[metric].dtype in ['int64', 'float64']:
                                fig = px.bar(df, x=metric, title=f"Bar Chart of {metric}")
                                st.plotly_chart(fig, use_container_width=True)

                    # Line Chart
                    if chart_type == "Line Chart":
                        for metric in selected_metrics:
                            if df[metric].dtype in ['int64', 'float64']:
                                fig = px.line(df, x=df.index, y=metric, title=f"Line Chart of {metric}")
                                st.plotly_chart(fig, use_container_width=True)

                    # Pie Chart
                    if chart_type == "Pie Chart":
                        for metric in selected_metrics:
                            if df[metric].dtype in ['int64', 'float64']:
                                fig = px.pie(df, names=metric, title=f"Pie Chart of {metric}")
                                st.plotly_chart(fig, use_container_width=True)

                    # Scatter Plot
                    if chart_type == "Scatter Plot":
                        if len(selected_metrics) > 1:
                            scatter_x = st.selectbox("Select X-axis for Scatter Plot", selected_metrics)
                            scatter_y = st.selectbox("Select Y-axis for Scatter Plot", selected_metrics)
                            fig = px.scatter(df, x=scatter_x, y=scatter_y, title=f"Scatter Plot of {scatter_x} vs {scatter_y}")
                            st.plotly_chart(fig, use_container_width=True)

        else:
            st.warning("Please upload or connect to a dataset first.")

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
                mime="application/vnd.ms-excel"
            )
