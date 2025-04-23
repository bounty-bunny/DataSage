import sqlite3

def create_connection(db_file):
    """Create a database connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")  # Ensure foreign key constraints
        print(f"[DB] Connected to {db_file} successfully")
        return conn
    except sqlite3.Error as e:
        print(f"[DB ERROR] Connection failed: {e}")
        return None

def execute_query(conn, query, description):
    """Utility to execute a SQL query with basic error logging."""
    try:
        cursor = conn.cursor()
        cursor.executescript(query)
        conn.commit()
        print(f"[DB] {description} - Success")
    except sqlite3.Error as e:
        print(f"[DB ERROR] {description} - {e}")

def check_user(conn, username, password):
    """Check if a user exists with the given username and password."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error checking user: {e}")
        return None

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
    execute_query(conn, query, "Workspace tables creation")

def create_dashboard_tables(conn):
    query = """
    CREATE TABLE IF NOT EXISTS dashboards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        user_id INTEGER,
        workspace_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
    );

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
    execute_query(conn, query, "Dashboard and elements tables creation")

def create_dashboard_sharing_and_history(conn):
    query = """
    CREATE TABLE IF NOT EXISTS dashboard_shares (
        dashboard_id INTEGER,
        shared_with_user_id INTEGER,
        permission TEXT DEFAULT 'view',
        PRIMARY KEY(dashboard_id, shared_with_user_id),
        FOREIGN KEY(dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE,
        FOREIGN KEY(shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS dashboard_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dashboard_id INTEGER,
        version_number INTEGER,
        snapshot TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
    );
    """
    execute_query(conn, query, "Sharing & history tables creation")

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

def initialize_database(conn):
    print("[DB INIT] Initializing all required tables...")
    create_user_table(conn)
    create_workspace_table(conn)
    create_dashboard_tables(conn)
    create_dashboard_sharing_and_history(conn)
    create_comments_table(conn)
    print("[DB INIT] Initialization complete.")
