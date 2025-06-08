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
    # ... (This function is unchanged) ...
    print(f"Gathering records modified since timestamp {last_sync_timestamp}...")
    conn = get_db_connection()
    meetings = conn.execute("SELECT * FROM meetings").fetchall()
    conn.close()
    return [dict(row) for row in meetings]

# The function now accepts the peer's user object to check their permissions
def initiate_sync(peer_address: str, current_user: User, peer_user: User):
    """
    Prepares a filtered, signed payload and sends it to a peer.
    """
    print(f"\n--- Initiating Sync with Peer '{peer_user.role}' at {peer_address} ---")
    
    # 1. Gather all potentially changed records
    all_records = gather_changed_records(0)
    print(f"Found {len(all_records)} total records to consider for sync.")
    
    # 2. Filter records based on the PEER's permissions
    # This implements the ACL filtering requirement 
    records_to_send = [
        record for record in all_records if has_access(peer_user, record)
    ]
    print(f"Applying ACLs. Sending {len(records_to_send)} records to peer.")
    
    # 3. Construct the payload
    payload = {
        "sender_id": current_user.id,
        "records": records_to_send,
        "timestamp": int(time.time())
    }
    
    # 4. Sign the payload
    # ... (This logic is unchanged) ...
    try:
        with open(PRIVATE_KEY_PATH, "rb") as f:
            signing_key = SigningKey(f.read())
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signed = signing_key.sign(payload_json)
        # We now send the public key so the peer can verify the signature
        final_payload = {
            "data": payload,
            "signature": signed.signature.hex(),
            "public_key": signed.verify_key.encode().hex()
        }
    except (IOError, CryptoError) as e:
        print(f"Error: Could not load private key to sign payload. {e}")
        return

    # 5. Send the request
    # ... (This logic is unchanged) ...
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
