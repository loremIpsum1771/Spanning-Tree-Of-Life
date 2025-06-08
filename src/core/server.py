from flask import Flask, request, jsonify
import logging

# Disable the default Flask startup messages to keep our console clean
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Create the Flask application instance
app = Flask(__name__)

# --- Define Server Endpoints ---

@app.route('/sync', methods=['POST'])
def sync():
    """
    This endpoint receives a sync payload from another peer.
    For now, it just acknowledges the data and prints it.
    In future steps, we will add decryption, signature verification, and merging.
    """
    # Get the JSON data from the incoming request
    payload = request.get_json()
    
    print("\n--- [/sync] Received a P2P Sync Request ---")
    print(f"Sender: {payload.get('sender')}")
    print(f"Data received: {payload.get('data')}")
    print("-------------------------------------------\n")
    
    # Send back a success response
    # This fulfills the requirement for a POST /sync endpoint 
    return jsonify({"status": "success", "message": "Data received"}), 200


def run_server():
    """
    Runs the Flask server.
    Binds to 127.0.0.1 to ensure it's only accessible locally.
    """
    print("Starting local P2P server on http://127.0.0.1:5000...")
    # The 'debug=False' is important for a production-like environment
    app.run(host='127.0.0.1', port=5000, debug=False)
