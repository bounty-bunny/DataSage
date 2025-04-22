import sqlite3

def create_connection(db_file):
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
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
            password TEXT NOT NULL
        );
        """)
        conn.commit()
        print("User table created or already exists.")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def check_user(conn, username):
    """Check if a user exists in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    return user

def add_user(conn, username, password):
    """Add a new user to the database."""
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    print(f"User {username} added successfully.")
