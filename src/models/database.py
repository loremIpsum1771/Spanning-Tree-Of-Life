import sqlite3
from config import DB_PATH

# Imports needed for the find_records function
from core.models import User
from acl.permissions import get_acl_filter_clause


def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    # This line allows us to access columns by name (e.g., results['title'])
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """
    Connects to the database and creates all necessary tables if they don't exist.
    """
    print("Initializing database...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Defines the schema for the 'users' table
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            public_key TEXT NOT NULL,
            role TEXT CHECK(role IN ('connector', 'shadower', 'facilitator', 'municipal', 'statal', 'national', 'dev')),
            region TEXT,
            cc_score INTEGER DEFAULT 0,
            last_active TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        """

        # Defines the schema for the 'audit_log' table
        create_audit_log_table = """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY,
            action TEXT,
            performed_by INTEGER REFERENCES users(id),
            record_id INTEGER,
            entity TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            signature TEXT
        );
        """
        
        # Defines the schema for the 'meetings' table, including the last_modified column for syncing
        create_meetings_table = """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY,
            host_id INTEGER REFERENCES users(id),
            city TEXT,
            state TEXT,
            scheduled_at TIMESTAMP,
            title TEXT,
            notes TEXT,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Execute the SQL commands to create the tables
        cursor.execute(create_users_table)
        cursor.execute(create_audit_log_table)
        cursor.execute(create_meetings_table)
        
        conn.commit()
        conn.close()
        print(f"Database ready at: {DB_PATH}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")


def find_records(table_name: str, user: User) -> list:
    """
    Finds records from a table, automatically applying ACL filtering by generating
    a dynamic WHERE clause based on the user's role.
    """
    clause, params = get_acl_filter_clause(user)
    
    # Construct the final, safe, parameterized query
    sql = f"SELECT * FROM {table_name} WHERE {clause}"
    
    print(f"\nExecuting query for user '{user.role}' in '{user.region}':")
    print(f"SQL: {sql}")
    print(f"Params: {params}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    
    # Convert results from sqlite3.Row objects to a list of standard dictionaries
    return [dict(row) for row in results]
