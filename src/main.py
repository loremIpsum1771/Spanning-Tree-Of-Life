import os
import time
import threading

from models.database import initialize_database
from utils.crypto import generate_and_store_keys
from core.models import User
from core.meetings import MeetingScheduler # Import our new scheduler

def initialize_environment():
    """Ensures all necessary directories exist and runs all setup functions."""
    print("--- Initializing Environment ---")
    # ... (This function's content is correct and does not need to change) ...
    # You do not need to delete your database for this step.
    generate_and_store_keys()
    initialize_database()
    print("\n--- Environment check complete ---")


def run_app():
    """
    Demonstrates the Meeting Scheduling feature, including permission checks.
    """
    print("\nWelcome to the Spanning Tree of Life Organizer System!")
    
    # --- DEMO: Meeting Scheduling Workflow ---
    print("\n--- Running Meeting Scheduling Demo ---")

    # 1. Setup
    scheduler = MeetingScheduler()
    
    # Create two sample users: one with permission, one without
    facilitator_user = User(id=20, role='facilitator', region='nyc')
    shadower_user = User(id=10, role='shadower', region='nyc')

    # 2. Facilitator (Success Case)
    # This user has permission and the meeting should be created.
    scheduler.schedule_meeting(
        host=facilitator_user,
        title="Weekly Planning Session",
        notes="Discuss upcoming events and goals.",
        city="nyc",
        state="ny"
    )

    # 3. Shadower (Failure Case)
    # This user does not have permission, so the action should be denied.
    scheduler.schedule_meeting(
        host=shadower_user,
        title="Unauthorized Meeting",
        notes="This should not be created.",
        city="nyc",
        state="ny"
    )

    print("\n--- Demo Complete. Application is idle. ---")
    print("To verify, check the 'meetings' and 'audit_log' tables in your database.")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down application.")


if __name__ == "__main__":
    initialize_environment()
    run_app()
