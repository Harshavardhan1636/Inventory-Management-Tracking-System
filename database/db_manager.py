"""
Database Manager for Inventory-Management-Tracking-System.

Handles database connections and CRUD operations.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict, Optional
from pathlib import Path
import json
import logging

from .models import Base, Inventory, ShelfState, EventLog, InventoryActionLog, AlertModel

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and operations.
    
    Provides high-level interface for all database interactions.
    
    Attributes:
        db_path: Path to SQLite database file
        engine: SQLAlchemy engine
        SessionLocal: Session factory
    """
    
    def __init__(self, db_path: str = "data/shelf.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        logger.info(f"Database initialized: {db_path}")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    # ===== INVENTORY OPERATIONS =====
    
    def get_inventory(self, session: Session = None) -> Dict[str, int]:
        """Get all inventory items as {item_class: quantity} dict."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            items = session.query(Inventory).all()
            result = {item.item_class: item.quantity for item in items}
            return result
        finally:
            if close_session:
                session.close()
    
    def update_inventory(
        self, 
        item_class: str, 
        quantity_change: int,
        session: Session = None
    ) -> bool:
        """
        Update inventory quantity.
        
        Args:
            item_class: Item to update
            quantity_change: Amount to add (can be negative)
            session: Optional existing session
            
        Returns:
            bool: True if successful
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            item = session.query(Inventory).filter_by(item_class=item_class).first()
            
            if not item:
                # Create new item
                item = Inventory(
                    item_class=item_class, 
                    quantity=max(0, quantity_change)
                )
                session.add(item)
            else:
                # Update existing
                new_quantity = item.quantity + quantity_change
                if new_quantity < 0:
                    logger.error(f"Cannot set negative quantity for {item_class}")
                    return False
                item.quantity = new_quantity
            
            session.commit()
            logger.info(f"Updated inventory: {item_class} -> {item.quantity}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating inventory: {e}")
            return False
        finally:
            if close_session:
                session.close()
    
    def set_inventory(
        self, 
        item_class: str, 
        quantity: int,
        session: Session = None
    ) -> bool:
        """Set inventory quantity directly."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            item = session.query(Inventory).filter_by(item_class=item_class).first()
            
            if not item:
                item = Inventory(item_class=item_class, quantity=quantity)
                session.add(item)
            else:
                item.quantity = quantity
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting inventory: {e}")
            return False
        finally:
            if close_session:
                session.close()
    
    def get_inventory_item(
        self, 
        item_class: str, 
        session: Session = None
    ) -> Optional[Dict]:
        """Get single inventory item."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            item = session.query(Inventory).filter_by(item_class=item_class).first()
            return item.to_dict() if item else None
        finally:
            if close_session:
                session.close()
    
    # ===== SHELF STATE OPERATIONS =====
    
    def save_shelf_state(
        self, 
        states: Dict[str, Dict], 
        session: Session = None
    ) -> None:
        """
        Save complete shelf state.
        
        Args:
            states: Dict of {slot_id: state_dict}
            session: Optional existing session
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            for slot_id, state_data in states.items():
                existing = session.query(ShelfState).filter_by(slot_id=slot_id).first()
                
                if existing:
                    # Update existing
                    for key, value in state_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                else:
                    # Create new
                    new_state = ShelfState(slot_id=slot_id, **state_data)
                    session.add(new_state)
            
            session.commit()
            logger.debug(f"Saved shelf state for {len(states)} slots")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving shelf state: {e}")
        finally:
            if close_session:
                session.close()
    
    def get_shelf_state(self, session: Session = None) -> Dict[str, Dict]:
        """Get all shelf states."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            states = session.query(ShelfState).all()
            return {state.slot_id: state.to_dict() for state in states}
        finally:
            if close_session:
                session.close()
    
    # ===== EVENT LOGGING =====
    
    def log_event(self, event_data: Dict, session: Session = None) -> int:
        """
        Log an event to the database.
        
        Args:
            event_data: Event dictionary
            session: Optional existing session
            
        Returns:
            int: Event ID
        """
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            # Convert metadata dict to JSON string
            metadata = event_data.get('metadata')
            if metadata is not None and not isinstance(metadata, str):
                metadata = json.dumps(metadata)
            
            event = EventLog(
                event_type=event_data.get('event_type'),
                slot_id=event_data.get('slot_id'),
                item_class=event_data.get('item_class'),
                confidence=event_data.get('confidence', 0.0),
                event_metadata=metadata
            )
            
            session.add(event)
            session.commit()
            
            logger.debug(f"Logged event: {event.event_id}")
            return event.event_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging event: {e}")
            return -1
        finally:
            if close_session:
                session.close()
    
    def get_recent_events(
        self, 
        limit: int = 50, 
        session: Session = None
    ) -> List[Dict]:
        """Get recent events."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            events = session.query(EventLog)\
                           .order_by(EventLog.timestamp.desc())\
                           .limit(limit)\
                           .all()
            return [event.to_dict() for event in events]
        finally:
            if close_session:
                session.close()
    
    # ===== INVENTORY ACTIONS LOGGING =====
    
    def log_action(self, action_data: Dict, session: Session = None) -> int:
        """Log an inventory action."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            action = InventoryActionLog(
                action_type=action_data.get('action_type'),
                item_class=action_data.get('item_class'),
                slot_id=action_data.get('slot_id'),
                quantity_change=action_data.get('quantity_change', 0),
                reason=action_data.get('reason'),
                confidence=action_data.get('confidence')
            )
            session.add(action)
            session.commit()
            
            logger.debug(f"Logged action: {action.action_id}")
            return action.action_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging action: {e}")
            return -1
        finally:
            if close_session:
                session.close()
    
    def get_recent_actions(
        self, 
        limit: int = 50, 
        session: Session = None
    ) -> List[Dict]:
        """Get recent inventory actions."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            actions = session.query(InventoryActionLog)\
                            .order_by(InventoryActionLog.timestamp.desc())\
                            .limit(limit)\
                            .all()
            return [action.to_dict() for action in actions]
        finally:
            if close_session:
                session.close()
    
    # ===== ALERTS =====
    
    def save_alert(self, alert_data: Dict, session: Session = None) -> None:
        """Save an alert to database."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            alert = AlertModel(
                alert_id=alert_data.get('alert_id'),
                level=alert_data.get('level'),
                title=alert_data.get('title'),
                message=alert_data.get('message'),
                item_class=alert_data.get('item_class'),
                slot_id=alert_data.get('slot_id'),
                acknowledged=alert_data.get('acknowledged', False)
            )
            session.add(alert)
            session.commit()
            logger.debug(f"Saved alert: {alert.alert_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving alert: {e}")
        finally:
            if close_session:
                session.close()
    
    def get_active_alerts(self, session: Session = None) -> List[Dict]:
        """Get unacknowledged alerts."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            alerts = session.query(AlertModel)\
                           .filter_by(acknowledged=False)\
                           .order_by(AlertModel.timestamp.desc())\
                           .all()
            return [alert.to_dict() for alert in alerts]
        finally:
            if close_session:
                session.close()
    
    def acknowledge_alert_db(
        self, 
        alert_id: str, 
        session: Session = None
    ) -> bool:
        """Acknowledge an alert in database."""
        close_session = False
        if session is None:
            session = self.get_session()
            close_session = True
        
        try:
            alert = session.query(AlertModel).filter_by(alert_id=alert_id).first()
            if alert:
                alert.acknowledged = True
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Error acknowledging alert: {e}")
            return False
        finally:
            if close_session:
                session.close()
