import os
import time
import threading

from models.database import initialize_database
from utils.crypto import generate_and_store_keys
from core.models import User
from core.invites import InvitationManager # Import the new manager

def initialize_environment():
    """Ensures all necessary directories exist and runs all setup functions."""
    print("--- Initializing Environment ---")
    # ... (No changes here, but you must delete your old .db file) ...
    # ...
    generate_and_store_keys()
    initialize_database()
    print("\n--- Environment check complete ---")


def run_app():
    """
    Demonstrates the invitation token generation and redemption workflow.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    
    # --- DEMO: Invitation Workflow ---
    print("\n--- Running Invitation Demo ---")

    # 1. Setup
    invitation_manager = InvitationManager()
    # Let's pretend our current user (ID=20, a facilitator) is inviting someone
    inviter_user = User(id=20, role='facilitator', region='nyc')
    invitee_email = "new.participant@example.com"
    
    # 2. Generate an invite
    new_token = invitation_manager.generate_invite(inviter_user, invitee_email)

    if new_token:
        # 3. Simulate the new participant signing up with the correct token
        print("\n--- Simulating successful redemption ---")
        invitation_manager.redeem_invite(new_token, invitee_email)

        # 4. Simulate someone trying to use the same token again
        print("\n--- Simulating a repeat redemption attempt ---")
        invitation_manager.redeem_invite(new_token, invitee_email)

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
