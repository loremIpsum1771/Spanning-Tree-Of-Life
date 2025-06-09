import sqlite3
import time
from typing import Optional

from core.models import User
from models.database import get_db_connection
from core.audit import log_action # Import our existing audit logger

class MeetingScheduler:
    """Handles the business logic for creating and managing meetings."""

    def schedule_meeting(
        self,
        host: User,
        title: str,
        notes: str,
        city: str,
        state: str
    ) -> Optional[int]:
        """
        Creates a new meeting record in the database if the user has permission.
        Logs the creation event in the audit log.
        Returns the new meeting's ID on success, otherwise None.
        """
        print(f"\nUser '{host.id}' (role: {host.role}) attempting to schedule meeting '{title}'...")

        # 1. Check for permission based on user role 
        allowed_roles = ['facilitator', 'municipal', 'statal', 'national', 'dev']
        if host.role not in allowed_roles:
            print("Permission denied: User does not have the required role to schedule meetings.")
            return None

        # 2. Insert the new meeting into the database 
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # The scheduled_at and last_modified timestamps are handled by the database defaults
            cursor.execute(
                "INSERT INTO meetings (host_id, city, state, title, notes) VALUES (?, ?, ?, ?, ?)",
                (host.id, city, state, title, notes)
            )
            
            # Get the ID of the meeting we just created
            new_meeting_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            print(f"Successfully inserted new meeting with ID: {new_meeting_id}")

        except sqlite3.Error as e:
            print(f"Database error while scheduling meeting: {e}")
            return None
            
        # 3. Create a signed audit log for this action 
        log_action(
            action="create",
            performed_by=host.id,
            entity="meetings",
            record_id=new_meeting_id
        )

        return new_meeting_id
