import secrets
import sqlite3
import time
from typing import List

from core.models import User
from models.database import get_db_connection, find_records

class CtaManager:
    """Handles the logic for sending and tracking Calls to Action (CTAs)."""

    def send_cta(self, sender: User, subject: str, body: str, cta_link: str):
        """
        Sends a CTA to all users the sender is allowed to see.
        """
        print(f"\nUser '{sender.id}' is sending a new CTA: '{subject}'")

        # 1. Permission Check
        allowed_roles = ['facilitator', 'municipal', 'statal', 'national', 'dev']
        if sender.role not in allowed_roles:
            print("Permission Denied: User cannot send mass CTAs.")
            return

        # 2. Get Recipients using our existing ACL-filtered function
        # A full implementation would allow for more specific filters.
        recipients = find_records('users', sender)
        print(f"Found {len(recipients)} recipients based on ACLs.")

        conn = get_db_connection()
        try:
            for recipient in recipients:
                # 3. For each recipient, generate a unique token and log it
                token = secrets.token_urlsafe(16)
                recipient_id = recipient['id']

                conn.execute(
                    "INSERT INTO email_log (sender_id, recipient_id, subject, cta_link, token) VALUES (?, ?, ?, ?, ?)",
                    (sender.id, recipient_id, subject, cta_link, token)
                )

                # 4. Simulate sending the email
                # The personalized link points back to our server's tracking endpoint
                personalized_link = f"http://127.0.0.1:5000/cta/{token}"
                print(f"  -> SIMULATING EMAIL to user {recipient_id}: {body}. Click here: {personalized_link}")
            
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error while sending CTA: {e}")
        finally:
            conn.close()

    def track_click(self, token: str):
        """
        Tracks a click on a CTA link, marking it as responded.
        """
        print(f"\n--- [/cta] Tracking click for token: {token} ---")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find the log entry and update it if it exists and hasn't been used
        cursor.execute(
            "UPDATE email_log SET responded_at = ? WHERE token = ? AND responded_at IS NULL",
            (int(time.time()), token)
        )
        
        # cursor.rowcount will be 1 if a row was updated, 0 otherwise
        if cursor.rowcount > 0:
            print("Successfully tracked CTA click.")
            # TODO: A full implementation would also update the user's CC score here.
        else:
            print("Warning: Could not track click. Token not found or already used.")
            
        conn.commit()
        conn.close()
