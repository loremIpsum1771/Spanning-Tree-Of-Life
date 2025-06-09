import json
import time
from typing import List, Optional
from pathlib import Path

from config import CONFIG_DIR
from core.models import Peer

PEERS_FILE_PATH = CONFIG_DIR / "peers.json"

class PeerManager:
    """Handles loading, saving, and managing the list of known peers."""

    def __init__(self, peers_file_path: Path = PEERS_FILE_PATH):
        self.peers_file_path = peers_file_path
        self._peers = {}  # In-memory cache, mapping email to Peer object
        self.load_peers()

    def load_peers(self):
        """Loads the list of peers from the peers.json file."""
        print("Loading peers from peers.json...")
        try:
            with open(self.peers_file_path, 'r') as f:
                peers_data = json.load(f)
                for email, data in peers_data.items():
                    self._peers[email] = Peer(**data)
            print(f"Loaded {len(self._peers)} peers.")
        except (FileNotFoundError, json.JSONDecodeError):
            print("peers.json not found or is empty. Starting with an empty peer list.")
            self._peers = {}

    def save_peers(self):
        """Saves the current list of peers back to peers.json."""
        peers_to_save = {
            email: peer.__dict__ for email, peer in self._peers.items()
        }
        with open(self.peers_file_path, 'w') as f:
            json.dump(peers_to_save, f, indent=4)

    def add_peer(self, peer: Peer):
        """Adds a new peer to the list and saves the file."""
        print(f"Adding peer: {peer.email}")
        self._peers[peer.email] = peer
        self.save_peers()

    def get_peer(self, email: str) -> Optional[Peer]:
        """Retrieves a peer by their email address."""
        return self._peers.get(email)

    def get_all_peers(self) -> List[Peer]:
        """Returns a list of all known peer objects."""
        return list(self._peers.values())

    def update_last_synced(self, email: str):
        """Updates the last_synced timestamp for a peer after a successful sync."""
        peer = self.get_peer(email)
        if peer:
            peer.last_synced = int(time.time())
            self.save_peers()
            print(f"Updated last_synced for peer: {email}")
