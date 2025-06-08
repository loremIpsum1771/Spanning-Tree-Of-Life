# Import the User class we just defined
from core.models import User

def has_access(user: User, record: dict) -> bool:
    """
    Checks if a user has permission to view a given record based on their role and region.
    This function is a direct implementation of the Row-Level Function from the design doc. 
    """
    # national role has full access to all data 
    if user.role == 'national':
        return True
    
    # statal role can view records matching their state 
    if user.role == 'statal' and record.get('state') == user.region:
        return True
    
    # municipal role can view records matching their city 
    if user.role == 'municipal' and record.get('city') == user.region:
        return True
    
    # facilitator can view records they invited or meetings they host 
    if user.role == 'facilitator' and (record.get('invited_by') == user.id or record.get('host_id') == user.id):
        return True
    
    # shadower can only view records they invited 
    if user.role == 'shadower' and record.get('invited_by') == user.id:
        return True

    # If no rules match, access is denied
    return False
    
# --- New Function ---
def get_acl_filter_clause(user: User) -> (str, tuple):
    """
    Generates a SQL WHERE clause and parameters based on the user's role and region.
    This translates the ACL rules into a database query. 
    """
    role = user.role
    
    # National users have no filters 
    if role == 'national':
        return ("1 = 1", ()) # A clause that is always true
        
    # Statal users are filtered by state 
    elif role == 'statal':
        return ("state = ?", (user.region,))
        
    # Municipal users are filtered by city 
    elif role == 'municipal':
        return ("city = ?", (user.region,))
        
    # Facilitators can see meetings they host 
    # (We are simplifying here to just 'host_id' for meetings)
    elif role == 'facilitator':
        return ("host_id = ?", (user.id,))
        
    # Shadowers can see people they invited, but not meetings by default
    # We will handle the 'invited_by' case when querying those specific tables.
    # For a general query on meetings, they see nothing.
    
    # Default case: deny access by returning a clause that is always false
    return ("1 = 0", ())
