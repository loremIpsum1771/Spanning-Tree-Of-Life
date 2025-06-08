import sqlite3
from config import DB_PATH

def get_db_connection():
    # ... (no changes) ...
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_database():
    """Connects to the DB and creates tables if they don't exist."""
    print("Initializing database...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # ... (create_users_table and create_audit_log_table are unchanged) ...
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, public_key TEXT NOT NULL,
            role TEXT CHECK(role IN ('connector', 'shadower', 'facilitator', 'municipal', 'statal', 'national', 'dev')),
            region TEXT, cc_score INTEGER DEFAULT 0, last_active TIMESTAMP, is_active BOOLEAN DEFAULT 1
        );
        """
        create_audit_log_table = """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY, action TEXT, performed_by INTEGER REFERENCES users(id),
            record_id INTEGER, entity TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, signature TEXT
        );
        """
        
        # --- New Table ---
        # meetings table schema from the document 
        create_meetings_table = """
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY,
            host_id INTEGER REFERENCES users(id),
            city TEXT,
            state TEXT,
            scheduled_at TIMESTAMP,
            title TEXT,
            notes TEXT
        );
        """

        cursor.execute(create_users_table)
        cursor.execute(create_audit_log_table)
        cursor.execute(create_meetings_table) # Execute the new table creation
        
        conn.commit()
        conn.close()
        print(f"Database ready at: {DB_PATH}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
