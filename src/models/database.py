import sqlite3
from config import DB_PATH
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
        
        create_invitations_table = """
        CREATE TABLE IF NOT EXISTS invitations (
            id INTEGER PRIMARY KEY,
            email TEXT NOT NULL,
            invited_by INTEGER REFERENCES users(id),
            used BOOLEAN DEFAULT 0,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_signups_table = """
        CREATE TABLE IF NOT EXISTS signups (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            invited_by INTEGER REFERENCES users(id),
            city TEXT,
            state TEXT,
            zip TEXT,
            neighborhood TEXT,
            occupation TEXT,
            token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_email_log_table = """
        CREATE TABLE IF NOT EXISTS email_log (
            id INTEGER PRIMARY KEY,
            sender_id INTEGER REFERENCES users(id),
            recipient_id INTEGER REFERENCES users(id),
            subject TEXT,
            cta_link TEXT,
            token TEXT UNIQUE NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            responded_at TIMESTAMP
        );
        """

        # Execute the SQL commands to create the tables
        cursor.execute(create_users_table)
        cursor.execute(create_audit_log_table)
        cursor.execute(create_meetings_table)
        cursor.execute(create_invitations_table)
        cursor.execute(create_signups_table)
        cursor.execute(create_email_log_table)
        
        conn.commit()
        conn.close()
        print(f"Database ready at: {DB_PATH}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")


def find_records(table_name: str, user: User) -> list:
    """
    Finds records from a table, automatically applying ACL filtering.
    """
    # The table_name is now passed to the ACL function
    clause, params = get_acl_filter_clause(user, table_name)
    
    sql = f"SELECT * FROM {table_name} WHERE {clause}"
    
    print(f"\nExecuting query for user '{user.role}' in '{user.region}':")
    print(f"SQL: {sql}")
    print(f"Params: {params}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]


def setup_demo_data():
    """Inserts or resets sample data in the database for demos."""
    print("Setting up demo data...")
    conn = get_db_connection()

    # Setup meetings data
    meetings = [
        (20, 'nyc', 'ny', 'Meeting A in NYC'),
        (21, 'nyc', 'ny', 'Meeting B in NYC'),
        (40, 'albany', 'ny', 'Meeting C in Albany'),
        (41, 'sf', 'ca', 'Meeting D in SF')
    ]
    conn.execute("DELETE FROM meetings")
    conn.executemany("INSERT INTO meetings (host_id, city, state, title) VALUES (?, ?, ?, ?)", meetings)
    
    # Setup users data
    users = [
        (10, 'shadower@example.com', 'key1', 'shadower', 'nyc'),
        (20, 'facilitator@example.com', 'key2', 'facilitator', 'nyc'),
        (30, 'municipal@example.com', 'key3', 'municipal', 'nyc')
    ]
    conn.execute("DELETE FROM users")
    conn.executemany("INSERT INTO users (id, email, public_key, role, region) VALUES (?, ?, ?, ?, ?)", users)

    conn.commit()
    conn.close()
    print("Demo data has been set up.")


def merge_records(records: list) -> dict:
    """
    Merges a list of incoming records into the local database.
    - Inserts new records.
    - Updates existing records if the incoming one is newer.
    - Skips existing records if the incoming one is older or the same.
    """
    summary = {'inserted': 0, 'updated': 0, 'skipped': 0}
    
    # For now, we only handle the 'meetings' table. A full implementation
    # would check the record type and dispatch to the correct table handler.
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for record in records:
        record_id = record.get('id')
        if not record_id:
            continue

        # Check if a record with this ID already exists
        cursor.execute("SELECT last_modified FROM meetings WHERE id = ?", (record_id,))
        local_record = cursor.fetchone()
        
        if local_record is None:
            # Record does not exist locally, so insert it
            print(f"Merging: Inserting new meeting with ID {record_id}.")
            cursor.execute(
                "INSERT INTO meetings (id, host_id, city, state, title, notes, last_modified) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record_id, record.get('host_id'), record.get('city'), record.get('state'), record.get('title'), record.get('notes'), record.get('last_modified'))
            )
            summary['inserted'] += 1
        else:
            # Record exists, compare timestamps
            local_timestamp = local_record['last_modified']
            incoming_timestamp = record.get('last_modified')

            if incoming_timestamp and local_timestamp and incoming_timestamp > local_timestamp:
                # Incoming record is newer, so update
                print(f"Merging: Updating existing meeting with ID {record_id}.")
                cursor.execute(
                    "UPDATE meetings SET host_id = ?, city = ?, state = ?, title = ?, notes = ?, last_modified = ? WHERE id = ?",
                    (record.get('host_id'), record.get('city'), record.get('state'), record.get('title'), record.get('notes'), incoming_timestamp, record_id)
                )
                summary['updated'] += 1
            else:
                # Local record is same age or newer, so skip
                print(f"Merging: Skipping meeting with ID {record_id} (local is newer or timestamp missing).")
                summary['skipped'] += 1

    conn.commit()
    conn.close()
    
    return summary
