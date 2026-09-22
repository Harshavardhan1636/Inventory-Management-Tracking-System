"""
API route regression tests.
"""

import sys
from pathlib import Path

from flask import Flask

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.routes import register_routes, set_components


class FakeDB:
    """Minimal DB stub for API route tests."""

    def __init__(self):
        self.inventory = {"apple": 2}
        self.update_calls = []
        self.logged_actions = []

    def get_inventory_item(self, item_class):
        if item_class not in self.inventory:
            return None
        return {
            "item_class": item_class,
            "quantity": self.inventory[item_class],
            "last_updated": "2026-04-07T00:00:00",
            "low_stock_threshold": 2,
        }

    def update_inventory(self, item_class, quantity_change):
        self.update_calls.append((item_class, quantity_change))

        if item_class not in self.inventory:
            self.inventory[item_class] = 0

        new_quantity = self.inventory[item_class] + quantity_change
        if new_quantity < 0:
            return False

        self.inventory[item_class] = new_quantity
        return True

    def log_action(self, action):
        self.logged_actions.append(action)


class FakeReasoning:
    """Minimal reasoning stub for shelf state endpoint tests."""

    def __init__(self):
        self.state = {
            "SLOT_0_0": {
                "slot_id": "SLOT_0_0",
                "current_item": "apple",
                "expected_item": None,
                "is_occupied": True,
                "is_uncertain": False,
                "is_misplaced": False,
                "confidence": 0.9,
                "status": "STABLE",
                "verification": {
                    "fusion_source": "hybrid_agree",
                    "resolved_confidence": 0.9,
                },
            }
        }

    def get_current_state(self):
        return self.state

    def set_expected_item(self, slot_id, expected_item):
        slot_state = self.state.get(slot_id)
        if slot_state is None:
            return False

        slot_state["expected_item"] = expected_item
        slot_state["is_misplaced"] = (
            expected_item is not None
            and slot_state.get("current_item") != expected_item
        )
        return True


def build_client():
    """Build a Flask test client with stubbed components."""
    app = Flask(__name__)
    register_routes(app)

    db = FakeDB()
    set_components(
        {
            "database": db,
            "reasoning": FakeReasoning(),
        }
    )

    return app.test_client(), db


def test_shelf_state_alias_matches_primary_route():
    """Both shelf-state URLs should remain available for compatibility."""
    client, _ = build_client()

    primary = client.get("/api/shelf/state")
    alias = client.get("/api/shelf-state")

    assert primary.status_code == 200
    assert alias.status_code == 200
    assert primary.get_json() == alias.get_json()


def test_update_inventory_missing_item_returns_404_without_mutation():
    """Updating unknown items must not create phantom inventory rows."""
    client, db = build_client()

    response = client.post("/api/inventory/missing/update", json={"quantity_change": 1})

    assert response.status_code == 404
    assert db.update_calls == []
    assert db.logged_actions == []


def test_update_inventory_zero_change_rejected():
    """Zero-change updates should be rejected as invalid input."""
    client, db = build_client()

    response = client.post("/api/inventory/apple/update", json={"quantity_change": 0})

    assert response.status_code == 400
    assert db.update_calls == []
    assert db.logged_actions == []


def test_update_inventory_existing_item_success():
    """Valid updates should still work for existing items."""
    client, db = build_client()

    response = client.post(
        "/api/inventory/apple/update",
        json={"quantity_change": -1, "reason": "Manual adjustment"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["item"]["quantity"] == 1
    assert db.update_calls == [("apple", -1)]
    assert len(db.logged_actions) == 1


def test_set_shelf_assignment_updates_expected_item():
    """Slot assignment endpoint should update expected item in reasoning state."""
    client, _ = build_client()

    response = client.post(
        "/api/shelf/assignment",
        json={"slot_id": "SLOT_0_0", "expected_item": "bottle"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["slot_id"] == "SLOT_0_0"
    assert payload["expected_item"] == "bottle"
    assert payload["slot_state"]["is_misplaced"] is True


def test_set_shelf_assignment_rejects_unknown_slot():
    """Unknown slot assignment requests should return 404."""
    client, _ = build_client()

    response = client.post(
        "/api/shelf/assignment",
        json={"slot_id": "SLOT_9_9", "expected_item": "bottle"},
    )

    assert response.status_code == 404
