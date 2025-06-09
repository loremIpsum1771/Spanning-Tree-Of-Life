import os
import time
import threading
import requests # We'll use requests to simulate a link click

from models.database import initialize_database, get_db_connection
from utils.crypto import generate_and_store_keys
from core.models import User
from core.server import run_server
from core.cta import CtaManager

def initialize_environment():
    """Ensures all necessary directories exist and runs all setup functions."""
    print("--- Initializing Environment ---")
    # ... (This function's content is correct and does not need to change) ...
    # You do not need to delete your database for this step.
    generate_and_store_keys()
    initialize_database()
    print("\n--- Environment check complete ---")


def setup_cta_demo_data(conn):
    """Creates dummy users for the CTA demo."""
    print("Setting up demo users for CTA...")
    users = [
        (10, 'shadower@example.com', 'key1', 'shadower', 'nyc'),
        (20, 'facilitator@example.com', 'key2', 'facilitator', 'nyc'),
        (30, 'municipal@example.com', 'key3', 'municipal', 'nyc')
    ]
    conn.execute("DELETE FROM users")
    conn.executemany("INSERT INTO users (id, email, public_key, role, region) VALUES (?, ?, ?, ?, ?)", users)
    conn.commit()

def run_app():
    """Demonstrates the Mass Email CTA workflow."""
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    
    conn = get_db_connection()
    setup_cta_demo_data(conn)
    conn.close()

    # --- Start the P2P server in a background thread ---
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1) 

    # --- DEMO: CTA Workflow ---
    cta_manager = CtaManager()
    
    # A facilitator will send the CTA.
    sender = User(id=20, role='facilitator', region='nyc')
    
    cta_manager.send_cta(
        sender=sender,
        subject="Volunteer for upcoming event!",
        body="We need volunteers for the rally next Saturday.",
        cta_link="https://example.com/volunteer-signup"
    )

    # --- Simulate a user clicking the link ---
    # In a real scenario, the user would click this link in their email client.
    # We will grab a token from the database to simulate this.
    print("\n--- Simulating a user clicking a CTA link ---")
    conn = get_db_connection()
    # Get a token that was just sent to the municipal user (ID 30)
    result = conn.execute("SELECT token FROM email_log WHERE recipient_id = 30").fetchone()
    conn.close()
    
    if result:
        token_to_click = result['token']
        # Use requests to "click" the link by sending a request to our server
        requests.get(f"http://127.0.0.1:5000/cta/{token_to_click}")
    
    print("\n--- Demo Complete. Application is idle. ---")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application.")


if __name__ == "__main__":
    initialize_environment()
    run_app()
