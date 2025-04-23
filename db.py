import sqlite3

def create_connection(db_file):
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        print(f"Connected to {db_file} successfully")
    except sqlite3.Error as e:
        print(f"Error {e}")
    return conn

def create_user_table(conn):
    """Create a table for storing users if it doesn't exist."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'viewer'
        );
        """)
        conn.commit()
        print("User table created or already exists.")
    except sqlite3.Error as e:
        print(f"Error creating users table: {e}")

def create_workspace_table(conn):
    """Create workspaces for team collaboration."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_workspace (
            user_id INTEGER,
            workspace_id INTEGER,
            role TEXT DEFAULT 'editor',
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(workspace_id) REFERENCES workspaces(id),
            PRIMARY KEY(user_id, workspace_id)
        );
        """)
        conn.commit()
        print("Workspace tables created or already exist.")
    except sqlite3.Error as e:
        print(f"Error creating workspace tables: {e}")

def create_dashboard_tables(conn):
    """Create dashboard and elements tables."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_id INTEGER,
            workspace_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(workspace_id) REFERENCES workspaces(id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_elements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dashboard_id INTEGER,
            element_type TEXT,
            element_data TEXT,
            settings_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dashboard_id) REFERENCES dashboards(id)
        );
        """)
        conn.commit()
        print("Dashboard tables created or already exist.")
    except sqlite3.Error as e:
        print(f"Error creating dashboard tables: {e}")

def create_dashboard_sharing_and_history(conn):
    """Enable dashboard sharing and history tracking."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_shares (
            dashboard_id INTEGER,
            shared_with_user_id INTEGER,
            permission TEXT DEFAULT 'view',
            FOREIGN KEY(dashboard_id) REFERENCES dashboards(id),
            FOREIGN KEY(shared_with_user_id) REFERENCES users(id),
            PRIMARY KEY(dashboard_id, shared_with_user_id)
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dashboard_id INTEGER,
            version_number INTEGER,
            snapshot TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(dashboard_id) REFERENCES dashboards(id)
        );
        """)
        conn.commit()
        print("Dashboard share/history tables created or already exist.")
    except sqlite3.Error as e:
        print(f"Error creating share/history tables: {e}")

def create_comments_table(conn):
    """Create comments table for visual discussions."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            element_id INTEGER,
            user_id INTEGER,
            comment_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(element_id) REFERENCES dashboard_elements(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
        conn.commit()
        print("Comments table created or already exists.")
    except sqlite3.Error as e:
        print(f"Error creating comments table: {e}")

def initialize_database(conn):
    create_user_table(conn)
    create_workspace_table(conn)
    create_dashboard_tables(conn)
    create_dashboard_sharing_and_history(conn)
    create_comments_table(conn)
