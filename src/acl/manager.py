"""
Access Control Layer - Role-based permissions management
"""

from typing import Dict, List, Optional, Any, Tuple
from ..models.enums import Role


class ACLManager:
    """Access Control Layer - enforces role-based permissions"""
    
    def __init__(self, db):
        self.db = db
    
    def has_access(self, user: Dict[str, Any], record: Dict[str, Any]) -> bool:
        """
        Core ACL function - determines if user can access a record
        """
        if not user or not record:
            return False
            
        role = user.get('role')
        user_region = user.get('region')
        user_id = user.get('id')
        
        # National and dev roles have full access
        if role in ['national', 'dev']:
            return True
            
        # Statal role can access records in their state
        if role == 'statal' and record.get('state') == user_region:
            return True
            
        # Municipal role can access records in their city
        if role == 'municipal' and record.get('city') == user_region:
            return True
            
        # Facilitator can access records they created or host
        if role == 'facilitator':
            if (record.get('invited_by') == user_id or 
                record.get('host_id') == user_id):
                return True
                
        # Shadower can only access records they invited
        if role == 'shadower' and record.get('invited_by') == user_id:
            return True
            
        return False
    
    def get_acl_filter(self, user: Dict[str, Any], table: str) -> Tuple[str, List]:
        """
        Generate SQL WHERE clause and parameters for ACL filtering
        Returns (where_clause, parameters)
        """
        if not user:
            return "1 = 0", []  # No access
            
        role = user.get('role')
        user_region = user.get('region')
        user_id = user.get('id')
        
        # National and dev see everything
        if role in ['national', 'dev']:
            return "1 = 1", []
            
        conditions = []
        params = []
        
        # State-level access
        if role == 'statal':
            conditions.append("state = ?")
            params.append(user_region)
            
        # City-level access  
        elif role == 'municipal':
            conditions.append("city = ?")
            params.append(user_region)
            
        # Facilitator access (own records)
        elif role == 'facilitator':
            if table in ['meetings']:
                conditions.append("host_id = ?")
                params.append(user_id)
            elif table in ['nodes', 'signups']:
                conditions.append("invited_by = ?")
                params.append(user_id)
            else:
                # For other tables, need both invited_by and host_id checks
                conditions.append("(invited_by = ? OR host_id = ?)")
                params.extend([user_id, user_id])
                
        # Shadower access (only invitees)
        elif role == 'shadower':
            conditions.append("invited_by = ?")
            params.append(user_id)
            
        # Connector has no system access
        else:
            return "1 = 0", []
            
        if conditions:
            return " OR ".join(f"({cond})" for cond in conditions), params
        else:
            return "1 = 0", []
    
    def can_perform_action(self, user: Dict[str, Any], action: str, 
                          target_table: str = None) -> bool:
        """
        Check if user can perform a specific action
        """
        role = user.get('role')
        
        # Action-specific permissions
        if action == 'create_meeting':
            return Role.has_minimum_role(role, Role.FACILITATOR.value)
        elif action == 'create_user':
            return Role.has_minimum_role(role, Role.MUNICIPAL.value)
        elif action == 'send_mass_email':
            return Role.has_minimum_role(role, Role.FACILITATOR.value)
        elif action == 'view_audit_log':
            return Role.has_minimum_role(role, Role.MUNICIPAL.value)
        elif action == 'system_admin':
            return role == Role.DEV.value
        
        return False