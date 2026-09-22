"""
Reasoning Engine Module for Inventory-Management-Tracking-System.

Core intelligence that reasons about shelf state over time.
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from .shelf_state import ShelfStateModel, SlotState
from .temporal_buffer import TemporalBuffer
from .event_generator import Event, EventType
import logging

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Core intelligence: reasons about shelf state over time.
    
    This is NOT just object detection post-processing.
    This component:
    - Maintains belief about shelf state
    - Handles detection uncertainty
    - Detects meaningful state transitions
    - Generates confident events
    
    CRITICAL: This is what makes the system intelligent, not reactive.
    
    Attributes:
        state_model: Current believed state of shelf
        buffer: Temporal detection history
        config: Reasoning thresholds and parameters
    """
    
    def __init__(
        self,
        slot_ids: List[str],
        expected_items: Dict[str, str],
        config: Dict
    ):
        """
        Initialize reasoning engine.
        
        Args:
            slot_ids: All shelf slot IDs
            expected_items: Expected item per slot
            config: Reasoning configuration containing:
                - temporal_window: Buffer size
                - short_absence_threshold: Frames to ignore
                - removal_threshold: Frames for confirmed removal
                - confidence_threshold: Minimum confidence to act
        """
        # State model: what we believe is true
        self.state_model = ShelfStateModel(slot_ids, expected_items)
        
        # Temporal buffer: recent detection history
        window_size = config.get('temporal_window', 10)
        self.buffer = TemporalBuffer(slot_ids, window_size=window_size)
        
        # Configuration
        self.short_absence_threshold = config.get('short_absence_threshold', 2)
        self.removal_threshold = config.get('removal_threshold', 5)
        self.confidence_threshold = config.get('confidence_threshold', 0.7)
        gemini_fusion = config.get('gemini_fusion', {})
        self.gemini_fusion_enabled = bool(gemini_fusion.get('enabled', True))
        self.gemini_agreement_weight = max(
            0.0,
            min(1.0, float(gemini_fusion.get('agreement_weight', 0.3)))
        )
        self.gemini_conflict_threshold = float(
            gemini_fusion.get('conflict_confidence_threshold', 0.75)
        )
        self.gemini_conflict_penalty = max(
            0.1,
            min(1.0, float(gemini_fusion.get('conflict_penalty', 0.5)))
        )
        self.gemini_inject_min_confidence = float(
            gemini_fusion.get('inject_min_confidence', 0.7)
        )
        self.gemini_inject_confidence_scale = max(
            0.1,
            min(1.0, float(gemini_fusion.get('inject_confidence_scale', 0.9)))
        )
        
        # Track event generation to prevent duplicates
        self._recent_events: Dict[str, datetime] = {}
        self._latest_slot_evidence: Dict[str, Dict[str, Any]] = {
            slot_id: {
                'fusion_source': 'uninitialized',
                'yolo_item': None,
                'yolo_confidence': 0.0,
                'gemini_status': 'unavailable',
                'gemini_item': None,
                'gemini_confidence': 0.0,
                'resolved_item': None,
                'resolved_confidence': 0.0,
            }
            for slot_id in slot_ids
        }
        
        logger.info(f"ReasoningEngine initialized: "
                   f"window={window_size}, "
                   f"short_absence={self.short_absence_threshold}, "
                   f"removal={self.removal_threshold}")
    
    def process_detections(
        self, 
        detections: List[Dict],
        gemini_slot_hints: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Event]:
        """
        Main reasoning loop: process new detections and generate events.
        
        Args:
            detections: Current frame detections with slot assignments
            [
                {
                    'slot_id': str,
                    'class_name': str,
                    'confidence': float
                }
            ]
            
        Returns:
            List of generated events (state transitions)
        """
        events = []
        
        # Step 1: Update temporal buffers with new detections
        self._update_buffers(detections, gemini_slot_hints=gemini_slot_hints)
        
        # Step 2: Reason about each slot
        for slot_id in self.state_model.states.keys():
            slot_events = self._reason_about_slot(slot_id)
            events.extend(slot_events)
        
        # Log events
        for event in events:
            logger.info(f"Event generated: {event}")
        
        return events

    def _normalize_item_class(self, item_class: Optional[str]) -> Optional[str]:
        """Normalize item labels to a stable lower-case token."""
        if item_class is None:
            return None

        normalized = str(item_class).strip().lower()
        if not normalized:
            return None

        normalized = normalized.replace('_', ' ').replace('-', ' ')
        normalized = ' '.join(normalized.split())

        alias_map = {
            'books': 'book',
            'book': 'book',
            'apples': 'apple',
            'apple': 'apple',
            'bananas': 'banana',
            'banana': 'banana',
            'bottled water': 'bottle',
            'water bottle': 'bottle',
            'water bottles': 'bottle',
            'bottles': 'bottle',
            'bottle': 'bottle',
            'ceramic mug': 'cup',
            'ceramic mugs': 'cup',
            'mug': 'cup',
            'mugs': 'cup',
            'cups': 'cup',
            'cup': 'cup',
            'headphone': 'headphones',
            'headphones': 'headphones',
            'headset': 'headphones',
            'headsets': 'headphones',
            'earphone': 'headphones',
            'earphones': 'headphones',
            'earbud': 'headphones',
            'earbuds': 'headphones'
        }

        return alias_map.get(normalized, normalized)
    
    def _update_buffers(
        self,
        detections: List[Dict],
        gemini_slot_hints: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """
        Add new detections to temporal buffers.
        
        IMPORTANT: Slots with no detection = empty slot detection
        """
        gemini_slot_hints = gemini_slot_hints or {}

        # Create mapping of slot_id -> best detection (highest fused confidence).
        detection_map: Dict[str, Dict[str, Any]] = {}
        for detection in detections:
            slot_id = detection.get('slot_id')
            if not slot_id:
                continue

            detection_conf = float(
                detection.get('fused_confidence', detection.get('confidence', 0.0))
            )
            existing = detection_map.get(slot_id)
            if existing is None or detection_conf >= existing['confidence']:
                raw_item = detection.get('class_name')
                normalized_item = self._normalize_item_class(raw_item)
                detection_map[slot_id] = {
                    'item_class': normalized_item,
                    'confidence': detection_conf,
                }
        
        # Update all slots
        for slot_id in self.buffer.buffers.keys():
            det = detection_map.get(slot_id)
            hint = gemini_slot_hints.get(slot_id) if self.gemini_fusion_enabled else None
            state = self.state_model.get_slot_state(slot_id)
            expected_item = self._normalize_item_class(state.expected_item) if state else None

            evidence = {
                'fusion_source': 'default_empty',
                'yolo_item': det.get('item_class') if det else None,
                'yolo_confidence': float(det.get('confidence', 0.0)) if det else 0.0,
                'gemini_status': 'unavailable',
                'gemini_item': None,
                'gemini_confidence': 0.0,
                'resolved_item': None,
                'resolved_confidence': 0.9,
            }

            hint_status = 'unknown'
            hint_item = None
            hint_conf = 0.0
            if hint:
                hint_status = str(hint.get('status', 'unknown')).lower()
                hint_item = self._normalize_item_class(hint.get('item_class'))
                hint_conf = float(hint.get('confidence', 0.0))
                evidence['gemini_status'] = hint_status
                evidence['gemini_item'] = hint_item
                evidence['gemini_confidence'] = hint_conf

            if det is not None:
                item_class = det.get('item_class')
                confidence = float(det.get('confidence', 0.0))
                fusion_source = 'yolo_only'

                if hint:
                    if hint_status == 'item' and hint_item == item_class:
                        confidence = (
                            (1.0 - self.gemini_agreement_weight) * confidence
                            + self.gemini_agreement_weight * hint_conf
                        )
                        fusion_source = 'hybrid_agree'
                    elif (
                        hint_status == 'item'
                        and hint_item
                        and hint_item != item_class
                        and hint_conf >= self.gemini_conflict_threshold
                    ):
                        if expected_item and hint_item == expected_item:
                            # Expected-item alignment can correct ambiguous detector class labels.
                            item_class = hint_item
                            confidence = max(
                                confidence * self.gemini_conflict_penalty,
                                hint_conf * self.gemini_inject_confidence_scale,
                            )
                            fusion_source = 'hybrid_expected_override'
                        else:
                            confidence = confidence * self.gemini_conflict_penalty
                            fusion_source = 'hybrid_conflict_penalty'
                    elif hint_conf >= self.gemini_conflict_threshold and (
                        (hint_status == 'item' and hint_item != item_class)
                        or hint_status == 'empty'
                    ):
                        confidence = confidence * self.gemini_conflict_penalty
                        fusion_source = 'hybrid_conflict_penalty'

                resolved_conf = min(max(confidence, 0.0), 1.0)
                self.buffer.add_detection(slot_id, item_class, resolved_conf)

                evidence['fusion_source'] = fusion_source
                evidence['resolved_item'] = item_class
                evidence['resolved_confidence'] = resolved_conf
                self._latest_slot_evidence[slot_id] = evidence
                continue

            # No YOLO detection for this slot. Optionally inject Gemini hint.
            if hint:
                if hint_conf >= self.gemini_inject_min_confidence:
                    scaled_conf = min(
                        1.0,
                        max(0.0, hint_conf * self.gemini_inject_confidence_scale)
                    )
                    if hint_status == 'item' and hint_item:
                        self.buffer.add_detection(slot_id, hint_item, scaled_conf)
                        evidence['fusion_source'] = 'gemini_injected'
                        evidence['resolved_item'] = hint_item
                        evidence['resolved_confidence'] = scaled_conf
                        self._latest_slot_evidence[slot_id] = evidence
                        continue
                    if hint_status == 'empty':
                        self.buffer.add_detection(slot_id, None, scaled_conf)
                        evidence['fusion_source'] = 'gemini_empty_confirmed'
                        evidence['resolved_item'] = None
                        evidence['resolved_confidence'] = scaled_conf
                        self._latest_slot_evidence[slot_id] = evidence
                        continue

            # Default fallback: no detection = empty slot with high confidence
            self.buffer.add_detection(slot_id, None, 0.9)
            evidence['resolved_item'] = None
            evidence['resolved_confidence'] = 0.9
            self._latest_slot_evidence[slot_id] = evidence
    
    def _reason_about_slot(self, slot_id: str) -> List[Event]:
        """
        Apply reasoning logic to a single slot.
        
        This is where the intelligence happens.
        
        Reasoning rules (priority order):
        1. Short absence (1-2 frames) → IGNORE (likely occlusion)
        2. Sustained absence (5+ frames) → ITEM_REMOVED
        3. Sustained presence of wrong item → ITEM_MISPLACED
        4. Sustained presence of correct item → ITEM_ADDED (if was empty)
        5. Flickering detections → UNCERTAIN (flag for review)
        
        Returns:
            List of events generated for this slot
        """
        events = []
        current_state = self.state_model.get_slot_state(slot_id)
        
        if not current_state:
            return events
        
        # Get temporal analysis
        consecutive_absences = self.buffer.get_consecutive_absences(slot_id)
        consecutive_presences = self.buffer.get_consecutive_presences(slot_id)
        aggregated_item, aggregated_conf = self.buffer.get_aggregated_confidence(slot_id)
        is_flickering = self.buffer.is_fluctuating(slot_id)
        
        # Update state counters
        current_state.consecutive_absences = consecutive_absences
        current_state.consecutive_presences = consecutive_presences
        
        # Rule 1: Short absence → ignore
        if 0 < consecutive_absences <= self.short_absence_threshold:
            logger.debug(f"{slot_id}: Short absence ({consecutive_absences} frames), ignoring")
            return events
        
        # Rule 2: Sustained absence → removal
        if consecutive_absences >= self.removal_threshold:
            if current_state.is_occupied():
                event = self._handle_removal(slot_id, current_state, aggregated_conf)
                if event:
                    events.append(event)
        
        # Rule 3: Sustained mismatch → misplacement
        elif (
            current_state.expected_item
            and aggregated_item
            and self.buffer.has_sustained_mismatch(
                slot_id,
                current_state.expected_item,
                threshold=4
            )
        ):
            event = self._handle_misplacement(
                slot_id,
                current_state,
                aggregated_item,
                aggregated_conf
            )
            if event:
                events.append(event)
        
        # Rule 4: Sustained presence → addition
        elif aggregated_item and consecutive_absences == 0 and consecutive_presences >= 3:
            if not current_state.is_occupied():
                event = self._handle_addition(
                    slot_id, 
                    current_state, 
                    aggregated_item, 
                    aggregated_conf
                )
                if event:
                    events.append(event)
        
        # Rule 5: Flickering → uncertainty
        if is_flickering:
            if current_state.state_status != "UNCERTAIN":
                event = self._handle_uncertainty(slot_id, current_state)
                if event:
                    events.append(event)
        
        return events
    
    def _handle_removal(
        self, 
        slot_id: str, 
        current_state: SlotState, 
        confidence: float
    ) -> Optional[Event]:
        """
        Handle item removal from slot.
        
        Only generate event if:
        - Confidence above threshold
        - State was previously STABLE
        """
        if confidence < self.confidence_threshold:
            return None
        
        if current_state.state_status == "UNKNOWN":
            return None
        
        # Check for duplicate event
        if self._is_duplicate_event(slot_id, EventType.ITEM_REMOVED):
            return None
        
        # Update state
        removed_item = current_state.current_item
        current_state.current_item = None
        current_state.confidence = confidence
        current_state.state_status = "STABLE"
        current_state.last_confirmed = datetime.now()
        current_state.consecutive_absences = 0
        
        logger.info(f"{slot_id}: Item removed - {removed_item}")
        
        # Record event
        self._record_event(slot_id, EventType.ITEM_REMOVED)
        
        return Event(
            event_type=EventType.ITEM_REMOVED,
            slot_id=slot_id,
            item_class=removed_item,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def _handle_addition(
        self, 
        slot_id: str, 
        current_state: SlotState, 
        item_class: str, 
        confidence: float
    ) -> Optional[Event]:
        """Handle item addition to slot."""
        if confidence < self.confidence_threshold:
            return None
        
        # Check for duplicate event
        if self._is_duplicate_event(slot_id, EventType.ITEM_ADDED):
            return None
        
        # Update state
        current_state.current_item = item_class
        current_state.confidence = confidence
        current_state.state_status = "STABLE"
        current_state.last_confirmed = datetime.now()
        current_state.consecutive_presences = 0
        
        logger.info(f"{slot_id}: Item added - {item_class}")
        
        # Record event
        self._record_event(slot_id, EventType.ITEM_ADDED)
        
        return Event(
            event_type=EventType.ITEM_ADDED,
            slot_id=slot_id,
            item_class=item_class,
            confidence=confidence,
            timestamp=datetime.now()
        )
    
    def _handle_misplacement(
        self, 
        slot_id: str, 
        current_state: SlotState, 
        detected_item: str, 
        confidence: float
    ) -> Optional[Event]:
        """Handle wrong item in slot."""
        if confidence < self.confidence_threshold:
            return None
        
        # Check for duplicate event
        if self._is_duplicate_event(slot_id, EventType.ITEM_MISPLACED):
            return None
        
        # Update state
        current_state.current_item = detected_item
        current_state.confidence = confidence
        current_state.state_status = "STABLE"
        current_state.last_confirmed = datetime.now()
        
        logger.warning(f"{slot_id}: Item misplaced - "
                      f"found {detected_item}, expected {current_state.expected_item}")
        
        # Record event
        self._record_event(slot_id, EventType.ITEM_MISPLACED)
        
        return Event(
            event_type=EventType.ITEM_MISPLACED,
            slot_id=slot_id,
            item_class=detected_item,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata={'expected_item': current_state.expected_item}
        )
    
    def _handle_uncertainty(
        self, 
        slot_id: str, 
        current_state: SlotState
    ) -> Optional[Event]:
        """Handle uncertain/flickering state."""
        # Check for duplicate event
        if self._is_duplicate_event(slot_id, EventType.UNCERTAIN_STATE):
            return None
        
        # Update state
        current_state.state_status = "UNCERTAIN"
        current_state.confidence = 0.3
        
        logger.warning(f"{slot_id}: Uncertain state - flickering detections")
        
        # Record event
        self._record_event(slot_id, EventType.UNCERTAIN_STATE)
        
        return Event(
            event_type=EventType.UNCERTAIN_STATE,
            slot_id=slot_id,
            item_class=None,
            confidence=0.3,
            timestamp=datetime.now()
        )
    
    def _is_duplicate_event(
        self, 
        slot_id: str, 
        event_type: EventType
    ) -> bool:
        """Check if similar event was recently generated."""
        key = f"{slot_id}_{event_type.value}"
        
        if key in self._recent_events:
            elapsed = (datetime.now() - self._recent_events[key]).total_seconds()
            if elapsed < 5.0:  # 5 second cooldown
                return True
        
        return False
    
    def _record_event(self, slot_id: str, event_type: EventType) -> None:
        """Record event to prevent duplicates."""
        key = f"{slot_id}_{event_type.value}"
        self._recent_events[key] = datetime.now()
    
    def get_current_state(self) -> Dict[str, Dict]:
        """Get current believed state of all slots."""
        return {
            slot_id: {
                'slot_id': str(slot_id),
                'current_item': str(state.current_item) if state.current_item is not None else None,
                'expected_item': str(state.expected_item) if state.expected_item is not None else None,
                'confidence': float(state.confidence),
                'status': str(state.state_status),
                'is_misplaced': bool(state.is_misplaced()),
                'is_occupied': bool(state.is_occupied()),
                'is_uncertain': bool(state.is_uncertain()),
                'verification': {
                    'fusion_source': str(
                        self._latest_slot_evidence.get(slot_id, {}).get('fusion_source', 'unknown')
                    ),
                    'yolo_item': self._latest_slot_evidence.get(slot_id, {}).get('yolo_item'),
                    'yolo_confidence': float(
                        self._latest_slot_evidence.get(slot_id, {}).get('yolo_confidence', 0.0)
                    ),
                    'gemini_status': str(
                        self._latest_slot_evidence.get(slot_id, {}).get('gemini_status', 'unavailable')
                    ),
                    'gemini_item': self._latest_slot_evidence.get(slot_id, {}).get('gemini_item'),
                    'gemini_confidence': float(
                        self._latest_slot_evidence.get(slot_id, {}).get('gemini_confidence', 0.0)
                    ),
                    'resolved_item': self._latest_slot_evidence.get(slot_id, {}).get('resolved_item'),
                    'resolved_confidence': float(
                        self._latest_slot_evidence.get(slot_id, {}).get('resolved_confidence', 0.0)
                    ),
                }
            }
            for slot_id, state in self.state_model.states.items()
        }

    def get_shelf_item_counts(self, confidence_threshold: float = 0.6) -> Dict[str, Dict[str, int]]:
        """
        Compute per-item shelf counts using stabilized reasoning state
        derived from fused YOLO + Gemini evidence.

        Counts only include slots whose resolved confidence meets the threshold.
        Returned mapping includes:
          - expected_counts: slots configured for each item
          - observed_expected_counts: slots where detected item matches expected item
          - observed_any_counts: slots where detected item appears regardless of expected
        """
        threshold = max(0.0, min(1.0, float(confidence_threshold)))
        expected_counts: Dict[str, int] = {}
        observed_expected_counts: Dict[str, int] = {}
        observed_any_counts: Dict[str, int] = {}

        for _, state in self.state_model.states.items():
            expected_item = self._normalize_item_class(state.expected_item)
            if expected_item:
                expected_counts[expected_item] = expected_counts.get(expected_item, 0) + 1

            resolved_item = self._normalize_item_class(state.current_item)
            resolved_confidence = float(state.confidence)

            if resolved_item and resolved_confidence >= threshold:
                observed_any_counts[resolved_item] = observed_any_counts.get(resolved_item, 0) + 1
                if expected_item and resolved_item == expected_item:
                    observed_expected_counts[expected_item] = (
                        observed_expected_counts.get(expected_item, 0) + 1
                    )

        return {
            'expected_counts': expected_counts,
            'observed_expected_counts': observed_expected_counts,
            'observed_any_counts': observed_any_counts
        }

    def set_expected_item(self, slot_id: str, expected_item: Optional[str]) -> bool:
        """Assign or clear expected item for a slot at runtime."""
        state = self.state_model.get_slot_state(slot_id)
        if state is None:
            return False

        state.expected_item = self._normalize_item_class(expected_item)
        state.consecutive_absences = 0
        state.consecutive_presences = 0
        self.buffer.clear_slot(slot_id)
        logger.info(f"Updated expected item for {slot_id}: {state.expected_item}")
        return True

    def get_expected_items(self) -> Dict[str, str]:
        """Return expected items mapping for all slots."""
        return {
            slot_id: state.expected_item
            for slot_id, state in self.state_model.states.items()
            if state.expected_item
        }
    
    def reset_slot(self, slot_id: str) -> None:
        """Reset reasoning for a specific slot."""
        self.buffer.clear_slot(slot_id)
        self.state_model.reset_slot(slot_id)
        
        # Clear recent events for this slot
        keys_to_remove = [k for k in self._recent_events if k.startswith(slot_id)]
        for key in keys_to_remove:
            del self._recent_events[key]
        
        logger.info(f"Reset slot: {slot_id}")
    
    def reset_all(self) -> None:
        """Reset all reasoning state."""
        self.buffer.clear_all()
        self.state_model.reset_all()
        self._recent_events.clear()
        for slot_id in self._latest_slot_evidence:
            self._latest_slot_evidence[slot_id] = {
                'fusion_source': 'reset',
                'yolo_item': None,
                'yolo_confidence': 0.0,
                'gemini_status': 'unavailable',
                'gemini_item': None,
                'gemini_confidence': 0.0,
                'resolved_item': None,
                'resolved_confidence': 0.0,
            }
        logger.info("Reasoning engine reset")
