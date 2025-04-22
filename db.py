import sqlite3
from sqlite3 import Error

# Function to create a database connection
def create_connection(db_file):
    """Create a database connection to the SQLite database"""
    conn = None
    try:
        # Create a connection to the database file
        conn = sqlite3.connect(db_file)
        print(f"Connection to {db_file} established!")
    except Error as e:
        print(f"Error: {e}")
    return conn

# Function to create the users table if it does not exist
def create_user_table(conn):
    """Create a table for storing users if it does not exist"""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Error: {e}")

# Function to check if a user exists by username
def check_user(conn, username):
    """Check if the user exists in the database"""
    if conn is None:
        print("Connection is None, cannot check user.")
        return None

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    return user  # Returns None if no user is found, else returns the user row

# Function to add a new user to the database
def add_user(conn, username, password):
    """Add a new user to the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print(f"User {username} added successfully!")
    except Error as e:
        print(f"Error: {e}")

# Function to close the database connection
def close_connection(conn):
    """Close the database connection"""
    if conn:
        conn.close()
        print("Database connection closed.")
