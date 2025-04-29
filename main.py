import streamlit as st
from db import *
import os

# Connect to SQLite DB
DB_PATH = "datasage.db"
conn = create_connection(DB_PATH)
initialize_database(conn)

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- SESSION STATE INIT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.workspace_id = None
    st.session_state.workspace_name = ""

# --- SIDEBAR LAYOUT ---
def sidebar_menu():
    st.sidebar.markdown('<h2 class="sidebar-title">DataSage</h2>', unsafe_allow_html=True)
    selected = st.sidebar.radio(
        "Navigation",
        options=["📊 Dashboards", "➕ New Dashboard", "⚙️ Workspaces", "🔓 Logout"] if st.session_state.logged_in else ["🔐 Login", "🧾 Sign Up"],
        key="sidebar_option"
    )
    return selected

# --- LOGIN ---
def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_user(conn, username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.username = username
            st.success(f"Welcome {username}!")
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- SIGN UP ---
def signup_page():
    st.title("Sign Up")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")
    if st.button("Create Account"):
        if get_user_by_username(conn, username):
            st.warning("Username already taken.")
        else:
            add_user(conn, username, password)
            st.success("Account created! Please log in.")
            st.rerun()

# --- WORKSPACE SELECTOR ---
def workspace_selector():
    st.subheader("Select a Workspace")
    user_workspaces = get_user_workspaces(conn, st.session_state.user_id)
    if not user_workspaces:
        st.info("No workspaces found. Create one below.")
        new_name = st.text_input("New Workspace Name")
        if st.button("Create Workspace"):
            ws_id = create_workspace(conn, new_name)
            add_user_to_workspace(conn, st.session_state.user_id, ws_id)
            st.success(f"Workspace '{new_name}' created.")
            st.rerun()
    else:
        names = [w[1] for w in user_workspaces]
        selected = st.selectbox("Your Workspaces", names)
        if st.button("Enter Workspace"):
            for ws in user_workspaces:
                if ws[1] == selected:
                    st.session_state.workspace_id = ws[0]
                    st.session_state.workspace_name = selected
                    break
            st.rerun()

# --- DASHBOARD LIST ---
def dashboards_page():
    st.subheader(f"Dashboards in '{st.session_state.workspace_name}'")
    dashboards = get_user_dashboards(conn, st.session_state.user_id, st.session_state.workspace_id)
    if dashboards:
        for d in dashboards:
            st.write(f"📌 **{d[1]}**")
    else:
        st.info("No dashboards yet.")

# --- NEW DASHBOARD ---
def create_dashboard_page():
    st.subheader("Create a New Dashboard")
    name = st.text_input("Dashboard Name")
    if st.button("Create"):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dashboards (name, user_id, workspace_id) VALUES (?, ?, ?)",
            (name, st.session_state.user_id, st.session_state.workspace_id)
        )
        conn.commit()
        st.success(f"Dashboard '{name}' created.")
        st.rerun()

# --- ROUTING ---
selected = sidebar_menu()

if not st.session_state.logged_in:
    if selected == "🔐 Login":
        login_page()
    elif selected == "🧾 Sign Up":
        signup_page()
else:
    if not st.session_state.workspace_id:
        workspace_selector()
    else:
        if selected == "📊 Dashboards":
            dashboards_page()
        elif selected == "➕ New Dashboard":
            create_dashboard_page()
        elif selected == "⚙️ Workspaces":
            st.session_state.workspace_id = None
            st.rerun()
        elif selected == "🔓 Logout":
            st.session_state.clear()
            st.rerun()
