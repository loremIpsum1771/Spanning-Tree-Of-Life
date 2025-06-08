# (imports at the top are unchanged)
from utils.crypto import generate_and_store_keys
from models.database import initialize_database
from core.audit import log_action
from config import ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR, CORE_DIR, UTILS_DIR
# --- New Imports ---
from acl.permissions import has_access
from core.models import User
import os

def initialize_environment():
    """
    Ensures all necessary directories exist and runs all setup functions.
    This is now a high-level coordinator function.
    """
    print("--- Initializing Environment ---")
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR, CORE_DIR, UTILS_DIR]:
        dir_path.mkdir(exist_ok=True)
    if os.name != 'nt':
        os.chmod(KEYS_DIR, 0o700)
    generate_and_store_keys()
    initialize_database()
    print("\n--- Environment check complete ---")


def run_app():
    """
    The main application logic. Now demonstrates the ACL.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    
    # --- DEMO: Test the Access Control Layer ---
    print("\n--- Running ACL Demo ---")

    # 1. Create sample users with different roles
    shadower_user = User(id=10, role='shadower', region='nyc')
    facilitator_user = User(id=20, role='facilitator', region='nyc')
    municipal_user = User(id=30, role='municipal', region='nyc')
    statal_user = User(id=40, role='statal', region='ny')
    national_user = User(id=50, role='national', region=None)
    other_user = User(id=99, role='shadower', region='sf') # A user from another city

    # 2. Create sample data records
    record_invited_by_shadower = {'invited_by': 10, 'city': 'nyc', 'state': 'ny'}
    record_hosted_by_facilitator = {'host_id': 20, 'city': 'nyc', 'state': 'ny'}
    record_in_nyc = {'city': 'nyc', 'state': 'ny'}
    record_in_albany = {'city': 'albany', 'state': 'ny'}
    record_in_sf = {'city': 'sf', 'state': 'ca'}

    # 3. Run tests and print results
    print(f"Shadower accessing their own invite: {has_access(shadower_user, record_invited_by_shadower)}") # Expected: True
    print(f"Shadower accessing another record in their city: {has_access(shadower_user, record_in_nyc)}") # Expected: False
    
    print(f"\nFacilitator accessing their hosted meeting: {has_access(facilitator_user, record_hosted_by_facilitator)}") # Expected: True
    
    print(f"\nMunicipal user accessing a record in their city: {has_access(municipal_user, record_in_nyc)}") # Expected: True
    print(f"Municipal user accessing a record in another city: {has_access(municipal_user, record_in_albany)}") # Expected: False
    
    print(f"\nStatal user accessing a record in their state (Albany): {has_access(statal_user, record_in_albany)}") # Expected: True
    print(f"Statal user accessing a record in another state (SF): {has_access(statal_user, record_in_sf)}") # Expected: False
    
    print(f"\nNational user accessing a random record: {has_access(national_user, record_in_sf)}") # Expected: True
