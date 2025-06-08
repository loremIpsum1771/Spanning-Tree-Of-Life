import os
# Import our refactored functions
from utils.crypto import generate_and_store_keys
from models.database import initialize_database
from core.audit import log_action
# Import paths from the config file
from config import ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR, CORE_DIR, UTILS_DIR

def initialize_environment():
    """
    Ensures all necessary directories exist and runs all setup functions.
    This is now a high-level coordinator function.
    """
    print("--- Initializing Environment ---")

    # 1. Ensure all directories exist
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR, CORE_DIR, UTILS_DIR]:
        dir_path.mkdir(exist_ok=True)
    
    # Secure the keys directory
    if os.name != 'nt':
        os.chmod(KEYS_DIR, 0o700)

    # 2. Run initial setup functions from other modules
    generate_and_store_keys()
    initialize_database()

    print("\n--- Environment check complete ---")

def run_app():
    """
    The main application logic.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    
    # --- DEMO: Log a sample action ---
    print("\n--- Running Audit Log Demo ---")
    log_action(action="update", performed_by=1, entity="meetings", record_id=101)

if __name__ == "__main__":
    initialize_environment()
    run_app()
