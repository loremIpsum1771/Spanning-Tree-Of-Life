import json
import logging
from flask import Flask, request, jsonify, redirect
from nacl.public import PrivateKey, Box
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError, CryptoError

from models.database import merge_records
from core.cta import CtaManager # Import the new manager
from config import PRIVATE_KEY_PATH, PUBLIC_KEY_PATH

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/sync', methods=['POST'])
def sync():
    """
    Receives an encrypted sync payload, decrypts it, verifies the signature,
    and merges the data.
    """
    # Get the raw encrypted bytes from the request
    encrypted_payload = request.get_data()
    
    # 1. Decrypt the payload
    try:
        print("\n--- [/sync] Received encrypted payload, attempting decryption... ---")
        # Load our own private key for decryption
        with open(PRIVATE_KEY_PATH, "rb") as f:
            server_signing_key = SigningKey(f.read())
        server_private_key = server_signing_key.to_curve25519_private_key()
        
        # For the demo, we assume we know the sender's public key (our own)
        with open(PUBLIC_KEY_PATH, "rb") as f:
            sender_public_key_bytes = f.read()
        sender_encryption_public_key = VerifyKey(sender_public_key_bytes).to_curve25519_public_key()

        # Create the Box to decrypt the message
        box = Box(server_private_key, sender_encryption_public_key)
        
        # The decrypt() method will raise CryptoError if decryption fails
        decrypted_payload_json = box.decrypt(encrypted_payload)
        payload = json.loads(decrypted_payload_json)
        print("Decryption successful.")

    except (CryptoError, json.JSONDecodeError, IOError):
        print("--- [/sync] DECRYPTION FAILED. Rejecting request. ---")
        return jsonify({"status": "error", "message": "Decryption failed or invalid payload"}), 403

    # 2. Verify the signature (on the now-decrypted payload)
    data = payload.get('data')
    signature_hex = payload.get('signature')
    public_key_hex = payload.get('public_key')
    
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key_hex))
        data_json = json.dumps(data, separators=(',', ':')).encode('utf-8')
        verify_key.verify(data_json, bytes.fromhex(signature_hex))
        print("--- [/sync] Signature VERIFIED. Request is authentic. ---")
    except (BadSignatureError, TypeError, KeyError, ValueError):
        print("--- [/sync] Signature INVALID. Rejecting request. ---")
        return jsonify({"status": "error", "message": "Invalid signature"}), 403

    # 3. If verification passes, process the data using the merge function
    records_to_merge = data.get('records', [])
    print(f"Received {len(records_to_merge)} records to merge.")
    merge_summary = merge_records(records_to_merge)
    print("----------------------------------------------------\n")
    
    return jsonify({
        "status": "success", 
        "message": "Data decrypted, verified, and merged",
        "summary": merge_summary
    }), 200

# --- New Endpoint for CTA Tracking ---
@app.route('/cta/<token>', methods=['GET'])
def track_cta_click(token: str):
    """
    This endpoint is hit when a user clicks a CTA link in an email.
    It logs the click and then redirects the user to the original destination.
    """
    cta_manager.track_click(token)
    # For a real user experience, you could fetch the original cta_link
    # from the database and redirect them. For now, we show a simple message.
    return "Thank you for your response! Your click has been recorded."
    
def run_server():
    """
    Runs the Flask server on a local-only address.
    """
    print("Starting local P2P server on http://127.0.0.1:5000...")
    app.run(host='127.0.0.1', port=5000, debug=False)
