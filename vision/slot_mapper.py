"""
Slot Mapper Module for Inventory-Management-Tracking-System.

Maps object detections to predefined shelf slots.
"""

import numpy as np
import cv2
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SlotMapper:
    """
    Maps object detections to predefined shelf slots.
    
    Divides the camera frame into a grid of slots and assigns
    detected objects to slots based on centroid location.
    
    Attributes:
        frame_width: Camera frame width
        frame_height: Camera frame height
        rows: Number of rows in grid
        cols: Number of columns in grid
        slots: Dictionary of slot boundaries
    """
    
    def __init__(
        self,
        frame_width: int,
        frame_height: int,
        layout_config_path: str
    ):
        """
        Initialize slot mapper with shelf layout.
        
        Args:
            frame_width: Camera frame width
            frame_height: Camera frame height
            layout_config_path: Path to JSON layout configuration
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.layout_config_path = Path(layout_config_path)
        
        # Load layout configuration
        self.layout = self._load_layout(layout_config_path)
        
        self.rows = self.layout.get('rows', 2)
        self.cols = self.layout.get('cols', 3)
        
        # Get shelf region
        self.shelf_region = self.layout.get('shelf_region', {
            'x1': 0,
            'y1': 0,
            'x2': frame_width,
            'y2': frame_height
        })
        
        # Expected items per slot
        raw_expected_items = self.layout.get('expected_items', {})
        self.expected_items: Dict[str, str] = {}
        for slot_id, item_class in raw_expected_items.items():
            normalized = self._normalize_item_class(item_class)
            if normalized:
                self.expected_items[str(slot_id)] = normalized
        self.layout['expected_items'] = self.expected_items.copy()
        
        # Calculate slot boundaries
        self.slots: Dict[str, Dict[str, int]] = {}
        self._calculate_slots()
        
        logger.info(f"SlotMapper initialized: {self.rows}x{self.cols} grid, "
                   f"{len(self.slots)} slots")
    
    def _load_layout(self, path: str) -> Dict:
        """Load layout configuration from JSON file."""
        config_path = Path(path)
        
        if not config_path.exists():
            logger.warning(f"Layout config not found: {path}, using defaults")
            return {
                'rows': 2,
                'cols': 3,
                'shelf_region': {
                    'x1': 100,
                    'y1': 100,
                    'x2': self.frame_width - 100,
                    'y2': self.frame_height - 100
                },
                'expected_items': {}
            }
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                layout = json.load(f)
            logger.info(f"Loaded layout: {layout.get('name', 'unnamed')}")
            return layout
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in layout config: {e}")
            raise ValueError(f"Invalid layout configuration: {e}")

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
    
    def _calculate_slots(self) -> None:
        """Calculate slot boundaries from shelf region."""
        region = self.shelf_region
        x1, y1 = region['x1'], region['y1']
        x2, y2 = region['x2'], region['y2']
        
        # Calculate slot dimensions
        slot_width = (x2 - x1) // self.cols
        slot_height = (y2 - y1) // self.rows
        
        # Create slot boundaries
        for row in range(self.rows):
            for col in range(self.cols):
                slot_id = f"SLOT_{row}_{col}"
                
                self.slots[slot_id] = {
                    'x1': x1 + col * slot_width,
                    'y1': y1 + row * slot_height,
                    'x2': x1 + (col + 1) * slot_width,
                    'y2': y1 + (row + 1) * slot_height,
                    'row': row,
                    'col': col
                }
        
        logger.debug(f"Calculated {len(self.slots)} slot boundaries")
    
    def map_to_slot(self, centroid: Tuple[int, int]) -> Optional[str]:
        """
        Determine which slot contains the given centroid.
        
        Args:
            centroid: (x, y) coordinates
            
        Returns:
            Slot ID (e.g., 'SLOT_1_2') or None if outside shelf area
        """
        x, y = centroid
        
        # Check if within shelf region
        region = self.shelf_region
        if not (region['x1'] <= x <= region['x2'] and 
                region['y1'] <= y <= region['y2']):
            return None
        
        # Find matching slot
        for slot_id, bounds in self.slots.items():
            if (bounds['x1'] <= x < bounds['x2'] and 
                bounds['y1'] <= y < bounds['y2']):
                return slot_id
        
        return None
    
    def get_slot_bounds(self, slot_id: str) -> Optional[Dict[str, int]]:
        """
        Get pixel boundaries of a slot.
        
        Args:
            slot_id: Slot ID (e.g., 'SLOT_0_1')
            
        Returns:
            {'x1': int, 'y1': int, 'x2': int, 'y2': int} or None
        """
        return self.slots.get(slot_id)
    
    def get_expected_item(self, slot_id: str) -> Optional[str]:
        """
        Get expected item for a slot.
        
        Args:
            slot_id: Slot ID
            
        Returns:
            Expected item class or None
        """
        return self.expected_items.get(slot_id)

    def set_expected_item(self, slot_id: str, item_class: Optional[str], persist: bool = True) -> bool:
        """
        Assign or clear an expected item for a slot.

        Args:
            slot_id: Slot ID to update
            item_class: Expected item class (None/empty clears assignment)
            persist: Persist update back to layout JSON file

        Returns:
            bool: True on success
        """
        if slot_id not in self.slots:
            logger.warning(f"Cannot assign expected item: unknown slot_id={slot_id}")
            return False

        normalized = self._normalize_item_class(item_class)
        if normalized:
            self.expected_items[slot_id] = normalized
        else:
            self.expected_items.pop(slot_id, None)

        self.layout['expected_items'] = self.expected_items.copy()

        if persist:
            self._persist_layout()

        return True

    def _persist_layout(self) -> None:
        """Persist current layout (including expected_items) to disk."""
        try:
            if not self.layout_config_path.exists() or not self.layout_config_path.is_file():
                logger.warning(
                    f"Layout file does not exist, expected items kept in memory only: {self.layout_config_path}"
                )
                return

            with open(self.layout_config_path, 'w', encoding='utf-8') as layout_file:
                json.dump(self.layout, layout_file, indent=2)
                layout_file.write('\n')
            logger.info(f"Persisted slot expected-item updates to {self.layout_config_path}")
        except Exception as exc:
            logger.warning(f"Failed to persist layout updates: {exc}")
    
    def draw_slots(
        self,
        frame: np.ndarray,
        show_labels: bool = True,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Draw slot grid overlay on frame.
        
        Args:
            frame: Input image (BGR)
            show_labels: Whether to show slot labels
            color: Line color (BGR)
            thickness: Line thickness
            
        Returns:
            Frame with slot grid drawn
        """
        annotated = frame.copy()
        
        # Draw shelf region boundary
        region = self.shelf_region
        cv2.rectangle(
            annotated,
            (region['x1'], region['y1']),
            (region['x2'], region['y2']),
            (255, 255, 255),
            1
        )
        
        # Draw each slot
        for slot_id, bounds in self.slots.items():
            # Draw rectangle
            cv2.rectangle(
                annotated,
                (bounds['x1'], bounds['y1']),
                (bounds['x2'], bounds['y2']),
                color,
                thickness
            )
            
            # Draw label
            if show_labels:
                label = slot_id.replace('SLOT_', '')
                label_pos = (bounds['x1'] + 5, bounds['y1'] + 20)
                cv2.putText(
                    annotated,
                    label,
                    label_pos,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )
        
        return annotated
    
    def draw_detection(
        self,
        frame: np.ndarray,
        detection: Dict,
        color: Tuple[int, int, int] = (0, 255, 255)
    ) -> np.ndarray:
        """
        Draw detection bounding box and info on frame.
        
        Args:
            frame: Input image
            detection: Detection dictionary
            color: Bounding box color
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        bbox = detection['bbox']
        x1, y1, x2, y2 = bbox
        
        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        
        # Draw label
        label = f"{detection['class_name']} {detection['confidence']:.2f}"
        slot_id = detection.get('slot_id', 'N/A')
        label = f"{label} [{slot_id}]"
        
        # Label background
        (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(annotated, (x1, y1 - 20), (x1 + w, y1), color, -1)
        
        # Label text
        cv2.putText(
            annotated,
            label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1
        )
        
        # Draw centroid
        cx, cy = detection['centroid']
        cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)
        
        return annotated
    
    def get_all_slot_ids(self) -> List[str]:
        """Get list of all slot IDs."""
        return list(self.slots.keys())
    
    def get_slot_center(self, slot_id: str) -> Optional[Tuple[int, int]]:
        """
        Get center point of a slot.
        
        Args:
            slot_id: Slot ID
            
        Returns:
            (x, y) center coordinates or None
        """
        bounds = self.slots.get(slot_id)
        if bounds:
            cx = (bounds['x1'] + bounds['x2']) // 2
            cy = (bounds['y1'] + bounds['y2']) // 2
            return (cx, cy)
        return None
    
    def update_shelf_region(
        self,
        x1: int, y1: int, x2: int, y2: int
    ) -> None:
        """
        Update shelf region and recalculate slots.
        
        Args:
            x1, y1: Top-left corner
            x2, y2: Bottom-right corner
        """
        self.shelf_region = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2}
        self._calculate_slots()
        logger.info(f"Shelf region updated: ({x1},{y1}) to ({x2},{y2})")
