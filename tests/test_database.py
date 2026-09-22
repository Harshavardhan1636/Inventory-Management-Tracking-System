"""
Database manager regression tests.
"""

from pathlib import Path

from database.db_manager import DatabaseManager


def test_log_event_accepts_empty_metadata_dict(tmp_path):
    """Empty dict metadata should be serialized and persisted without DB errors."""
    db_path = tmp_path / "test_shelf.db"
    db = DatabaseManager(str(db_path))

    event_id = db.log_event(
        {
            "event_type": "item_added",
            "slot_id": "SLOT_0_0",
            "item_class": "bottle",
            "confidence": 0.91,
            "metadata": {},
        }
    )

    assert event_id != -1

    events = db.get_recent_events(limit=1)
    assert len(events) == 1
    assert events[0]["event_type"] == "item_added"
    assert events[0]["metadata"] == "{}"
