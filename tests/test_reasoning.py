"""
Inventory-Management-Tracking-System - Reasoning Engine Tests

Tests for temporal reasoning and state management.
"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime
import numpy as np

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from reasoning.shelf_state import SlotState, ShelfStateModel
from reasoning.temporal_buffer import TemporalBuffer
from reasoning.reasoning_engine import ReasoningEngine


class TestSlotState:
    """Tests for SlotState dataclass."""
    
    def test_slot_state_creation(self):
        """Test basic slot state creation."""
        state = SlotState(
            slot_id="SLOT_0_0",
            expected_item="bottle",
            current_item="bottle",
            confidence=0.9,
            state_status="STABLE"
        )
        
        assert state.slot_id == "SLOT_0_0"
        assert state.is_occupied() == True
        assert state.is_misplaced() == False
    
    def test_is_misplaced(self):
        """Test misplacement detection."""
        state = SlotState(
            slot_id="SLOT_0_0",
            expected_item="bottle",
            current_item="cup",
            confidence=0.8
        )
        
        assert state.is_misplaced() == True
    
    def test_is_empty(self):
        """Test empty detection."""
        state = SlotState(
            slot_id="SLOT_0_0",
            expected_item="bottle",
            current_item=None,
            confidence=0.9
        )
        
        assert state.is_empty() == True


class TestTemporalBuffer:
    """Tests for TemporalBuffer."""
    
    def test_buffer_creation(self):
        """Test buffer initialization."""
        slot_ids = ["SLOT_0_0", "SLOT_0_1"]
        buffer = TemporalBuffer(slot_ids, window_size=10)
        
        assert len(buffer.buffers) == 2
        assert buffer.window_size == 10
    
    def test_add_detection(self):
        """Test adding detections."""
        buffer = TemporalBuffer(["SLOT_0_0"], window_size=5)
        
        buffer.add_detection("SLOT_0_0", "bottle", 0.9)
        buffer.add_detection("SLOT_0_0", "bottle", 0.85)
        
        detections = buffer.get_recent_detections("SLOT_0_0")
        assert len(detections) == 2
    
    def test_consecutive_absences(self):
        """Test consecutive absence counting."""
        buffer = TemporalBuffer(["SLOT_0_0"], window_size=10)
        
        # Add some detections then absences
        buffer.add_detection("SLOT_0_0", "bottle", 0.9)
        buffer.add_detection("SLOT_0_0", None, 0.9)
        buffer.add_detection("SLOT_0_0", None, 0.9)
        buffer.add_detection("SLOT_0_0", None, 0.9)
        
        assert buffer.get_consecutive_absences("SLOT_0_0") == 3
    
    def test_consecutive_presences(self):
        """Test consecutive presence counting."""
        buffer = TemporalBuffer(["SLOT_0_0"], window_size=10)
        
        buffer.add_detection("SLOT_0_0", None, 0.9)
        buffer.add_detection("SLOT_0_0", "bottle", 0.9)
        buffer.add_detection("SLOT_0_0", "bottle", 0.85)
        buffer.add_detection("SLOT_0_0", "bottle", 0.88)
        
        assert buffer.get_consecutive_presences("SLOT_0_0") == 3


class TestReasoningEngine:
    """Tests for ReasoningEngine."""
    
    def get_test_engine(self):
        """Create test reasoning engine."""
        slot_ids = ["SLOT_0_0", "SLOT_0_1"]
        expected_items = {"SLOT_0_0": "bottle", "SLOT_0_1": "cup"}
        config = {
            'temporal_window': 10,
            'short_absence_threshold': 2,
            'removal_threshold': 5,
            'confidence_threshold': 0.7
        }
        return ReasoningEngine(slot_ids, expected_items, config)
    
    def test_engine_creation(self):
        """Test engine initialization."""
        engine = self.get_test_engine()
        
        assert engine is not None
        assert len(engine.state_model.states) == 2
    
    def test_short_absence_ignored(self):
        """Test that short absences are ignored (occlusion)."""
        engine = self.get_test_engine()
        
        # Simulate item being detected
        for _ in range(5):
            engine.process_detections([
                {'slot_id': 'SLOT_0_0', 'class_name': 'bottle', 'confidence': 0.9}
            ])
        
        # Simulate short absence (1 frame) - should be ignored
        events = engine.process_detections([])
        
        # Should not generate removal event for 1 frame absence
        removal_events = [e for e in events if e.event_type.value == 'item_removed']
        assert len(removal_events) == 0
    
    def test_sustained_absence_triggers_removal(self):
        """Test that sustained absence triggers removal."""
        engine = self.get_test_engine()
        
        # First establish item presence
        for _ in range(5):
            engine.process_detections([
                {'slot_id': 'SLOT_0_0', 'class_name': 'bottle', 'confidence': 0.9}
            ])
        
        # Now simulate sustained absence
        all_events = []
        for _ in range(7):
            events = engine.process_detections([])
            all_events.extend(events)
        
        # Should eventually get a removal event
        removal_events = [e for e in all_events if e.event_type.value == 'item_removed']
        assert len(removal_events) >= 1

    def test_current_state_is_json_serializable(self):
        """Reasoning state API payload should not contain numpy scalar types."""
        engine = self.get_test_engine()

        engine.process_detections([
            {
                'slot_id': 'SLOT_0_0',
                'class_name': np.str_('bottle'),
                'confidence': np.float32(0.95)
            }
        ])

        state = engine.get_current_state()
        # Should not raise TypeError: Object of type bool_/float32 is not JSON serializable
        json.dumps(state)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
