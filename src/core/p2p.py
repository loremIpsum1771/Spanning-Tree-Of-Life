import json
import requests
import time
from nacl.signing import SigningKey
from nacl.exceptions import CryptoError

# Import the has_access function for filtering
from acl.permissions import has_access
from config import PRIVATE_KEY_PATH
from core.models import User
from models.database import get_db_connection

def gather_changed_records(last_sync_timestamp: int) -> list:
    """
    Gathers records from the database that have changed since the last sync.
    """
    print(f"Gathering records modified since timestamp {last_sync_timestamp}...")
    conn = get_db_connection()
    meetings = conn.execute("SELECT * FROM meetings").fetchall()
    conn.close()
    
    # Convert records to a list of dictionaries
    return [dict(row) for row in meetings]

def initiate_sync(peer_address: str, current_user: User, peer_user: User):
    """
    Prepares a filtered, signed payload and sends it to a peer.
    """
    print(f"\n--- Initiating Sync with Peer '{peer_user.role}' at {peer_address} ---")
    
    all_records = gather_changed_records(0)
    print(f"Found {len(all_records)} total records to consider for sync.")
    
    records_to_send = [
        record for record in all_records if has_access(peer_user, record)
    ]
    print(f"Applying ACLs. Sending {len(records_to_send)} records to peer.")
    
    payload = {
        "sender_id": current_user.id,
        "records": records_to_send,
        "timestamp": int(time.time())
    }
    
    try:
        with open(PRIVATE_KEY_PATH, "rb") as f:
            # Load the private key into the SigningKey object
            signing_key = SigningKey(f.read())
        
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        
        # Sign the message
        signed_message = signing_key.sign(payload_json)
        
        # --- This is the corrected section ---
        # Get the public verify_key FROM the signing_key object
        verify_key = signing_key.verify_key
        # Encode the public key to hex to be sent in the payload
        public_key_hex = verify_key.encode().hex()
        # --- End of corrected section ---

        final_payload = {
            "data": payload,
            "signature": signed_message.signature.hex(),
            "public_key": public_key_hex # Use the correctly retrieved public key
        }
        
    except (IOError, CryptoError) as e:
        print(f"Error: Could not load private key to sign payload. {e}")
        return

    try:
        response = requests.post(
            f"{peer_address}/sync",
            json=final_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("Sync request successfully sent and acknowledged by peer.")
            print(f"Peer response: {response.json()}")
        else:
            print(f"Peer responded with an error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to peer at {peer_address}. They might be offline.")
        print(f"Error: {e}")
