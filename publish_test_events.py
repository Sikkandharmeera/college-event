#!/usr/bin/env python
"""
Create test published events for student viewing
"""

import sys
sys.path.insert(0, '/d/CollegeEventsHub_FINAL')

from app import db, q
from datetime import datetime, timedelta

# First, let's check what events exist
print("=" * 60)
print("CHECKING EXISTING EVENTS")
print("=" * 60)

all_events = q(
    """
    SELECT id, event_name, status
    FROM events
    LIMIT 10
    """,
    fetch=True
)

if all_events:
    print(f"\nFound {len(all_events)} events:")
    for e in all_events:
        print(f"  - ID {e['id']}: {e['event_name']} (Status: {e['status']})")
else:
    print("\nNo events found in database!")
    sys.exit(1)

# Count published vs unpublished
published = q(
    """
    SELECT COUNT(*) as count
    FROM events
    WHERE status = 'Published'
    """,
    fetch=True
)

draft = q(
    """
    SELECT COUNT(*) as count
    FROM events
    WHERE status = 'Draft'
    """,
    fetch=True
)

cancelled = q(
    """
    SELECT COUNT(*) as count
    FROM events
    WHERE status = 'Cancelled'
    """,
    fetch=True
)

print(f"\n📊 Event Status Summary:")
print(f"  - Published: {published[0]['count']}")
print(f"  - Draft: {draft[0]['count']}")
print(f"  - Cancelled: {cancelled[0]['count']}")

# If there are draft events, publish them
draft_events = q(
    """
    SELECT id, event_name
    FROM events
    WHERE status = 'Draft'
    LIMIT 5
    """,
    fetch=True
)

if draft_events:
    print(f"\n🔄 Publishing {len(draft_events)} draft events...")
    for event in draft_events:
        q(
            """
            UPDATE events
            SET status = 'Published'
            WHERE id = %s
            """,
            (event['id'],)
        )
        print(f"  ✅ Published: {event['event_name']}")
    
    print(f"\n✨ Successfully published {len(draft_events)} events!")
    print("Students can now see these events on the /events page.")
else:
    print("\n⚠️  No draft events to publish.")
    print("You need to create events via the admin panel first.")
    print("1. Go to /admin/event/new (login as admin)")
    print("2. Create an event and save it")
    print("3. It will be created as 'Draft' status")
    print("4. Run this script again to publish it")
