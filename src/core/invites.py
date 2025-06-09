import secrets
import sqlite3
from typing import Optional

from core.models import User
from models.database import get_db_connection

class InvitationManager:
    """Handles the logic for creating and redeeming invitation tokens."""

    def generate_invite(self, inviter: User, invitee_email: str) -> Optional[str]:
        """
        Generates a unique, secure token and stores the invitation record.
        Returns the token if successful.
        """
        print(f"User '{inviter.id}' is generating an invite for '{invitee_email}'...")
        # Generate a cryptographically secure, URL-safe token 
        token = secrets.token_urlsafe(32)
        
        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO invitations (email, invited_by, token) VALUES (?, ?, ?)",
                (invitee_email, inviter.id, token)
            )
            conn.commit()
            conn.close()
            print(f"Successfully created invitation with token: {token}")
            return token
        except sqlite3.Error as e:
            print(f"Database error while creating invitation: {e}")
            return None

    def redeem_invite(self, token: str, signup_email: str) -> bool:
        """
        Validates an invitation token and marks it as used upon successful signup.
        """
        print(f"Attempting to redeem invitation token '{token}' for email '{signup_email}'...")
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Find the invitation
        cursor.execute("SELECT * FROM invitations WHERE token = ?", (token,))
        invite = cursor.fetchone()

        # 2. Validate the invitation
        if not invite:
            print("Redemption failed: Token not found.")
            return False
        if invite['used']:
            print("Redemption failed: Token has already been used.") # 
            return False
        if invite['email'].lower() != signup_email.lower(): # 
            print(f"Redemption failed: Token is not valid for this email address.")
            return False

        # 3. If valid, proceed to mark as used and create signup record
        try:
            # Mark the token as used in the 'invitations' table 
            cursor.execute("UPDATE invitations SET used = 1 WHERE id = ?", (invite['id'],))
            
            # Create a record in the 'signups' table 
            # In a real app, this data would come from a sign-up form.
            cursor.execute(
                "INSERT INTO signups (name, email, invited_by, token) VALUES (?, ?, ?, ?)",
                ("New User", signup_email, invite['invited_by'], token)
            )
            conn.commit()
            print("Invitation successfully redeemed!")
            return True
        except sqlite3.Error as e:
            print(f"Database error during redemption: {e}")
            return False
        finally:
            conn.close()
