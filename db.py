import sqlite3
import json
import streamlit as st

def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        print(f"[DB] Connected to {db_file} successfully")
        return conn
    except sqlite3.Error as e:
        print(f"[DB ERROR] Connection failed: {e}")
        return None

def execute_query(conn, query, label=""):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        if label:
            print(f"{label} - Executed successfully.")
    except Exception as e:
        print(f"Error executing {label}: {e}")
        st.error(f"Database Error: {e}")

# === USER FUNCTIONS ===

def create_user_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'viewer'
    );
    """
    execute_query(conn, query, "User table creation")

def check_user(conn, username, password):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"[DB ERROR] check_user: {e}")
        return None

def add_user(conn, username, password, role="viewer"):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        print(f"[DB] User '{username}' added successfully with role '{role}'.")
    except sqlite3.IntegrityError:
        print(f"[DB ERROR] Username '{username}' already exists.")
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to add user: {e}")

def get_user_by_username(conn, username):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"[DB ERROR] get_user_by_username: {e}")
        return None

# === WORKSPACE FUNCTIONS ===

def create_workspace_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS workspaces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS user_workspace (
        user_id INTEGER,
        workspace_id INTEGER,
        role TEXT DEFAULT 'editor',
        PRIMARY KEY(user_id, workspace_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
    );
    """
    try:
        cursor = conn.cursor()
        cursor.executescript(query)
        conn.commit()
        print("[DB] Workspace tables created.")
    except Exception as e:
        print(f"[DB ERROR] create_workspace_table: {e}")
        st.error(f"Database Error: {e}")

def create_workspace(conn, name):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO workspaces (name) VALUES (?)", (name,))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        print(f"[DB ERROR] Workspace '{name}' already exists.")
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to create workspace: {e}")
    return None

def add_user_to_workspace(conn, user_id, workspace_id, role="editor"):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO user_workspace (user_id, workspace_id, role)
            VALUES (?, ?, ?)
        """, (user_id, workspace_id, role))
        conn.commit()
        print(f"[DB] User {user_id} added to workspace {workspace_id} as {role}")
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to add user to workspace: {e}")

def get_user_workspaces(conn, user_id):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT w.id, w.name, uw.role 
            FROM workspaces w
            JOIN user_workspace uw ON w.id = uw.workspace_id
            WHERE uw.user_id = ?
        """, (user_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"[DB ERROR] get_user_workspaces: {e}")
        return []

# === DASHBOARD TABLES ===

def create_dashboard_tables(conn):
    query1 = """
    CREATE TABLE IF NOT EXISTS dashboards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        user_id INTEGER,
        workspace_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
    );
    """
    query2 = """
    CREATE TABLE IF NOT EXISTS dashboard_elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dashboard_id INTEGER,
        element_type TEXT,
        element_data TEXT,
        settings_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
    );
    """
    execute_query(conn, query1, "Dashboard table creation")
    execute_query(conn, query2, "Dashboard elements table creation")

# === SHARING & VERSION HISTORY ===

def create_dashboard_sharing_and_history(conn):
    query1 = """
    CREATE TABLE IF NOT EXISTS dashboard_shares (
        dashboard_id INTEGER,
        shared_with_user_id INTEGER,
        permission TEXT DEFAULT 'view',
        PRIMARY KEY(dashboard_id, shared_with_user_id),
        FOREIGN KEY(dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
        FOREIGN KEY(shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    query2 = """
    CREATE TABLE IF NOT EXISTS dashboard_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dashboard_id INTEGER,
        version_number INTEGER,
        snapshot TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
    );
    """
    execute_query(conn, query1, "Dashboard shares table creation")
    execute_query(conn, query2, "Dashboard history table creation")

# === COMMENTS ===

def create_comments_table(conn):
    query = """
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        element_id INTEGER,
        user_id INTEGER,
        comment_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(element_id) REFERENCES dashboard_elements(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """
    execute_query(conn, query, "Comments table creation")

# === INIT ===

def initialize_database(conn):
    print("[DB INIT] Initializing all required tables...")
    create_user_table(conn)
    create_workspace_table(conn)
    create_dashboard_tables(conn)
    create_dashboard_sharing_and_history(conn)
    create_comments_table(conn)
    print("[DB INIT] Initialization complete.")

# === DASHBOARD OPERATIONS ===

def save_dashboard_element(conn, dashboard_id, element_type, element_data, settings_json=None):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO dashboard_elements (dashboard_id, element_type, element_data, settings_json)
            VALUES (?, ?, ?, ?)
        ''', (dashboard_id, element_type, json.dumps(element_data), json.dumps(settings_json) if settings_json else None))
        conn.commit()
        print(f"[DB] Dashboard element saved successfully.")
    except sqlite3.Error as e:
        print(f"[DB ERROR] save_dashboard_element: {e}")

def get_user_dashboards(conn, user_id, workspace_id=None):
    try:
        cursor = conn.cursor()
        if workspace_id:
            cursor.execute('''
                SELECT id, name FROM dashboards 
                WHERE user_id=? AND workspace_id=?
            ''', (user_id, workspace_id))
        else:
            cursor.execute('''
                SELECT id, name FROM dashboards 
                WHERE user_id=?
            ''', (user_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"[DB ERROR] get_user_dashboards: {e}")
        return []

def get_dashboard_elements(conn, dashboard_id):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, element_type, element_data, settings_json
            FROM dashboard_elements
            WHERE dashboard_id=?
        ''', (dashboard_id,))
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"[DB ERROR] get_dashboard_elements: {e}")
        return []

def delete_dashboard(conn, dashboard_id):
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM dashboards WHERE id=?', (dashboard_id,))
        conn.commit()
        print(f"[DB] Dashboard {dashboard_id} deleted successfully.")
    except sqlite3.Error as e:
        print(f"[DB ERROR] delete_dashboard: {e}")
