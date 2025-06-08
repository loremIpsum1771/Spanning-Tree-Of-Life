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
