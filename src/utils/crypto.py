import os
from nacl.signing import SigningKey
from nacl.exceptions import CryptoError
# Import paths from our central config file
from config import PRIVATE_KEY_PATH, PUBLIC_KEY_PATH, KEYS_DIR

def generate_and_store_keys():
    """
    Generates an Ed25519 key pair if it doesn't already exist and stores it securely.
    """
    if PRIVATE_KEY_PATH.exists():
        print("Key pair already exists.")
        return

    print("Generating new Ed25519 key pair...")
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(signing_key.encode())
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(verify_key.encode())

    if os.name != 'nt':
        os.chmod(PRIVATE_KEY_PATH, 0o600)
        os.chmod(PUBLIC_KEY_PATH, 0o600)

    print(f"Private and public keys saved to: {KEYS_DIR}")
