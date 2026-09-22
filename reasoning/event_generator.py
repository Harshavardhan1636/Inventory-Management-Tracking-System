"""
Event Generator Module for Inventory-Management-Tracking-System.

Defines event types and structure for state transitions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of shelf state events."""
    ITEM_REMOVED = "item_removed"
    ITEM_ADDED = "item_added"
    ITEM_MISPLACED = "item_misplaced"
    LOW_STOCK = "low_stock"
    UNCERTAIN_STATE = "uncertain_state"
    STATE_STABILIZED = "state_stabilized"


@dataclass
class Event:
    """
    Represents a meaningful shelf state transition.
    
    Events are the output of the reasoning engine - they represent
    confident conclusions about what happened, not raw observations.
    
    Attributes:
        event_type: Type of event (from EventType enum)
        slot_id: Which slot this event occurred in
        item_class: Item involved (if applicable)
        confidence: Confidence level of this event
        timestamp: When event was generated
        metadata: Additional event-specific data
    """
    
    event_type: EventType
    slot_id: str
    item_class: Optional[str]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'event_type': self.event_type.value,
            'slot_id': self.slot_id,
            'item_class': self.item_class,
            'confidence': round(self.confidence, 3),
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }
    
    def __str__(self) -> str:
        return (
            f"Event({self.event_type.value} | "
            f"slot={self.slot_id} | "
            f"item={self.item_class} | "
            f"conf={self.confidence:.2f})"
        )
    
    def __repr__(self) -> str:
        return self.__str__()


def create_removal_event(
    slot_id: str,
    item_class: str,
    confidence: float,
    metadata: Optional[Dict] = None
) -> Event:
    """Factory function for removal events."""
    return Event(
        event_type=EventType.ITEM_REMOVED,
        slot_id=slot_id,
        item_class=item_class,
        confidence=confidence,
        metadata=metadata
    )


def create_addition_event(
    slot_id: str,
    item_class: str,
    confidence: float,
    metadata: Optional[Dict] = None
) -> Event:
    """Factory function for addition events."""
    return Event(
        event_type=EventType.ITEM_ADDED,
        slot_id=slot_id,
        item_class=item_class,
        confidence=confidence,
        metadata=metadata
    )


def create_misplacement_event(
    slot_id: str,
    detected_item: str,
    expected_item: str,
    confidence: float
) -> Event:
    """Factory function for misplacement events."""
    return Event(
        event_type=EventType.ITEM_MISPLACED,
        slot_id=slot_id,
        item_class=detected_item,
        confidence=confidence,
        metadata={'expected_item': expected_item}
    )


def create_uncertainty_event(
    slot_id: str,
    confidence: float
) -> Event:
    """Factory function for uncertainty events."""
    return Event(
        event_type=EventType.UNCERTAIN_STATE,
        slot_id=slot_id,
        item_class=None,
        confidence=confidence
    )
