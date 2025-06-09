from core.models import User

def has_access(user: User, record: dict) -> bool:
    """
    Checks if a user has permission to view a given record based on their role and region.
    This function is a direct implementation of the Row-Level Function from the design doc.
    """
    # ... (This function is unchanged) ...
    if user.role == 'national': return True
    if user.role == 'statal' and record.get('state') == user.region: return True
    if user.role == 'municipal' and record.get('city') == user.region: return True
    if user.role == 'facilitator' and (record.get('invited_by') == user.id or record.get('host_id') == user.id): return True
    if user.role == 'shadower' and record.get('invited_by') == user.id: return True
    return False

# --- Updated Function ---
def get_acl_filter_clause(user: User, table_name: str) -> (str, tuple):
    """
    Generates a SQL WHERE clause and parameters based on the user's role, region,
    and the specific table being queried.
    """
    role = user.role
    
    if role == 'national':
        return ("1 = 1", ())
        
    elif role == 'statal':
        return ("state = ?", (user.region,))
        
    elif role == 'municipal':
        return ("city = ?", (user.region,))
        
    # This logic is now aware of the table being queried
    elif role == 'facilitator':
        if table_name == 'meetings':
            # Facilitators can see meetings they host.
            return ("host_id = ?", (user.id,))
        else:
            # For other tables like 'users', we need a different rule.
            # A facilitator can see users they invited. Let's assume for now
            # this logic will be handled by a JOIN on the 'invitations' table
            # in a more complex query. For this simple find, we deny by default.
            # A safe default is to only let them see their own user record.
            return ("id = ?", (user.id,))
            
    # Default case: deny access
    return ("1 = 0", ())
