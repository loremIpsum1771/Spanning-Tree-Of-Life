import os
from pathlib import Path
# Import the necessary components from PyNaCl
from nacl.signing import SigningKey
from nacl.exceptions import CryptoError

# --- Configuration: Define all application paths ---
PROJECT_ROOT = Path.cwd()
ACL_DIR = PROJECT_ROOT / "acl"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
KEYS_DIR = PROJECT_ROOT / "keys"
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = DATA_DIR / "spanning_tree.db"

# Define the paths for the key files
PRIVATE_KEY_PATH = KEYS_DIR / "id_ed25519"
PUBLIC_KEY_PATH = KEYS_DIR / "id_ed25519.pub"


def generate_and_store_keys():
    """
    Generates an Ed25519 key pair if it doesn't already exist and stores it securely.
    """
    # Check if the private key already exists to avoid overwriting it.
    if PRIVATE_KEY_PATH.exists():
        print("Key pair already exists. Loading public key.")
    else:
        print("Generating new Ed25519 key pair...")
        # Generate a new SigningKey (which contains the private key) 
        signing_key = SigningKey.generate()

        # Extract the public key (VerifyKey) from the signing key 
        verify_key = signing_key.verify_key

        # Save the private key (as raw bytes)
        with open(PRIVATE_KEY_PATH, "wb") as f:
            f.write(signing_key.encode())

        # Save the public key (as raw bytes)
        with open(PUBLIC_KEY_PATH, "wb") as f:
            f.write(verify_key.encode())

        # Set secure file permissions (read/write for owner only)
        # This corresponds to chmod 600 
        if os.name != 'nt':
            os.chmod(PRIVATE_KEY_PATH, 0o600)
            os.chmod(PUBLIC_KEY_PATH, 0o600)

        print(f"Private key saved to: {PRIVATE_KEY_PATH}")
        print(f"Public key saved to: {PUBLIC_KEY_PATH}")

    # For demonstration, let's read and display the public key
    with open(PUBLIC_KEY_PATH, "rb") as f:
        public_key_bytes = f.read()
    print(f"Node Public Key (hex): {public_key_bytes.hex()}")


def initialize_environment():
    """
    Ensures all necessary directories exist and sets secure permissions for the keys directory.
    """
    print("Initializing environment...")
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR]:
        dir_path.mkdir(exist_ok=True)
        print(f"Directory ensured: {dir_path}")

    if os.name != 'nt':
        try:
            os.chmod(KEYS_DIR, 0o700) # Secure the directory 
            print(f"Secure permissions (700) set for: {KEYS_DIR}")
        except OSError as e:
            print(f"Error setting permissions for {KEYS_DIR}: {e}")

    # --- New step ---
    # Generate keys after ensuring the directory is secure
    generate_and_store_keys()
    # ----------------

    print("\nEnvironment check complete.")


def run_app():
    """
    The main application logic will eventually go here.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")


if __name__ == "__main__":
    initialize_environment()
    run_app()
