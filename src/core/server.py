from flask import Flask, request, jsonify
import logging
import json
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/sync', methods=['POST'])
def sync():
    """
    Receives a sync payload, verifies its signature, and processes the data.
    """
    payload = request.get_json()
    
    # Separate the data, signature, and public key from the payload
    data = payload.get('data')
    signature_hex = payload.get('signature')
    public_key_hex = payload.get('public_key')
    
    # 1. Verify the signature 
    try:
        # Recreate the VerifyKey from the hex-encoded public key
        verify_key = VerifyKey(bytes.fromhex(public_key_hex))
        
        # Re-serialize the data exactly as the client did to check the signature
        data_json = json.dumps(data, separators=(',', ':')).encode('utf-8')
        
        # The verify() method will raise BadSignatureError if the signature is invalid
        verify_key.verify(data_json, bytes.fromhex(signature_hex))
        
        print("\n--- [/sync] Signature VERIFIED. Request is authentic. ---")
        
    except (BadSignatureError, TypeError, KeyError):
        # If signature is bad or payload is malformed, reject it.
        print("\n--- [/sync] Signature INVALID. Rejecting request. ---")
        return jsonify({"status": "error", "message": "Invalid signature or malformed payload"}), 403

    # 2. Process the data (if signature was valid)
    print(f"Sender ID: {data.get('sender_id')}")
    print(f"Received {len(data.get('records', []))} records.")
    print("----------------------------------------------------\n")
    
    # TODO: In our next step, we will add the merge logic here.
    
    return jsonify({"status": "success", "message": "Data received and verified"}), 200

def run_server():
    # ... (This function is unchanged) ...
    print("Starting local P2P server on http://127.0.0.1:5000...")
    app.run(host='127.0.0.1', port=5000, debug=False)
