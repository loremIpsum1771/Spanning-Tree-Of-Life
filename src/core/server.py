import json
import logging
from flask import Flask, request, jsonify
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# Import the merge logic from our database module
from models.database import merge_records

# This quiets the default Flask server logging to keep our console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create the Flask application instance
app = Flask(__name__)


# --- Define Server Endpoints ---

@app.route('/sync', methods=['POST'])
def sync():
    """
    This endpoint receives a sync payload from another peer. It is responsible for:
    1. Verifying the cryptographic signature to ensure the request is authentic.
    2. Passing the verified data to the merge logic to be saved.
    3. Returning a summary of the operation to the peer.
    """
    payload = request.get_json()
    
    # Separate the data, signature, and public key from the incoming payload
    data = payload.get('data')
    signature_hex = payload.get('signature')
    public_key_hex = payload.get('public_key')
    
    # 1. Verify the signature
    try:
        # Recreate the peer's VerifyKey from their hex-encoded public key
        verify_key = VerifyKey(bytes.fromhex(public_key_hex))
        
        # Re-serialize the data exactly as the client did to prepare for verification
        data_json = json.dumps(data, separators=(',', ':')).encode('utf-8')
        
        # The verify() method cryptographically checks the signature.
        # It will raise a BadSignatureError if the signature does not match the data.
        verify_key.verify(data_json, bytes.fromhex(signature_hex))
        
        print("\n--- [/sync] Signature VERIFIED. Request is authentic. ---")
        
    except (BadSignatureError, TypeError, KeyError, ValueError):
        # If signature is bad, or the payload is malformed/missing keys, reject it.
        print("\n--- [/sync] Signature INVALID. Rejecting request. ---")
        return jsonify({"status": "error", "message": "Invalid signature or malformed payload"}), 403

    # 2. If verification passes, process the data using the merge function
    records_to_merge = data.get('records', [])
    print(f"Received {len(records_to_merge)} records to merge.")
    
    merge_summary = merge_records(records_to_merge)
    
    print("----------------------------------------------------\n")
    
    # 3. Return a success response including the summary of the merge operation
    return jsonify({
        "status": "success", 
        "message": "Data received and verified",
        "summary": merge_summary
    }), 200


def run_server():
    """
    Runs the Flask server on a local-only address.
    """
    print("Starting local P2P server on http://127.0.0.1:5000...")
    # debug=False is important for stability and performance
    app.run(host='127.0.0.1', port=5000, debug=False)
