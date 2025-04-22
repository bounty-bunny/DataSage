import sqlite3

def create_connection(db_file):
    conn = sqlite3.connect(db_file)
    return conn

def create_user_table(conn):
    # SQL statement to create user table
    pass

def check_user(conn, username):
    # Function to check if user exists
    pass

def add_user(conn, username, password):
    # Function to add a new user to the database
    pass
