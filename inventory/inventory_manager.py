"""
Inventory Manager Module for Inventory-Management-Tracking-System.

Manages inventory state and CRUD operations.
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InventoryItem:
    """Represents a single inventory item."""
    
    def __init__(
        self,
        item_class: str,
        quantity: int = 0,
        low_stock_threshold: int = 2
    ):
        """
        Initialize inventory item.
        
        Args:
            item_class: Item class name
            quantity: Initial quantity
            low_stock_threshold: When to trigger low stock
        """
        self.item_class = item_class
        self.quantity = quantity
        self.low_stock_threshold = low_stock_threshold
        self.last_updated = datetime.now()
    
    def is_low_stock(self) -> bool:
        """Check if item is low stock."""
        return self.quantity > 0 and self.quantity <= self.low_stock_threshold
    
    def is_out_of_stock(self) -> bool:
        """Check if item is out of stock."""
        return self.quantity == 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'item_class': self.item_class,
            'quantity': self.quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'is_low_stock': self.is_low_stock(),
            'is_out_of_stock': self.is_out_of_stock(),
            'last_updated': self.last_updated.isoformat()
        }


class InventoryManager:
    """
    Manages inventory state and updates.
    
    This is the single source of truth for inventory quantities.
    All inventory changes flow through this manager.
    
    Attributes:
        items: Dictionary of item_class to InventoryItem
    """
    
    def __init__(
        self, 
        initial_inventory: Dict[str, int] = None,
        low_stock_threshold: int = 2
    ):
        """
        Initialize inventory manager.
        
        Args:
            initial_inventory: Initial quantities {item_class: quantity}
            low_stock_threshold: Default low stock threshold
        """
        self.items: Dict[str, InventoryItem] = {}
        self.low_stock_threshold = low_stock_threshold
        
        if initial_inventory:
            for item_class, quantity in initial_inventory.items():
                self.items[item_class] = InventoryItem(
                    item_class, 
                    quantity, 
                    low_stock_threshold
                )
        
        logger.info(f"InventoryManager initialized with {len(self.items)} items")
    
    def get_item(self, item_class: str) -> Optional[InventoryItem]:
        """Get inventory item by class."""
        return self.items.get(item_class)
    
    def get_quantity(self, item_class: str) -> int:
        """Get current quantity of an item."""
        item = self.items.get(item_class)
        return item.quantity if item else 0
    
    def get_all_items(self) -> Dict[str, InventoryItem]:
        """Get all inventory items."""
        return self.items.copy()
    
    def get_inventory_dict(self) -> Dict[str, int]:
        """Get inventory as {item_class: quantity} dict."""
        return {
            item_class: item.quantity
            for item_class, item in self.items.items()
        }
    
    def increment(self, item_class: str, amount: int = 1) -> bool:
        """
        Increment item quantity.
        
        Args:
            item_class: Item to increment
            amount: Amount to add (default: 1)
            
        Returns:
            bool: True if successful
        """
        if item_class not in self.items:
            # Auto-create item if doesn't exist
            self.items[item_class] = InventoryItem(
                item_class, 
                0, 
                self.low_stock_threshold
            )
        
        item = self.items[item_class]
        item.quantity += amount
        item.last_updated = datetime.now()
        
        logger.info(f"Incremented {item_class}: +{amount} (now {item.quantity})")
        return True
    
    def decrement(self, item_class: str, amount: int = 1) -> bool:
        """
        Decrement item quantity.
        
        Args:
            item_class: Item to decrement
            amount: Amount to subtract (default: 1)
            
        Returns:
            bool: True if successful, False if would go negative
        """
        if item_class not in self.items:
            logger.error(f"Cannot decrement unknown item: {item_class}")
            return False
        
        item = self.items[item_class]
        
        if item.quantity - amount < 0:
            logger.error(
                f"Cannot decrement {item_class}: "
                f"would go negative ({item.quantity} - {amount})"
            )
            return False
        
        item.quantity -= amount
        item.last_updated = datetime.now()
        
        logger.info(f"Decremented {item_class}: -{amount} (now {item.quantity})")
        
        # Check for low stock
        if item.is_low_stock():
            logger.warning(f"LOW STOCK: {item_class} = {item.quantity}")
        
        return True
    
    def set_quantity(self, item_class: str, quantity: int) -> bool:
        """
        Set item quantity directly.
        
        Use with caution - prefer increment/decrement for tracking.
        
        Args:
            item_class: Item to set
            quantity: New quantity
            
        Returns:
            bool: True if successful
        """
        if quantity < 0:
            logger.error(f"Cannot set negative quantity: {quantity}")
            return False
        
        if item_class not in self.items:
            self.items[item_class] = InventoryItem(
                item_class, 
                quantity, 
                self.low_stock_threshold
            )
        else:
            self.items[item_class].quantity = quantity
            self.items[item_class].last_updated = datetime.now()
        
        logger.info(f"Set {item_class} quantity to {quantity}")
        return True
    
    def add_item(
        self, 
        item_class: str, 
        quantity: int = 0,
        low_stock_threshold: int = None
    ) -> InventoryItem:
        """
        Add new item to inventory.
        
        Args:
            item_class: Item class name
            quantity: Initial quantity
            low_stock_threshold: Custom threshold (optional)
            
        Returns:
            Created InventoryItem
        """
        threshold = low_stock_threshold or self.low_stock_threshold
        
        item = InventoryItem(item_class, quantity, threshold)
        self.items[item_class] = item
        
        logger.info(f"Added item: {item_class} (qty={quantity})")
        return item
    
    def remove_item(self, item_class: str) -> bool:
        """
        Remove item from inventory.
        
        Args:
            item_class: Item to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        if item_class in self.items:
            del self.items[item_class]
            logger.info(f"Removed item: {item_class}")
            return True
        return False
    
    def get_low_stock_items(self) -> List[InventoryItem]:
        """Get all items with low stock."""
        return [
            item for item in self.items.values()
            if item.is_low_stock()
        ]
    
    def get_out_of_stock_items(self) -> List[InventoryItem]:
        """Get all items that are out of stock."""
        return [
            item for item in self.items.values()
            if item.is_out_of_stock()
        ]
    
    def to_dict(self) -> Dict:
        """Serialize inventory state."""
        return {
            item_class: item.to_dict()
            for item_class, item in self.items.items()
        }
    
    def get_total_items(self) -> int:
        """Get total number of item types."""
        return len(self.items)
    
    def get_total_units(self) -> int:
        """Get total number of units across all items."""
        return sum(item.quantity for item in self.items.values())
