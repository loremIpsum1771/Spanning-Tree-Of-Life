"""
Database schema and connection management
"""

import sqlite3
import os
from pathlib import Path


class SpanningTreeDB:
    """Main database manager with schema initialization"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to user's home directory structure
            home_dir = Path.home()
            self.app_dir = home_dir / "SpanningTree"
            self.data_dir = self.app_dir / "data"
            self.data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(self.data_dir / "spanning_tree.db")
        
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with complete schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(self._get_schema_sql())
            # Enable foreign key constraints
            conn.execute("PRAGMA foreign_keys = ON")
    
    def _get_schema_sql(self) -> str:
        """Get the complete database schema SQL"""
        return """
            -- Users table - core identity and permissions
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                public_key TEXT NOT NULL,
                role TEXT CHECK(role IN ('connector', 'shadower', 'facilitator', 
                                       'municipal', 'statal', 'national', 'dev')) DEFAULT 'shadower',
                region TEXT,
                cc_score INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Signups table - people who registered but aren't activated yet
            CREATE TABLE IF NOT EXISTS signups (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                invited_by INTEGER REFERENCES users(id),
                city TEXT,
                state TEXT,
                zip TEXT,
                neighborhood TEXT,
                occupation TEXT,
                token TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                activated_at TIMESTAMP
            );

            -- Nodes table - activated community members
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                city TEXT,
                state TEXT,
                cc_score INTEGER DEFAULT 0,
                invited_by INTEGER REFERENCES users(id),
                first_meeting_id INTEGER REFERENCES meetings(id),
                region TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Meetings table - scheduled gatherings
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY,
                host_id INTEGER REFERENCES users(id),
                city TEXT,
                state TEXT,
                scheduled_at TIMESTAMP,
                title TEXT,
                notes TEXT,
                is_cancelled BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Attendance table - who attended which meetings
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY,
                meeting_id INTEGER REFERENCES meetings(id),
                node_id INTEGER REFERENCES nodes(id),
                attended BOOLEAN,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(meeting_id, node_id)
            );

            -- Invitations table - tracking invite tokens
            CREATE TABLE IF NOT EXISTS invitations (
                id INTEGER PRIMARY KEY,
                email TEXT,
                invited_by INTEGER REFERENCES users(id),
                used BOOLEAN DEFAULT 0,
                token TEXT UNIQUE,
                expires_at TIMESTAMP,
                used_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- CTA log table - call to action responses
            CREATE TABLE IF NOT EXISTS cta_log (
                id INTEGER PRIMARY KEY,
                node_id INTEGER REFERENCES nodes(id),
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                campaign_id TEXT,
                response_data TEXT
            );

            -- SLA votes table - service level agreement voting
            CREATE TABLE IF NOT EXISTS sla_votes (
                id INTEGER PRIMARY KEY,
                node_id INTEGER REFERENCES nodes(id),
                district TEXT,
                issue TEXT,
                vote TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Events table - general event logging
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                event_type TEXT,
                meta TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Audit log table - comprehensive action tracking
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY,
                action TEXT NOT NULL,
                performed_by INTEGER REFERENCES users(id),
                record_id INTEGER,
                entity TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                signature TEXT,
                payload TEXT
            );

            -- Email log table - mass communication tracking
            CREATE TABLE IF NOT EXISTS email_log (
                id INTEGER PRIMARY KEY,
                sender_id INTEGER REFERENCES users(id),
                recipient_id INTEGER REFERENCES nodes(id),
                subject TEXT,
                cta_link TEXT,
                token TEXT UNIQUE,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                responded_at TIMESTAMP
            );

            -- Create indexes for performance
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
            CREATE INDEX IF NOT EXISTS idx_users_region ON users(region);
            CREATE INDEX IF NOT EXISTS idx_meetings_city_state ON meetings(city, state);
            CREATE INDEX IF NOT EXISTS idx_meetings_host ON meetings(host_id);
            CREATE INDEX IF NOT EXISTS idx_nodes_city_state ON nodes(city, state);
            CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity);
            CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
        """
    
    def get_connection(self):
        """Get a database connection with row factory set"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query: str, params: tuple = None):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            if params:
                return conn.execute(query, params)
            else:
                return conn.execute(query)