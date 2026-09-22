"""
Helper Utilities for Inventory-Management-Tracking-System.

Common utility functions used across modules.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Output path
        indent: JSON indentation
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, default=str)


def calculate_centroid(bbox: List[int]) -> Tuple[int, int]:
    """
    Calculate centroid from bounding box.
    
    Args:
        bbox: [x1, y1, x2, y2] bounding box
        
    Returns:
        (cx, cy) centroid coordinates
    """
    x1, y1, x2, y2 = bbox
    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)
    return (cx, cy)


def format_timestamp(dt: datetime = None) -> str:
    """
    Format datetime for display.
    
    Args:
        dt: Datetime object (default: now)
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value to range.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def generate_slot_id(row: int, col: int) -> str:
    """
    Generate slot ID from row and column.
    
    Args:
        row: Row index (0-based)
        col: Column index (0-based)
        
    Returns:
        Slot ID string (e.g., 'SLOT_0_1')
    """
    return f"SLOT_{row}_{col}"


def parse_slot_id(slot_id: str) -> Tuple[int, int]:
    """
    Parse slot ID to get row and column.
    
    Args:
        slot_id: Slot ID string (e.g., 'SLOT_0_1')
        
    Returns:
        (row, col) tuple
        
    Raises:
        ValueError: If slot_id format is invalid
    """
    try:
        parts = slot_id.split('_')
        if len(parts) != 3 or parts[0] != 'SLOT':
            raise ValueError
        return (int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        raise ValueError(f"Invalid slot_id format: {slot_id}")
