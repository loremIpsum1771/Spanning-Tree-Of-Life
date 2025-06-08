from dataclasses import dataclass

@dataclass
class User:
    """A simple data class to represent a user for ACL checks."""
    id: int
    role: str
    region: str # This can be a city for municipal users, or a state for statal users
