import os
import sqlite3
import json # Import the json library for serializing data
import time # Import time for timestamps
from pathlib import Path
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import CryptoError

# --- Configuration: (omitted for brevity, no changes) ---
PROJECT_ROOT = Path.cwd()
ACL_DIR = PROJECT_ROOT / "acl"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
KEYS_DIR = PROJECT_ROOT / "keys"
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = DATA_DIR / "spanning_tree.db"

PRIVATE_KEY_PATH = KEYS_DIR / "id_ed25519"
PUBLIC_KEY_PATH = KEYS_DIR / "id_ed25519.pub"


def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    # This line allows us to access columns by name
    conn.row_factory = sqlite3.Row
    return conn

# --- New Function: log_action ---
def log_action(action: str, performed_by: int, entity: str, record_id: int):
    """
    Creates a signed audit log for a specific action.
    This is the core of the system's traceability.
    """
    print(f"Logging action: {action} on {entity} (ID: {record_id}) by user {performed_by}")
    
    # 1. Load the private key for signing
    try:
        with open(PRIVATE_KEY_PATH, "rb") as f:
            signing_key = SigningKey(f.read())
    except (IOError, CryptoError) as e:
        print(f"Error: Could not load private key. Cannot sign action. {e}")
        return

    # 2. Construct the action payload to be signed
    # The timestamp ensures the signature is unique even if the action is repeated.
    payload = {
        "action": action,
        "performed_by": performed_by,
        "entity": entity,
        "record_id": record_id,
        "timestamp": int(time.time()) # Use a Unix timestamp
    }
    # We serialize with no spaces for a compact, consistent representation
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    # 3. Sign the JSON payload with the private key
    signed = signing_key.sign(payload_json)
    signature_hex = signed.signature.hex() # Get the signature in hex format

    # 4. Store the log in the database
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO audit_log (action, performed_by, entity, record_id, timestamp, signature)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                action,
                performed_by,
                entity,
                record_id,
                payload["timestamp"],
                signature_hex
            )
        )
        conn.commit()
        print("Action successfully logged and signed.")
    except sqlite3.Error as e:
        print(f"Database error while logging action: {e}")
    finally:
        conn.close()

# --- (Other functions like initialize_database, generate_and_store_keys are unchanged) ---
def initialize_database():
    print("Initializing database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
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
        cursor.execute(create_users_table)
        cursor.execute(create_audit_log_table)
        conn.commit()
        conn.close()
        print(f"Database initialized successfully at: {DB_PATH}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")

def generate_and_store_keys():
    if PRIVATE_KEY_PATH.exists():
        print("Key pair already exists. Loading public key.")
    else:
        print("Generating new Ed25519 key pair...")
        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key
        with open(PRIVATE_KEY_PATH, "wb") as f: f.write(signing_key.encode())
        with open(PUBLIC_KEY_PATH, "wb") as f: f.write(verify_key.encode())
        if os.name != 'nt':
            os.chmod(PRIVATE_KEY_PATH, 0o600)
            os.chmod(PUBLIC_KEY_PATH, 0o600)
        print(f"Private key saved to: {PRIVATE_KEY_PATH}")
        print(f"Public key saved to: {PUBLIC_KEY_PATH}")
    with open(PUBLIC_KEY_PATH, "rb") as f:
        public_key_bytes = f.read()
    print(f"Node Public Key (hex): {public_key_bytes.hex()}")

def initialize_environment():
    print("Initializing environment...")
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR]:
        dir_path.mkdir(exist_ok=True)
    if os.name != 'nt': os.chmod(KEYS_DIR, 0o700)
    generate_and_store_keys()
    initialize_database()
    print("\nEnvironment check complete.")

# --- Updated run_app to demonstrate logging ---
def run_app():
    """
    Main application logic. Now includes a demo of the audit log.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    
    # --- DEMO: Log a sample action ---
    # In a real app, the user ID would come from the logged-in user.
    # We'll pretend the user with ID=1 is performing an action.
    print("\n--- Running Audit Log Demo ---")
    # Let's imagine user 1 just created a new user with ID 55
    log_action(action="create", performed_by=1, entity="users", record_id=55)


if __name__ == "__main__":
    initialize_environment()
    run_app()
