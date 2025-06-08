import json
import time
import sqlite3
from nacl.signing import SigningKey
from nacl.exceptions import CryptoError
from config import PRIVATE_KEY_PATH
from models.database import get_db_connection

def log_action(action: str, performed_by: int, entity: str, record_id: int):
    """Creates a signed audit log for a specific action."""
    print(f"Logging action: {action} on {entity} (ID: {record_id}) by user {performed_by}")
    
    try:
        with open(PRIVATE_KEY_PATH, "rb") as f:
            signing_key = SigningKey(f.read())
    except (IOError, CryptoError) as e:
        print(f"Error: Could not load private key. Cannot sign action. {e}")
        return

    payload = {
        "action": action,
        "performed_by": performed_by,
        "entity": entity,
        "record_id": record_id,
        "timestamp": int(time.time())
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    signed = signing_key.sign(payload_json)
    signature_hex = signed.signature.hex()

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_log (action, performed_by, entity, record_id, timestamp, signature) VALUES (?, ?, ?, ?, ?, ?)",
            (action, performed_by, entity, record_id, payload["timestamp"], signature_hex)
        )
        conn.commit()
        print("Action successfully logged and signed.")
    except sqlite3.Error as e:
        print(f"Database error while logging action: {e}")
    finally:
        conn.close()
