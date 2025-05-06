import streamlit as st
import os
from datetime import datetime
import json

# Internal imports
from auth import authenticate_user, create_user, logout_user
from workspace import load_workspaces, create_workspace
from dashboard import get_user_dashboards
from data_manager import load_data_source
from config import APP_NAME, APP_VERSION, DB_PATH, LOGO_PATH

# Page config
st.set_page_config(
    page_title=f"{APP_NAME} - Data Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
with open("assets/css/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "current_workspace" not in st.session_state:
    st.session_state.current_workspace = None
if "current_dashboard" not in st.session_state:
    st.session_state.current_dashboard = None
if "data_sources" not in st.session_state:
    st.session_state.data_sources = {}

# App header with logo
def render_header():
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.image(LOGO_PATH, width=70)
    with col2:
        st.title(f"{APP_NAME}")
    with col3:
        if st.session_state.authenticated:
            st.markdown(f"""
            <div class="user-info">
                <span>👤 {st.session_state.username}</span>
                <span class="role-badge">{st.session_state.user_role}</span>
            </div>
            """, unsafe_allow_html=True)

# Sidebar navigation
def render_sidebar():
    st.sidebar.markdown(f"## {APP_NAME} v{APP_VERSION}")
    
    if st.session_state.authenticated:
        # Workspace selector
        workspaces = load_workspaces(st.session_state.user_id)
        workspace_names = [ws[1] for ws in workspaces]
        
        if workspace_names:
            selected_workspace = st.sidebar.selectbox(
                "Select Workspace", 
                workspace_names,
                index=0 if st.session_state.current_workspace is None else workspace_names.index(st.session_state.current_workspace[1])
            )
            
            # Set current workspace
            for ws in workspaces:
                if ws[1] == selected_workspace:
                    st.session_state.current_workspace = ws
                    break
        
        # Navigation menu
        st.sidebar.markdown("### Navigation")
        nav_option = st.sidebar.radio(
            "",
            ["📂 Data Sources", "🔍 Data Explorer", "📊 Dashboards", "⚙️ Settings"]
        )
        
        # Create workspace button
        with st.sidebar.expander("➕ New Workspace"):
            new_ws_name = st.text_input("Workspace Name")
            if st.button("Create"):
                if new_ws_name:
                    create_workspace(new_ws_name, st.session_state.user_id)
                    st.rerun()
        
        # Logout button
        if st.sidebar.button("🚪 Logout"):
            logout_user()
            st.rerun()
            
        return nav_option
    else:
        return None

# Authentication forms
def render_auth_forms():
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                success, user_data = authenticate_user(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_data[0]
                    st.session_state.username = user_data[1]
                    st.session_state.user_role = user_data[3]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("signup_form"):
            new_username = st.text_input("Create Username")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            signup_submitted = st.form_submit_button("Sign Up")
            
            if signup_submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif not new_username or not new_password:
                    st.error("Username and password are required")
                else:
                    success = create_user(new_username, new_password)
                    if success:
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")

# Data sources page
def render_data_sources():
    st.header("📂 Data Sources")
    
    # Data source options
    source_type = st.selectbox(
        "Select Data Source Type",
        ["File Upload", "Database Connection", "SharePoint List", "Sample Data"]
    )
    
    if source_type == "File Upload":
        file = st.file_uploader("Upload file", type=["csv", "xlsx", "json"])
        if file is not None:
            try:
                data_source = load_data_source(file, source_type)
                if data_source:
                    st.session_state.data_sources[file.name] = data_source
                    st.success(f"Successfully loaded: {file.name}")
                    st.dataframe(data_source.data.head())
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
    
    elif source_type == "Database Connection":
        db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL", "SQLite"])
        
        if db_type == "SQLite":
            db_file = st.file_uploader("Upload SQLite DB", type=["db", "sqlite"])
            if db_file and st.button("Connect"):
                try:
                    data_source = load_data_source(db_file, source_type, db_type=db_type)
                    if data_source:
                        st.session_state.data_sources[db_file.name] = data_source
                        st.success(f"Connected to: {db_file.name}")
                        st.write("Available tables:")
                        st.write(data_source.tables)
                except Exception as e:
                    st.error(f"Error connecting to database: {str(e)}")
        else:
            with st.form("db_connection_form"):
                host = st.text_input("Host", "localhost")
                port = st.text_input("Port", "5432" if db_type == "PostgreSQL" else "3306")
                database = st.text_input("Database Name")
                user = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Connect"):
                    try:
                        connection_data = {
                            "host": host,
                            "port": port,
                            "database": database,
                            "user": user,
                            "password": password
                        }
                        data_source = load_data_source(connection_data, source_type, db_type=db_type)
                        if data_source:
                            source_name = f"{db_type}_{database}"
                            st.session_state.data_sources[source_name] = data_source
                            st.success(f"Connected to: {database}")
                            st.write("Available tables:")
                            st.write(data_source.tables)
                    except Exception as e:
                        st.error(f"Error connecting to database: {str(e)}")
    
    # Display active data sources if any
    if st.session_state.data_sources:
        st.subheader("Active Data Sources")
        for name, source in st.session_state.data_sources.items():
            st.markdown(f"**{name}** - {source.type}")

# Data explorer page
def render_data_explorer():
    st.header("🔍 Data Explorer")
    
    if not st.session_state.data_sources:
        st.info("No data sources available. Add a data source first.")
        return
    
    # Data source selector
    source_name = st.selectbox("Select Data Source", list(st.session_state.data_sources.keys()))
    data_source = st.session_state.data_sources[source_name]
    
    # Display options based on source type
    if data_source.type == "file":
        st.dataframe(data_source.data)
        
        # Data analysis options
        with st.expander("Data Analysis"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Generate Summary Statistics"):
                    st.write(data_source.data.describe())
            with col2:
                if st.button("Check Missing Values"):
                    st.write(data_source.data.isnull().sum())
        
        # Visualization options
        with st.expander("Quick Visualizations"):
            viz_type = st.selectbox("Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram"])
            
            if viz_type == "Bar Chart":
                x_col = st.selectbox("X-axis", data_source.data.columns)
                y_col = st.selectbox("Y-axis", data_source.data.columns)
                # Code for bar chart visualization would go here
            
            # Other visualization options would follow
    
    elif data_source.type == "database":
        # Table selector for database
        selected_table = st.selectbox("Select Table", data_source.tables)
        if selected_table:
            # Option for custom SQL query
            use_custom_sql = st.checkbox("Use Custom SQL Query")
            if use_custom_sql:
                sql_query = st.text_area("Enter SQL Query", f"SELECT * FROM {selected_table} LIMIT 100")
                if st.button("Run Query"):
                    try:
                        result = data_source.execute_query(sql_query)
                        st.dataframe(result)
                    except Exception as e:
                        st.error(f"Query error: {str(e)}")
            else:
                # Simple table view
                df = data_source.get_table_data(selected_table)
                st.dataframe(df)

# Dashboards page
def render_dashboards():
    st.header("📊 Dashboards")
    
    if st.session_state.current_workspace is None:
        st.info("Please select or create a workspace first.")
        return
    
    # Get dashboards for current workspace
    dashboards = get_user_dashboards(st.session_state.user_id, st.session_state.current_workspace[0])
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Dashboards in {st.session_state.current_workspace[1]}")
    with col2:
        if st.button("➕ New Dashboard"):
            st.session_state.current_dashboard = "new"
            st.rerun()
    
    # Display dashboards or create new one
    if st.session_state.current_dashboard == "new":
        with st.form("new_dashboard_form"):
            dashboard_name = st.text_input("Dashboard Name")
            dashboard_desc = st.text_area("Description")
            submitted = st.form_submit_button("Create Dashboard")
            if submitted and dashboard_name:
                # Code to create new dashboard
                pass
    elif dashboards:
        # Display existing dashboards in a grid
        dashboard_cols = st.columns(3)
        for i, dashboard in enumerate(dashboards):
            with dashboard_cols[i % 3]:
                st.markdown(f"""
                <div class="dashboard-card">
                    <h3>{dashboard[1]}</h3>
                    <p>Created: {dashboard[4]}</p>
                    <button>Open</button>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No dashboards in this workspace yet. Create your first dashboard!")

# Settings page
def render_settings():
    st.header("⚙️ Settings")
    
    tabs = st.tabs(["Profile", "Workspace Settings", "App Settings"])
    
    with tabs[0]:
        st.subheader("User Profile")
        st.write(f"Username: {st.session_state.username}")
        st.write(f"Role: {st.session_state.user_role}")
        
        with st.expander("Change Password"):
            with st.form("change_password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submitted = st.form_submit_button("Update Password")
                if submitted:
                    # Password change logic would go here
                    pass
    
    with tabs[1]:
        if st.session_state.current_workspace:
            st.subheader(f"Workspace: {st.session_state.current_workspace[1]}")
            
            if st.session_state.user_role == "admin":
                # Admin settings for workspace
                with st.expander("Users & Permissions"):
                    st.write("Manage user access and roles")
                    # User management UI would go here
            else:
                st.info("Only workspace admins can modify workspace settings.")
    
    with tabs[2]:
        st.subheader("Application Settings")
        theme = st.selectbox("Theme", ["Light", "Dark", "System Default"])
        data_preview_rows = st.slider("Data Preview Rows", 5, 100, 20)
        
        if st.button("Save Settings"):
            # Save settings logic would go here
            st.success("Settings saved!")

# Main application
def main():
    render_header()
    
    # Authentication check
    if not st.session_state.authenticated:
        render_auth_forms()
    else:
        # Render sidebar and get navigation option
        nav_option = render_sidebar()
        
        # Render appropriate page based on navigation
        if nav_option == "📂 Data Sources":
            render_data_sources()
        elif nav_option == "🔍 Data Explorer":
            render_data_explorer()
        elif nav_option == "📊 Dashboards":
            render_dashboards()
        elif nav_option == "⚙️ Settings":
            render_settings()

if __name__ == "__main__":
    main()
