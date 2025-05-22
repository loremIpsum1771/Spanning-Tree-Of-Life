"""
Enums and constants for the Spanning Tree system
"""

from enum import Enum


class Role(Enum):
    """User role hierarchy from lowest to highest privilege"""
    CONNECTOR = "connector"
    SHADOWER = "shadower" 
    FACILITATOR = "facilitator"
    MUNICIPAL = "municipal"
    STATAL = "statal"
    NATIONAL = "national"
    DEV = "dev"

    @classmethod
    def get_hierarchy_level(cls, role: str) -> int:
        """Get numeric level for role comparison"""
        hierarchy = {
            cls.CONNECTOR.value: 0,
            cls.SHADOWER.value: 1,
            cls.FACILITATOR.value: 2,
            cls.MUNICIPAL.value: 3,
            cls.STATAL.value: 4,
            cls.NATIONAL.value: 5,
            cls.DEV.value: 6
        }
        return hierarchy.get(role, 0)

    @classmethod
    def has_minimum_role(cls, user_role: str, required_role: str) -> bool:
        """Check if user has at least the required role level"""
        return cls.get_hierarchy_level(user_role) >= cls.get_hierarchy_level(required_role)