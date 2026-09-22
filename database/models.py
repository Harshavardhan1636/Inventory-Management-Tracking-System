"""
Database Models for Inventory-Management-Tracking-System.

SQLAlchemy ORM models for persistence.
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, CheckConstraint
)
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class Inventory(Base):
    """Inventory table model."""
    __tablename__ = 'inventory'
    
    item_class = Column(String, primary_key=True)
    quantity = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=False, default=2)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_non_negative_quantity'),
    )
    
    def to_dict(self):
        return {
            'item_class': self.item_class,
            'quantity': self.quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class ShelfState(Base):
    """Shelf state table model."""
    __tablename__ = 'shelf_state'
    
    slot_id = Column(String, primary_key=True)
    expected_item = Column(String, nullable=True)
    current_item = Column(String, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    state_status = Column(String, default='UNKNOWN')
    consecutive_absences = Column(Integer, default=0)
    consecutive_presences = Column(Integer, default=0)
    last_confirmed = Column(DateTime, nullable=True)
    
    __table_args__ = (
        CheckConstraint('confidence >= 0.0 AND confidence <= 1.0', 
                       name='check_confidence_range'),
    )
    
    def to_dict(self):
        return {
            'slot_id': self.slot_id,
            'expected_item': self.expected_item,
            'current_item': self.current_item,
            'confidence': self.confidence,
            'state_status': self.state_status,
            'last_confirmed': self.last_confirmed.isoformat() if self.last_confirmed else None
        }


class EventLog(Base):
    """Events log table model."""
    __tablename__ = 'events_log'
    
    event_id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String, nullable=False)
    slot_id = Column(String, nullable=False)
    item_class = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    event_metadata = Column(Text, nullable=True)  # JSON string (renamed from metadata)
    
    def to_dict(self):
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'slot_id': self.slot_id,
            'item_class': self.item_class,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'metadata': self.event_metadata  # return as 'metadata' for API compatibility
        }


class InventoryActionLog(Base):
    """Inventory actions table model."""
    __tablename__ = 'inventory_actions'
    
    action_id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String, nullable=False)
    item_class = Column(String, nullable=False)
    slot_id = Column(String, nullable=True)
    quantity_change = Column(Integer, default=0)
    reason = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'action_id': self.action_id,
            'action_type': self.action_type,
            'item_class': self.item_class,
            'slot_id': self.slot_id,
            'quantity_change': self.quantity_change,
            'reason': self.reason,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class AlertModel(Base):
    """Alerts table model."""
    __tablename__ = 'alerts'
    
    alert_id = Column(String, primary_key=True)
    level = Column(String, nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    item_class = Column(String, nullable=True)
    slot_id = Column(String, nullable=True)
    acknowledged = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'alert_id': self.alert_id,
            'level': self.level,
            'title': self.title,
            'message': self.message,
            'item_class': self.item_class,
            'slot_id': self.slot_id,
            'acknowledged': self.acknowledged,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
