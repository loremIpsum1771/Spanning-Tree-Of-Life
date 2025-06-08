import os
from pathlib import Path

# --- Configuration: Define all application paths ---

# Path.cwd() gets the current working directory, where you run the script from.
# This makes the script portable.
PROJECT_ROOT = Path.cwd()

# Define paths for all our specialized directories
ACL_DIR = PROJECT_ROOT / "acl"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
KEYS_DIR = PROJECT_ROOT / "keys"
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = DATA_DIR / "spanning_tree.db" # The path for the embedded SQLite database 


def initialize_environment():
    """
    Ensures all necessary directories exist and sets secure permissions for the keys directory.
    This function makes the app robust and secure from the start.
    """
    print("Initializing environment...")

    # Create all directories. `exist_ok=True` prevents errors if they already exist.
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR]:
        dir_path.mkdir(exist_ok=True)
        print(f"Directory ensured: {dir_path}")

    # Set secure permissions on the keys directory to protect the user's private key.
    # This is a critical security step from the design document. 
    # In Python, 0o700 is the octal representation for rwx------ permissions.
    if os.name != 'nt':  # os.name is 'posix' for Linux/macOS, 'nt' for Windows
        try:
            os.chmod(KEYS_DIR, 0o700)
            print(f"Secure permissions (700) set for: {KEYS_DIR}")
        except OSError as e:
            print(f"Error setting permissions for {KEYS_DIR}: {e}")
            print("Please ensure you have the necessary rights to change permissions.")

    print("\nEnvironment check complete.")


def run_app():
    """
    The main application logic will eventually go here.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    # TODO: Future steps will add onboarding, UI, and the main application loop here.


if __name__ == "__main__":
    initialize_environment()
    run_app()
