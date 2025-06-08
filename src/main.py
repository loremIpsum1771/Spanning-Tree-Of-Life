import os
import time
import threading

from models.database import initialize_database, get_db_connection, setup_demo_data
from utils.crypto import generate_and_store_keys
from core.models import User
from core.server import run_server
from core.p2p import initiate_sync # Import our new sync function
from config import (
    ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, 
    MODELS_DIR, CORE_DIR, UTILS_DIR
)


def initialize_environment():
    # ... (no changes) ...
    print("--- Initializing Environment ---")
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR, CORE_DIR, UTILS_DIR]:
        dir_path.mkdir(exist_ok=True)
    if os.name != 'nt':
        os.chmod(KEYS_DIR, 0o700)
    generate_and_store_keys()
    initialize_database()
    print("\n--- Environment check complete ---")


def run_app():
    """
    Starts the P2P server and demonstrates a self-sync loop.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    setup_demo_data() # Ensure we have data to send
    
    # --- Start the P2P server in a background thread ---
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1) # Give the server a moment to start up
    
    # --- DEMO: Initiate a sync with our own server ---
    # This simulates a peer sending us their data.
    local_server_address = "http://127.0.0.1:5000"
    # We'll pretend to be a 'national' user for this demo sync
    current_user = User(id=50, role='national', region=None)
    
    initiate_sync(local_server_address, current_user)
    
    # --- Keep the application running ---
    print("\nMain application is running.")
    print("The P2P server is listening in the background.")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application.")


if __name__ == "__main__":
    initialize_environment()
    run_app()
