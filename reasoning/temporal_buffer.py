"""
Temporal Buffer Module for Inventory-Management-Tracking-System.

Maintains rolling window of detections for temporal analysis.
"""

from collections import deque
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single detection observation."""
    timestamp: datetime
    item_class: Optional[str]   # None = empty slot
    confidence: float


class TemporalBuffer:
    """
    Maintains rolling window of detections for each slot.
    
    This buffer allows the reasoning engine to analyze detection
    patterns over time rather than making decisions on single frames.
    
    Attributes:
        window_size: Number of recent detections to store per slot
        buffers: Dictionary of slot_id to deque of detections
    """
    
    def __init__(self, slot_ids: List[str], window_size: int = 10):
        """
        Initialize temporal buffers.
        
        Args:
            slot_ids: List of all slot IDs
            window_size: Number of recent detections to store per slot
        """
        self.window_size = window_size
        self.buffers: Dict[str, deque] = {
            slot_id: deque(maxlen=window_size) 
            for slot_id in slot_ids
        }
        logger.info(f"TemporalBuffer initialized: {len(slot_ids)} slots, "
                   f"window={window_size}")
    
    def add_detection(
        self, 
        slot_id: str, 
        item_class: Optional[str], 
        confidence: float
    ) -> None:
        """
        Add a detection to the buffer.
        
        Args:
            slot_id: Target slot
            item_class: Detected item class (None = empty)
            confidence: Detection confidence
        """
        if slot_id not in self.buffers:
            logger.warning(f"Unknown slot_id: {slot_id}")
            return
        
        detection = Detection(
            timestamp=datetime.now(),
            item_class=item_class,
            confidence=confidence
        )
        self.buffers[slot_id].append(detection)
    
    def get_recent_detections(
        self, 
        slot_id: str, 
        count: Optional[int] = None
    ) -> List[Detection]:
        """
        Get N most recent detections for a slot.
        
        Args:
            slot_id: Target slot
            count: Number of detections (None = all)
            
        Returns:
            List of Detection objects
        """
        if slot_id not in self.buffers:
            return []
        
        buffer = self.buffers[slot_id]
        if count is None:
            return list(buffer)
        return list(buffer)[-count:]
    
    def get_consecutive_absences(self, slot_id: str) -> int:
        """
        Count consecutive frames where slot was detected empty.
        
        Returns:
            Number of consecutive empty detections (from most recent)
        """
        if slot_id not in self.buffers:
            return 0
        
        buffer = list(self.buffers[slot_id])
        if not buffer:
            return 0
        
        count = 0
        for detection in reversed(buffer):
            if detection.item_class is None:
                count += 1
            else:
                break
        
        return count
    
    def get_consecutive_presences(
        self, 
        slot_id: str, 
        item_class: Optional[str] = None
    ) -> int:
        """
        Count consecutive frames where item was detected.
        
        Args:
            slot_id: Target slot
            item_class: Specific item to check for (None = any item)
            
        Returns:
            Number of consecutive detections (from most recent)
        """
        if slot_id not in self.buffers:
            return 0
        
        buffer = list(self.buffers[slot_id])
        if not buffer:
            return 0
        
        count = 0
        for detection in reversed(buffer):
            if detection.item_class is not None:
                if item_class is None or detection.item_class == item_class:
                    count += 1
                else:
                    break
            else:
                break
        
        return count
    
    def get_aggregated_confidence(
        self, 
        slot_id: str
    ) -> Tuple[Optional[str], float]:
        """
        Calculate aggregated confidence for current slot state.
        
        Uses weighted average with recent detections weighted higher.
        
        Returns:
            (most_common_item, aggregated_confidence)
        """
        if slot_id not in self.buffers:
            return (None, 0.0)
        
        buffer = list(self.buffers[slot_id])
        if not buffer:
            return (None, 0.0)
        
        # Generate weights (recent = higher weight)
        n = len(buffer)
        weights = np.linspace(0.5, 1.0, n)
        weights = weights / weights.sum()  # Normalize
        
        # Count item occurrences with weighted confidence
        item_scores: Dict[Optional[str], float] = {}
        
        for i, detection in enumerate(buffer):
            item = detection.item_class
            score = detection.confidence * weights[i]
            
            if item in item_scores:
                item_scores[item] = item_scores[item] + score
            else:
                item_scores[item] = score
        
        if not item_scores:
            return (None, 0.0)
        
        # Find most confident item
        best_item = max(item_scores, key=item_scores.get)
        best_score = item_scores[best_item]
        
        # Calculate aggregated confidence
        total_score = sum(item_scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.0
        
        return (best_item, min(confidence, 1.0))
    
    def has_sustained_mismatch(
        self, 
        slot_id: str, 
        expected_item: str, 
        threshold: int = 3
    ) -> bool:
        """
        Check if a different item has been detected consistently.
        
        Args:
            slot_id: Target slot
            expected_item: What should be in the slot
            threshold: Minimum consecutive mismatches required
            
        Returns:
            True if wrong item detected for ≥threshold consecutive frames
        """
        if slot_id not in self.buffers:
            return False
        
        buffer = list(self.buffers[slot_id])
        if len(buffer) < threshold:
            return False
        
        # Check recent detections
        consecutive_mismatches = 0
        for detection in reversed(buffer):
            if (detection.item_class is not None and 
                detection.item_class != expected_item):
                consecutive_mismatches += 1
            else:
                break
        
        return consecutive_mismatches >= threshold
    
    def is_fluctuating(self, slot_id: str, threshold: int = 3) -> bool:
        """
        Check if detections are highly inconsistent (flickering).
        
        Returns:
            True if detections alternate frequently
        """
        if slot_id not in self.buffers:
            return False
        
        buffer = list(self.buffers[slot_id])
        if len(buffer) < 4:
            return False
        
        # Count state changes in recent buffer
        changes = 0
        prev_state = buffer[0].item_class
        
        for detection in buffer[1:]:
            if detection.item_class != prev_state:
                changes += 1
            prev_state = detection.item_class
        
        # Fluctuating if changes exceed threshold
        return changes >= threshold
    
    def get_most_recent(self, slot_id: str) -> Optional[Detection]:
        """Get most recent detection for a slot."""
        if slot_id not in self.buffers:
            return None
        
        buffer = self.buffers[slot_id]
        if not buffer:
            return None
        
        return buffer[-1]
    
    def clear_slot(self, slot_id: str) -> None:
        """Clear buffer for a specific slot."""
        if slot_id in self.buffers:
            self.buffers[slot_id].clear()
            logger.debug(f"Cleared buffer for {slot_id}")
    
    def clear_all(self) -> None:
        """Clear all buffers."""
        for buffer in self.buffers.values():
            buffer.clear()
        logger.info("All temporal buffers cleared")
    
    def get_buffer_fill(self, slot_id: str) -> float:
        """Get buffer fill percentage (0-1)."""
        if slot_id not in self.buffers:
            return 0.0
        
        buffer = self.buffers[slot_id]
        return len(buffer) / self.window_size
