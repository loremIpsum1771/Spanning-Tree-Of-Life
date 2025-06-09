from dataclasses import dataclass, field
from typing import Optional

@dataclass
class User:
    """A simple data class to represent the current user for ACL checks."""
    id: int
    role: str
    region: str # This can be a city for municipal users, or a state for statal users

@dataclass
class Peer:
    """Represents a known peer in the network."""
    email: str
    public_key: str # Stored in hex format
    address: str # e.g., "http://127.0.0.1:5000"
    last_synced: Optional[int] = None # Unix timestamp
