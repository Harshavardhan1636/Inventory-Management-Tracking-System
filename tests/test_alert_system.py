"""
Alert system regression tests.
"""

from inventory.alert_system import AlertSystem


def test_alert_ids_are_unique():
    """Alert IDs should not collide, including across quick successive creations."""
    alert_system = AlertSystem()

    ids = set()
    for idx in range(20):
        alert = alert_system.create_info(
            title=f"Info {idx}",
            message="test"
        )
        assert alert.alert_id not in ids
        ids.add(alert.alert_id)
