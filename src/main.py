"""
Main entry point and demo for Spanning Tree Database + ACL System
"""

from spanning_tree import SpanningTreeDB, DataManager, Role


def create_test_data(db: SpanningTreeDB):
    """Create some test data for development"""
    dm = DataManager(db)
    
    # Create test users
    admin_id = dm.create_user("admin@spanningtree.org", "admin_public_key", "dev", "National")
    facilitator_id = dm.create_user("facilitator@test.com", "facilitator_public_key", "facilitator", "San Francisco")
    shadower_id = dm.create_user("shadower@test.com", "shadower_public_key", "shadower", "San Francisco")
    
    # Create test meeting
    admin = dm.get_user_by_email("admin@spanningtree.org")
    meeting_id = dm.create_meeting(admin, {
        'city': 'San Francisco',
        'state': 'California', 
        'scheduled_at': '2024-12-01 19:00:00',
        'title': 'Monthly Organizing Meeting',
        'notes': 'Discussion of local initiatives'
    })
    
    print(f"Created test data - Admin: {admin_id}, Facilitator: {facilitator_id}, Meeting: {meeting_id}")


def main():
    """Demo usage of the system"""
    print("Initializing Spanning Tree Database + ACL System...")
    
    # Initialize database
    db = SpanningTreeDB()
    dm = DataManager(db)
    
    # Create test data
    create_test_data(db)
    
    # Test ACL functionality
    admin = dm.get_user_by_email("admin@spanningtree.org")
    facilitator = dm.get_user_by_email("facilitator@test.com")
    shadower = dm.get_user_by_email("shadower@test.com")
    
    print(f"\nTesting ACL with different roles:")
    print(f"Admin meetings: {len(dm.get_filtered_meetings(admin))}")
    print(f"Facilitator meetings: {len(dm.get_filtered_meetings(facilitator))}")
    print(f"Shadower meetings: {len(dm.get_filtered_meetings(shadower))}")
    
    # Test data export
    export_data = dm.export_filtered_data(admin)
    print(f"\nAdmin can export {sum(len(v) for v in export_data.values())} total records")
    
    export_data = dm.export_filtered_data(shadower)  
    print(f"Shadower can export {sum(len(v) for v in export_data.values())} total records")
    
    print("\nDatabase + ACL system ready!")


if __name__ == "__main__":
    main()