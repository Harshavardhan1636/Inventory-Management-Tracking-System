"""
Shelf State Model for Inventory-Management-Tracking-System.

Represents the believed state of each shelf slot.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SlotState:
    """
    Represents the believed state of a single shelf slot.
    
    This is NOT a direct observation - it's what the system
    believes to be true after reasoning over multiple observations.
    
    Attributes:
        slot_id: Unique identifier for this slot
        expected_item: What should be here (from config)
        current_item: What we believe is here now
        confidence: Confidence level (0.0 to 1.0)
        last_confirmed: When state was last confidently confirmed
        state_status: UNKNOWN, STABLE, UNCERTAIN, TRANSITIONING
        consecutive_absences: Frames with no detection
        consecutive_presences: Frames with detection
    """
    
    slot_id: str
    expected_item: Optional[str] = None
    current_item: Optional[str] = None
    confidence: float = 0.0
    last_confirmed: Optional[datetime] = None
    state_status: str = "UNKNOWN"
    consecutive_absences: int = 0
    consecutive_presences: int = 0
    
    def is_occupied(self) -> bool:
        """Is this slot currently occupied with high confidence?"""
        return self.current_item is not None and self.confidence > 0.6
    
    def is_misplaced(self) -> bool:
        """Is the wrong item in this slot?"""
        if not self.is_occupied():
            return False
        return (
            self.expected_item is not None 
            and self.current_item != self.expected_item
        )
    
    def is_empty(self) -> bool:
        """Is this slot empty with high confidence?"""
        return self.current_item is None and self.confidence > 0.7
    
    def is_uncertain(self) -> bool:
        """Is the state highly uncertain?"""
        return self.confidence < 0.5 or self.state_status == "UNCERTAIN"
    
    def is_stable(self) -> bool:
        """Is the state stable?"""
        return self.state_status == "STABLE" and self.confidence > 0.7
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'slot_id': self.slot_id,
            'expected_item': self.expected_item,
            'current_item': self.current_item,
            'confidence': round(self.confidence, 3),
            'last_confirmed': self.last_confirmed.isoformat() if self.last_confirmed else None,
            'state_status': self.state_status,
            'is_occupied': self.is_occupied(),
            'is_misplaced': self.is_misplaced(),
            'is_empty': self.is_empty(),
            'is_uncertain': self.is_uncertain()
        }


class ShelfStateModel:
    """
    Maintains the believed state of the entire shelf.
    
    This is the system's "memory" - what it believes to be true
    about each slot, independent of momentary detection noise.
    
    Attributes:
        states: Dictionary of slot_id to SlotState
    """
    
    def __init__(self, slot_ids: List[str], expected_items: Dict[str, str]):
        """
        Initialize shelf state model.
        
        Args:
            slot_ids: List of all slot IDs
            expected_items: Dict mapping slot_id -> expected item class
        """
        self.states: Dict[str, SlotState] = {}
        self._initialize_states(slot_ids, expected_items)
        logger.info(f"ShelfStateModel initialized for {len(slot_ids)} slots")
    
    def _initialize_states(
        self, 
        slot_ids: List[str], 
        expected_items: Dict[str, str]
    ) -> None:
        """Create initial state for each slot."""
        for slot_id in slot_ids:
            self.states[slot_id] = SlotState(
                slot_id=slot_id,
                expected_item=expected_items.get(slot_id),
                current_item=None,
                confidence=0.0,
                state_status="UNKNOWN"
            )
    
    def get_slot_state(self, slot_id: str) -> Optional[SlotState]:
        """Get current state of a specific slot."""
        return self.states.get(slot_id)
    
    def get_all_states(self) -> Dict[str, SlotState]:
        """Get states of all slots."""
        return self.states.copy()
    
    def update_slot(
        self,
        slot_id: str,
        current_item: Optional[str] = None,
        confidence: float = 0.0,
        state_status: str = None
    ) -> None:
        """
        Update a slot's state.
        
        Args:
            slot_id: Slot to update
            current_item: New current item (None = empty)
            confidence: New confidence level
            state_status: New status (optional)
        """
        if slot_id not in self.states:
            logger.warning(f"Unknown slot_id: {slot_id}")
            return
        
        state = self.states[slot_id]
        state.current_item = current_item
        state.confidence = confidence
        
        if state_status:
            state.state_status = state_status
        
        if confidence > 0.7:
            state.last_confirmed = datetime.now()
    
    def get_uncertain_slots(self) -> List[str]:
        """Get list of slot IDs with uncertain states."""
        return [
            slot_id 
            for slot_id, state in self.states.items() 
            if state.is_uncertain()
        ]
    
    def get_misplaced_items(self) -> List[str]:
        """Get list of slot IDs with misplaced items."""
        return [
            slot_id 
            for slot_id, state in self.states.items() 
            if state.is_misplaced()
        ]
    
    def get_empty_slots(self) -> List[str]:
        """Get list of slot IDs that are empty."""
        return [
            slot_id 
            for slot_id, state in self.states.items() 
            if state.is_empty()
        ]
    
    def get_occupied_slots(self) -> List[str]:
        """Get list of slot IDs that are occupied."""
        return [
            slot_id 
            for slot_id, state in self.states.items() 
            if state.is_occupied()
        ]
    
    def to_dict(self) -> Dict:
        """Serialize state for logging/storage."""
        return {
            slot_id: state.to_dict()
            for slot_id, state in self.states.items()
        }
    
    def reset_slot(self, slot_id: str) -> None:
        """Reset a slot to unknown state."""
        if slot_id in self.states:
            state = self.states[slot_id]
            state.current_item = None
            state.confidence = 0.0
            state.state_status = "UNKNOWN"
            state.consecutive_absences = 0
            state.consecutive_presences = 0
            logger.debug(f"Reset slot: {slot_id}")
    
    def reset_all(self) -> None:
        """Reset all slots to unknown state."""
        for slot_id in self.states:
            self.reset_slot(slot_id)
        logger.info("All slots reset")
