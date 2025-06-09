import os
import time
import threading

from models.database import initialize_database, setup_demo_data
from utils.crypto import generate_and_store_keys
from core.models import User, Peer
from core.server import run_server
from core.p2p import initiate_sync
from core.peers import PeerManager # Import the new manager
from config import (
    ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, 
    MODELS_DIR, CORE_DIR, UTILS_DIR, PUBLIC_KEY_PATH
)

def initialize_environment():
    """Ensures all necessary directories exist and runs all setup functions."""
    # ... (This function is unchanged) ...
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
    Starts the P2P server and demonstrates syncing with a managed peer.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    setup_demo_data()
    
    # --- Setup Peer Manager and Demo Peer ---
    peer_manager = PeerManager()
    
    # For the demo, we'll add ourselves as a peer to sync with
    with open(PUBLIC_KEY_PATH, "rb") as f:
        my_public_key = f.read().hex()

    # This represents our own application, acting as a peer
    self_as_peer = Peer(
        email="self@example.com",
        public_key=my_public_key,
        address="http://127.0.0.1:5000"
    )
    peer_manager.add_peer(self_as_peer)

    # --- Start the P2P server in a background thread ---
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1) 
    
    # --- DEMO: Initiate a sync with our managed self ---
    current_user = User(id=1, role='national', region=None)
    peer_to_sync = peer_manager.get_peer("self@example.com")
    
    if peer_to_sync:
        sync_successful = initiate_sync(current_user, peer_to_sync)
        if sync_successful:
            peer_manager.update_last_synced(peer_to_sync.email)

    # --- Keep the application running ---
    print("\nMain application is running.")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application.")


if __name__ == "__main__":
    initialize_environment()
    run_app()
