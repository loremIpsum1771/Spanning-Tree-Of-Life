# ... (imports are unchanged) ...
from models.database import initialize_database, setup_demo_data
from utils.crypto import generate_and_store_keys
from core.models import User
from core.server import run_server
from core.p2p import initiate_sync
import os
import time
import threading

def initialize_environment():
    # ... (This function is unchanged) ...
    print("--- Initializing Environment ---")
    for dir_path in [os.path.join(os.getcwd(), d) for d in ["acl", "config", "data", "keys", "models", "core", "utils"]]:
        os.makedirs(dir_path, exist_ok=True)
    if os.name != 'nt':
        os.chmod(os.path.join(os.getcwd(), "keys"), 0o700)
    generate_and_store_keys()
    initialize_database()
    print("\n--- Environment check complete ---")


def run_app():
    """
    Demonstrates a secure sync with ACL filtering and signature verification.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    setup_demo_data()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)
    
    # --- DEMO: A facilitator in NYC syncs with a municipal lead in NYC ---
    # In our self-sync, these are the same person, but it demonstrates the logic.
    
    # The user initiating the sync
    current_user = User(id=20, role='facilitator', region='nyc')
    
    # The user profile of the peer we are sending data to
    peer_user = User(id=30, role='municipal', region='nyc')
    
    local_server_address = "http://127.0.0.1:5000"
    
    # Initiate the sync, passing both user profiles
    initiate_sync(local_server_address, current_user, peer_user)
    
    print("\nMain application is running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application.")


if __name__ == "__main__":
    initialize_environment()
    run_app()
