"""
Data access layer with automatic ACL enforcement
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from ..acl.manager import ACLManager


class DataManager:
    """Data access layer with automatic ACL enforcement"""
    
    def __init__(self, db):
        self.db = db
        self.acl = ACLManager(db)
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by email (no ACL needed for auth)"""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE email = ? AND is_active = 1",
                (email.lower().strip(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_filtered_meetings(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get meetings visible to user based on ACL"""
        where_clause, params = self.acl.get_acl_filter(user, 'meetings')
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT m.*, u.email as host_email 
                FROM meetings m
                LEFT JOIN users u ON m.host_id = u.id
                WHERE ({where_clause}) AND m.is_cancelled = 0
                ORDER BY m.scheduled_at DESC
            """, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_filtered_nodes(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get nodes visible to user based on ACL"""
        where_clause, params = self.acl.get_acl_filter(user, 'nodes')
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT n.*, u.email as invited_by_email
                FROM nodes n
                LEFT JOIN users u ON n.invited_by = u.id
                WHERE ({where_clause})
                ORDER BY n.cc_score DESC, n.created_at DESC
            """, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def create_meeting(self, user: Dict[str, Any], meeting_data: Dict[str, Any]) -> Optional[int]:
        """Create meeting if user has permission (facilitator+)"""
        if not self.acl.can_perform_action(user, 'create_meeting'):
            raise PermissionError("Only facilitators and above can create meetings")
        
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO meetings (host_id, city, state, scheduled_at, title, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user['id'],
                meeting_data.get('city'),
                meeting_data.get('state'),
                meeting_data.get('scheduled_at'),
                meeting_data.get('title'),
                meeting_data.get('notes')
            ))
            meeting_id = cursor.lastrowid
            
            # Log the action
            self.log_action(user['id'], 'create', meeting_id, 'meetings', meeting_data)
            
            return meeting_id
    
    def record_attendance(self, user: Dict[str, Any], meeting_id: int, 
                         node_id: int, attended: bool) -> bool:
        """Record meeting attendance if user has access to the meeting"""
        # First check if user can access this meeting
        meeting = self.get_meeting_by_id(user, meeting_id)
        if not meeting:
            raise PermissionError("Cannot access this meeting")
        
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO attendance (meeting_id, node_id, attended)
                VALUES (?, ?, ?)
            """, (meeting_id, node_id, attended))
            
            # Update CC score if attended
            if attended:
                conn.execute("""
                    UPDATE nodes SET cc_score = cc_score + 1 
                    WHERE id = ?
                """, (node_id,))
            
            # Log the action
            self.log_action(user['id'], 'record_attendance', cursor.lastrowid, 
                          'attendance', {'meeting_id': meeting_id, 'node_id': node_id, 'attended': attended})
            
            return True
    
    def get_meeting_by_id(self, user: Dict[str, Any], meeting_id: int) -> Optional[Dict[str, Any]]:
        """Get specific meeting if user has access"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                SELECT m.*, u.email as host_email 
                FROM meetings m
                LEFT JOIN users u ON m.host_id = u.id
                WHERE m.id = ?
            """, (meeting_id,))
            row = cursor.fetchone()
            
            if row:
                meeting = dict(row)
                if self.acl.has_access(user, meeting):
                    return meeting
            return None
    
    def log_action(self, user_id: int, action: str, record_id: int, entity: str, 
                   payload: Dict[str, Any], signature: str = None):
        """Log action to audit trail"""
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_log (action, performed_by, record_id, entity, signature, payload)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (action, user_id, record_id, entity, signature, json.dumps(payload)))
    
    def create_user(self, email: str, public_key: str, role: str = 'shadower', 
                   region: str = None) -> int:
        """Create new user (admin function)"""
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO users (email, public_key, role, region)
                VALUES (?, ?, ?, ?)
            """, (email.lower().strip(), public_key, role, region))
            user_id = cursor.lastrowid
            
            # Log user creation
            self.log_action(user_id, 'create_user', user_id, 'users', 
                          {'email': email, 'role': role, 'region': region})
            
            return user_id
    
    def export_filtered_data(self, user: Dict[str, Any]) -> Dict[str, List]:
        """Export all data visible to user for sync purposes"""
        export_data = {}
        
        # Export each table with ACL filtering
        tables_to_export = ['meetings', 'nodes', 'attendance', 'invitations', 'cta_log']
        
        for table in tables_to_export:
            if table == 'meetings':
                export_data[table] = self.get_filtered_meetings(user)
            elif table == 'nodes':
                export_data[table] = self.get_filtered_nodes(user)
            elif table == 'attendance':
                export_data[table] = self._get_filtered_attendance(user)
            # Add other tables as needed
        
        return export_data
    
    def _get_filtered_attendance(self, user: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get attendance records user can access"""
        # Get meetings user can access, then get attendance for those meetings
        accessible_meetings = self.get_filtered_meetings(user)
        meeting_ids = [m['id'] for m in accessible_meetings]
        
        if not meeting_ids:
            return []
        
        placeholders = ','.join('?' * len(meeting_ids))
        
        with self.db.get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT * FROM attendance 
                WHERE meeting_id IN ({placeholders})
            """, meeting_ids)
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_inactive_users(self, days_threshold: int = 45):
        """Deactivate users inactive for more than threshold days"""
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        with self.db.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE users 
                SET is_active = 0 
                WHERE last_active < ? AND is_active = 1 AND role != 'dev'
            """, (cutoff_date,))
            
            deactivated_count = cursor.rowcount
            
            # Log cleanup action
            if deactivated_count > 0:
                self.log_action(None, 'cleanup_inactive', None, 'users', 
                              {'deactivated_count': deactivated_count, 'threshold_days': days_threshold})
            
            return deactivated_count