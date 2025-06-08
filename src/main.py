import os

# --- Imports from our application modules ---

# Imports the function to set up the database schema and a generic finder
from models.database import initialize_database, get_db_connection, find_records

# Imports the function to generate cryptographic keys
from utils.crypto import generate_and_store_keys

# Imports the User data structure
from core.models import User

# This import is now correctly used by initialize_environment
from config import (
    ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, 
    MODELS_DIR, CORE_DIR, UTILS_DIR
)


def initialize_environment():
    """
    Ensures all necessary directories exist and runs all setup functions.
    This is a high-level coordinator function for application startup.
    """
    print("--- Initializing Environment ---")

    # 1. Ensure all directories exist using the imported config paths.
    # This is the corrected version that uses our single source of truth (config.py).
    for dir_path in [ACL_DIR, CONFIG_DIR, DATA_DIR, KEYS_DIR, MODELS_DIR, CORE_DIR, UTILS_DIR]:
        dir_path.mkdir(exist_ok=True)
    
    # 2. Secure the keys directory
    if os.name != 'nt':
        os.chmod(KEYS_DIR, 0o700)

    # 3. Run initial setup functions from other modules
    generate_and_store_keys()
    initialize_database()

    print("\n--- Environment check complete ---")


def setup_demo_data():
    """Inserts sample meetings into the database for the demo."""
    meetings = [
        (20, 'nyc', 'ny', 'Meeting A in NYC'),
        (21, 'nyc', 'ny', 'Meeting B in NYC'),
        (40, 'albany', 'ny', 'Meeting C in Albany'),
        (41, 'sf', 'ca', 'Meeting D in SF')
    ]
    conn = get_db_connection()
    # Clear existing meetings to make the demo repeatable
    conn.execute("DELETE FROM meetings")
    conn.executemany("INSERT INTO meetings (host_id, city, state, title) VALUES (?, ?, ?, ?)", meetings)
    conn.commit()
    conn.close()
    print("Demo data has been set up.")


def run_app():
    """
    The main application logic. 
    Currently, it demonstrates fetching data with dynamic, role-based ACL filters.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    setup_demo_data()

    # Create sample users for the demo
    facilitator_nyc = User(id=20, role='facilitator', region='nyc')
    municipal_nyc = User(id=30, role='municipal', region='nyc')
    statal_ny = User(id=40, role='statal', region='ny')
    national_user = User(id=50, role='national', region=None)

    # --- Run ACL-filtered Queries ---
    
    # Facilitator in NYC should only see meetings they host (id=20)
    facilitator_meetings = find_records('meetings', facilitator_nyc)
    print("Results:", [m['title'] for m in facilitator_meetings])

    # Municipal user in NYC should see all meetings in their city
    municipal_meetings = find_records('meetings', municipal_nyc)
    print("Results:", [m['title'] for m in municipal_meetings])
    
    # Statal user for NY should see all meetings in their state
    statal_meetings = find_records('meetings', statal_ny)
    print("Results:", sorted([m['title'] for m in statal_meetings]))
    
    # National user should see all meetings
    national_meetings = find_records('meetings', national_user)
    print("Results:", sorted([m['title'] for m in national_meetings]))


# This is the main execution block that runs when you execute `python main.py`
if __name__ == "__main__":
    initialize_environment()
    run_app()
