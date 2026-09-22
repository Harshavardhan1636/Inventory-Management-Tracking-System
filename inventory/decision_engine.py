"""
Decision Engine Module for Inventory-Management-Tracking-System.

Translates reasoning events into inventory actions.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# Event types - duplicated here to avoid circular import
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
    Represents a shelf state event.
    Local definition to avoid circular imports.
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


class InventoryAction:
    """Represents an inventory update action."""
    
    def __init__(
        self,
        action_type: str,  # 'increment', 'decrement', 'flag', 'alert'
        item_class: str,
        slot_id: str,
        quantity_change: int = 0,
        reason: str = "",
        confidence: float = 0.0
    ):
        """
        Initialize inventory action.
        
        Args:
            action_type: Type of action ('increment', 'decrement', 'flag', 'alert')
            item_class: Item involved
            slot_id: Slot where action occurred
            quantity_change: Quantity to change
            reason: Reason for action
            confidence: Confidence level
        """
        self.action_type = action_type
        self.item_class = item_class
        self.slot_id = slot_id
        self.quantity_change = quantity_change
        self.reason = reason
        self.confidence = confidence
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'action_type': self.action_type,
            'item_class': self.item_class,
            'slot_id': self.slot_id,
            'quantity_change': self.quantity_change,
            'reason': self.reason,
            'confidence': round(self.confidence, 3),
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        return f"Action({self.action_type}: {self.item_class} @ {self.slot_id})"


class DecisionEngine:
    """
    Translates reasoning events into inventory actions.
    
    This layer applies business logic and validation before
    any inventory changes are made. It acts as a gatekeeper
    between reasoning and persistence.
    
    Attributes:
        min_confidence: Minimum confidence to act
        low_stock_threshold: When to generate low stock alerts
        auto_update: Whether to automatically update inventory
    """
    
    def __init__(self, config: Dict):
        """
        Initialize decision engine.
        
        Args:
            config: Configuration including:
                - min_confidence: Minimum confidence to act
                - low_stock_threshold: When to generate alerts
                - auto_update: Whether to auto-update inventory
        """
        self.min_confidence = config.get('min_confidence', 0.7)
        self.low_stock_threshold = config.get('low_stock_threshold', 2)
        self.auto_update = config.get('auto_update', True)
        
        # Track recent actions to prevent duplicates
        self.recent_actions: Dict[str, datetime] = {}
        
        logger.info(f"DecisionEngine initialized: "
                   f"min_conf={self.min_confidence}, "
                   f"low_stock={self.low_stock_threshold}")
    
    def process_events(
        self, 
        events: List[Event],
        current_inventory: Dict[str, int]
    ) -> List[InventoryAction]:
        """
        Process events and generate inventory actions.
        
        Args:
            events: List of events from reasoning engine
            current_inventory: Current inventory state {item_class: quantity}
            
        Returns:
            List of inventory actions to execute
        """
        actions = []
        
        for event in events:
            # Validate event
            if not self._is_valid_event(event):
                logger.debug(f"Event filtered out: {event}")
                continue
            
            # Check for duplicate (same slot + event type in last 5 seconds)
            if self._is_duplicate_event(event):
                logger.debug(f"Duplicate event ignored: {event}")
                continue
            
            # Generate action based on event type
            action = self._event_to_action(event, current_inventory)
            
            if action:
                actions.append(action)
                self._record_action(event)
                logger.info(f"Action generated: {action}")
        
        return actions

    def _event_type_value(self, event: Any) -> str:
        """
        Normalize event type across enum implementations.

        Reasoning events and decision events each define their own EventType enum
        classes. This helper converts both (and raw strings) into a shared string
        value such as "item_added".
        """
        raw_type = getattr(event, 'event_type', None)

        if hasattr(raw_type, 'value'):
            return str(raw_type.value)

        if isinstance(raw_type, str):
            return raw_type

        return str(raw_type) if raw_type is not None else ""
    
    def _is_valid_event(self, event: Event) -> bool:
        """
        Validate event before processing.
        
        Validation rules:
        - Confidence must be above threshold
        - Event type must be actionable
        - Item class must be valid (not None for certain events)
        """
        # Check confidence
        if event.confidence < self.min_confidence:
            return False

        event_type = self._event_type_value(event)
        if not event_type:
            return False
        
        # Check item class requirement
        if event_type in [EventType.ITEM_REMOVED.value, EventType.ITEM_ADDED.value]:
            if not event.item_class:
                logger.warning(f"Event missing item_class: {event}")
                return False
        
        return True
    
    def _is_duplicate_event(self, event: Event) -> bool:
        """Check if this event was recently processed."""
        key = f"{event.slot_id}_{self._event_type_value(event)}"
        
        if key in self.recent_actions:
            time_diff = (datetime.now() - self.recent_actions[key]).total_seconds()
            if time_diff < 5:  # 5 second window
                return True
        
        return False
    
    def _record_action(self, event: Event) -> None:
        """Record action to prevent duplicates."""
        key = f"{event.slot_id}_{self._event_type_value(event)}"
        self.recent_actions[key] = datetime.now()
    
    def _event_to_action(
        self, 
        event: Event,
        current_inventory: Dict[str, int]
    ) -> Optional[InventoryAction]:
        """
        Convert event to inventory action.
        
        Event -> Action mapping:
        - ITEM_REMOVED -> decrement quantity
        - ITEM_ADDED -> increment quantity
        - ITEM_MISPLACED -> flag for review
        - LOW_STOCK -> generate alert
        - UNCERTAIN_STATE -> flag for review
        """
        event_type = self._event_type_value(event)

        if event_type == EventType.ITEM_REMOVED.value:
            return self._handle_removal(event, current_inventory)
        
        elif event_type == EventType.ITEM_ADDED.value:
            return self._handle_addition(event, current_inventory)
        
        elif event_type == EventType.ITEM_MISPLACED.value:
            return self._handle_misplacement(event)
        
        elif event_type == EventType.LOW_STOCK.value:
            return self._handle_low_stock(event, current_inventory)
        
        elif event_type == EventType.UNCERTAIN_STATE.value:
            return self._handle_uncertainty(event)
        
        return None
    
    def _handle_removal(
        self, 
        event: Event,
        current_inventory: Dict[str, int]
    ) -> Optional[InventoryAction]:
        """
        Handle item removal event.
        
        Business logic:
        - Decrement quantity by 1
        - Check if this causes low stock
        - Prevent negative inventory
        """
        item_class = event.item_class
        current_qty = current_inventory.get(item_class, 0)
        
        # Prevent negative inventory
        if current_qty <= 0:
            logger.warning(f"Cannot decrement {item_class}: already at 0")
            return InventoryAction(
                action_type='flag',
                item_class=item_class,
                slot_id=event.slot_id,
                reason='Removal detected but inventory already 0',
                confidence=event.confidence
            )
        
        # Create decrement action
        action = InventoryAction(
            action_type='decrement',
            item_class=item_class,
            slot_id=event.slot_id,
            quantity_change=-1,
            reason=f'Item removed from {event.slot_id}',
            confidence=event.confidence
        )
        
        # Check if this will cause low stock
        if current_qty - 1 <= self.low_stock_threshold:
            logger.warning(f"Low stock alert: {item_class} = {current_qty - 1}")
        
        return action
    
    def _handle_addition(
        self, 
        event: Event,
        current_inventory: Dict[str, int]
    ) -> InventoryAction:
        """
        Handle item addition event.
        
        Business logic:
        - Increment quantity by 1
        """
        return InventoryAction(
            action_type='increment',
            item_class=event.item_class,
            slot_id=event.slot_id,
            quantity_change=1,
            reason=f'Item added to {event.slot_id}',
            confidence=event.confidence
        )
    
    def _handle_misplacement(self, event: Event) -> InventoryAction:
        """
        Handle misplaced item event.
        
        Business logic:
        - Flag for manual review
        - Don't auto-update inventory
        """
        return InventoryAction(
            action_type='flag',
            item_class=event.item_class,
            slot_id=event.slot_id,
            reason=f'Wrong item detected in {event.slot_id}',
            confidence=event.confidence
        )
    
    def _handle_low_stock(
        self, 
        event: Event,
        current_inventory: Dict[str, int]
    ) -> InventoryAction:
        """Handle low stock event."""
        return InventoryAction(
            action_type='alert',
            item_class=event.item_class,
            slot_id=event.slot_id,
            reason=f'Low stock: {current_inventory.get(event.item_class, 0)} remaining',
            confidence=event.confidence
        )
    
    def _handle_uncertainty(self, event: Event) -> InventoryAction:
        """Handle uncertain state event."""
        return InventoryAction(
            action_type='flag',
            item_class=event.item_class or 'unknown',
            slot_id=event.slot_id,
            reason=f'Uncertain state in {event.slot_id} - requires verification',
            confidence=event.confidence
        )
