import json
import requests
import time
from nacl.public import PrivateKey, Box
from nacl.signing import SigningKey
from nacl.exceptions import CryptoError

from acl.permissions import has_access
from config import PRIVATE_KEY_PATH, PUBLIC_KEY_PATH
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
    
    return [dict(row) for row in meetings]

def initiate_sync(peer_address: str, current_user: User, peer_user: User):
    """
    Prepares a filtered, signed, and ENCRYPTED payload and sends it to a peer.
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
            signing_key = SigningKey(f.read())
        
        payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        signed_message = signing_key.sign(payload_json)
        verify_key = signing_key.verify_key
        public_key_hex = verify_key.encode().hex()

        final_payload = {
            "data": payload,
            "signature": signed_message.signature.hex(),
            "public_key": public_key_hex
        }
        
        # --- New Encryption Step ---
        print("Encrypting payload for secure transport...")
        # A signing key can be converted into a key for encryption (Curve25519)
        encryption_private_key = signing_key.to_curve25519_private_key()
        
        # For the demo, we use our own public key as the peer's public key
        with open(PUBLIC_KEY_PATH, "rb") as f:
            peer_public_key_bytes = f.read()
        
        # The signing VerifyKey needs to be converted to an encryption PublicKey
        peer_encryption_public_key = VerifyKey(peer_public_key_bytes).to_curve25519_public_key()
        
        # Create a "Box" for encryption
        box = Box(encryption_private_key, peer_encryption_public_key)
        
        # The payload to encrypt is the JSON string of our final_payload dict
        final_payload_json = json.dumps(final_payload).encode('utf-8')
        
        encrypted_payload = box.encrypt(final_payload_json)
        # --- End of Encryption Step ---
        
    except (IOError, CryptoError) as e:
        print(f"Error: Could not process keys for encryption/signing. {e}")
        return

    try:
        print("Sending encrypted payload to peer...")
        # We now send the raw encrypted bytes, not JSON
        response = requests.post(
            f"{peer_address}/sync",
            data=encrypted_payload, # Send raw bytes
            headers={"Content-Type": "application/octet-stream"}, # Change content type
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
