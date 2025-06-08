import os
import time
import threading # Import the threading module

# --- Imports from our application modules ---
from models.database import initialize_database, get_db_connection, find_records
from utils.crypto import generate_and_store_keys
from core.models import User
from core.server import run_server # Import our new server function
from config import (
    ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, 
    MODELS_DIR, CORE_DIR, UTILS_DIR
)


def initialize_environment():
    """
    Ensures all necessary directories exist and runs all setup functions.
    """
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
    The main application logic.
    Starts the P2P server and keeps the main application running.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    
    # --- Start the P2P server in a background thread ---
    # A daemon thread will automatically exit when the main program finishes.
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    print("\nMain application is running.")
    print("The P2P server is listening in the background.")
    print("Press Ctrl+C to exit.")
    
    # Keep the main thread alive to allow the background server to run
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application.")


# This is the main execution block
if __name__ == "__main__":
    initialize_environment()
    run_app()
