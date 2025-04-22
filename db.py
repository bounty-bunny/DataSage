import sqlite3

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def create_user_table(conn):
    # SQL to create the user table
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    conn.commit()

def check_user(conn, username):
    # Check if the user already exists in the database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    return user  # Returns None if no user is found, else returns the user row

def add_user(conn, username, password):
    # Add a new user to the database
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
