import json
import requests
import time
from nacl.public import PrivateKey, Box
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import CryptoError

from acl.permissions import has_access
from config import PRIVATE_KEY_PATH, PUBLIC_KEY_PATH
from core.models import User, Peer
from models.database import get_db_connection

def gather_changed_records(last_sync_timestamp: int) -> list:
    """Gathers records from the database that have changed since the last sync."""
    # ... (This function is unchanged) ...
    print(f"Gathering records modified since timestamp {last_sync_timestamp}...")
    conn = get_db_connection()
    meetings = conn.execute("SELECT * FROM meetings").fetchall()
    conn.close()
    return [dict(row) for row in meetings]

# The function signature is now cleaner
def initiate_sync(current_user: User, peer: Peer):
    """Prepares and sends a filtered, signed, and encrypted payload to a peer."""
    print(f"\n--- Initiating Sync with Peer '{peer.email}' at {peer.address} ---")
    
    # We create a User object for the peer to perform ACL checks
    peer_user_profile = User(id=0, role='dev', region=None) # A placeholder profile
    # A full implementation would need to sync user profiles as well.
    # For now, we grant the peer 'dev' access for the purpose of the demo.

    all_records = gather_changed_records(peer.last_synced or 0)
    print(f"Found {len(all_records)} total records to consider for sync.")
    
    records_to_send = [
        record for record in all_records if has_access(peer_user_profile, record)
    ]
    print(f"Applying ACLs. Sending {len(records_to_send)} records to peer.")
    
    payload = {
        "sender_id": current_user.id,
        "records": records_to_send,
        "timestamp": int(time.time())
    }
    
    try:
        with open(PRIVATE_KEY_PATH, "rb") as f:
            signing_key = SigningKey(f.read())
        
        # ... (Signature logic is unchanged) ...
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signed_message = signing_key.sign(payload_json)
        verify_key = signing_key.verify_key
        public_key_hex = verify_key.encode().hex()

        final_payload = {
            "data": payload,
            "signature": signed_message.signature.hex(),
            "public_key": public_key_hex
        }
        
        # --- Encryption Step ---
        print("Encrypting payload for secure transport...")
        encryption_private_key = signing_key.to_curve25519_private_key()
        
        # Get the peer's public key from the Peer object
        peer_encryption_public_key = VerifyKey(bytes.fromhex(peer.public_key)).to_curve25519_public_key()
        
        box = Box(encryption_private_key, peer_encryption_public_key)
        final_payload_json = json.dumps(final_payload).encode('utf-8')
        encrypted_payload = box.encrypt(final_payload_json)
        
    except (IOError, CryptoError) as e:
        print(f"Error: Could not process keys for encryption/signing. {e}")
        return

    try:
        print("Sending encrypted payload to peer...")
        response = requests.post(
            f"{peer.address}/sync", # Use the peer's address from the Peer object
            data=encrypted_payload,
            headers={"Content-Type": "application/octet-stream"},
            timeout=10
        )
        if response.status_code == 200:
            print("Sync request successfully sent and acknowledged by peer.")
            print(f"Peer response: {response.json()}")
            return True # Return True on success
        else:
            print(f"Peer responded with an error: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to peer at {peer.address}. They might be offline.")
    
    return False # Return False on failure
