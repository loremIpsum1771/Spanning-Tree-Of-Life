import json
import requests
import time
from nacl.signing import SigningKey
from nacl.exceptions import CryptoError

from config import PRIVATE_KEY_PATH
from core.models import User
from models.database import get_db_connection

def gather_changed_records(last_sync_timestamp: int) -> list:
    """
    Gathers records from the database that have changed since the last sync.
    
    For this demo, we will just fetch all meetings. A full implementation
    would query all syncable tables based on the 'last_modified' column.
    """
    print(f"Gathering records modified since timestamp {last_sync_timestamp}...")
    conn = get_db_connection()
    # Demo query: just get all meetings
    meetings = conn.execute("SELECT * FROM meetings").fetchall()
    conn.close()
    
    # Convert records to a list of dictionaries
    return [dict(row) for row in meetings]

def initiate_sync(peer_address: str, user: User):
    """
    Prepares and sends a sync payload to a specified peer.
    """
    print(f"\n--- Initiating Sync with Peer at {peer_address} ---")
    
    # 1. Gather records that have changed.
    # We'll use 0 as the timestamp to get all records for this demo.
    records_to_send = gather_changed_records(0)
    
    # TODO: In a future step, we will filter `records_to_send` using the ACLs.
    # TODO: In a future step, we will encrypt the payload.
    
    # 2. Construct the payload 
    payload = {
        "sender": user.id, # In a real system, this would be the user's email or public key
        "records": records_to_send,
        "timestamp": int(time.time())
    }
    
    # 3. Sign the payload 
    try:
        with open(PRIVATE_KEY_PATH, "rb") as f:
            signing_key = SigningKey(f.read())
        
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signed = signing_key.sign(payload_json)
        signature_hex = signed.signature.hex()
        
        # Add the signature to the payload to be sent
        final_payload = {
            "data": payload,
            "signature": signature_hex
        }
        
    except (IOError, CryptoError) as e:
        print(f"Error: Could not load private key to sign payload. {e}")
        return

    # 4. Send the request to the peer's /sync endpoint
    try:
        response = requests.post(
            f"{peer_address}/sync",
            json=final_payload,
            headers={"Content-Type": "application/json"},
            timeout=10 # seconds
        )
        
        if response.status_code == 200:
            print("Sync request successfully sent and acknowledged by peer.")
            print(f"Peer response: {response.json()}")
        else:
            print(f"Peer responded with an error: {response.status_code} - {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to peer at {peer_address}. They might be offline.")
        print(f"Error: {e}")
