import os
import sqlite3 # Import the sqlite3 library
from pathlib import Path
from nacl.signing import SigningKey
from nacl.exceptions import CryptoError

# --- Configuration: Define all application paths ---
PROJECT_ROOT = Path.cwd()
ACL_DIR = PROJECT_ROOT / "acl"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
KEYS_DIR = PROJECT_ROOT / "keys"
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = DATA_DIR / "spanning_tree.db" # The path for the embedded SQLite database

PRIVATE_KEY_PATH = KEYS_DIR / "id_ed25519"
PUBLIC_KEY_PATH = KEYS_DIR / "id_ed25519.pub"


def initialize_database():
    """
    Connects to the SQLite database, creating it if it doesn't exist,
    and sets up the necessary tables.
    """
    print("Initializing database...")
    try:
        # connect() will create the database file if it doesn't exist.
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # --- Define SQL for creating tables ---
        # Using "IF NOT EXISTS" makes the script safe to re-run.

        # users table schema from the document 
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

        # audit_log table schema from the document 
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

        # Execute the SQL commands
        cursor.execute(create_users_table)
        cursor.execute(create_audit_log_table)

        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        print(f"Database initialized successfully at: {DB_PATH}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")


def generate_and_store_keys():
    """
    Generates an Ed25519 key pair if it doesn't already exist and stores it securely.
    """
    if PRIVATE_KEY_PATH.exists():
        print("Key pair already exists. Loading public key.")
    else:
        print("Generating new Ed25519 key pair...")
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(signing_key.encode())
        with open(PUBLIC_KEY_PATH, "wb") as f:
            f.write(verify_key.encode())
        if os.name != 'nt':
            os.chmod(PRIVATE_KEY_PATH, 0o600)
            os.chmod(PUBLIC_KEY_PATH, 0o600)
        print(f"Private key saved to: {PRIVATE_KEY_PATH}")
        print(f"Public key saved to: {PUBLIC_KEY_PATH}")
    with open(PUBLIC_KEY_PATH, "rb") as f:
        public_key_bytes = f.read()
    print(f"Node Public Key (hex): {public_key_bytes.hex()}")


def initialize_environment():
    """
    Ensures all necessary directories exist and sets up the environment.
    """
    print("Initializing environment...")
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR]:
        dir_path.mkdir(exist_ok=True)
    if os.name != 'nt':
        os.chmod(KEYS_DIR, 0o700)

    generate_and_store_keys()
    
    # --- New step ---
    initialize_database()
    # ----------------

    print("\nEnvironment check complete.")


def run_app():
    """
    The main application logic will eventually go here.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")


if __name__ == "__main__":
    initialize_environment()
    run_app()
