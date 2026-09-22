"""
Alert System Module for Inventory-Management-Tracking-System.

Manages system alerts and notifications.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Represents a system alert."""
    
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    item_class: Optional[str] = None
    slot_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'alert_id': self.alert_id,
            'level': self.level.value,
            'title': self.title,
            'message': self.message,
            'item_class': self.item_class,
            'slot_id': self.slot_id,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged
        }
    
    def __str__(self) -> str:
        return f"Alert[{self.level.value.upper()}]: {self.title}"


class AlertSystem:
    """
    Manages system alerts and notifications.
    
    Handles alert generation, storage, and acknowledgment.
    
    Attributes:
        alerts: List of all alerts
        max_alerts: Maximum alerts to keep in memory
    """
    
    def __init__(self, max_alerts: int = 100):
        """
        Initialize alert system.
        
        Args:
            max_alerts: Maximum alerts to keep in memory
        """
        self.alerts: List[Alert] = []
        self.max_alerts = max_alerts
        self._alert_counter = 0
        self._last_alerts: Dict[str, datetime] = {}
        
        logger.info("AlertSystem initialized")

    def _should_emit(self, key: Optional[str], cooldown_seconds: float) -> bool:
        """Check cooldown window to prevent repetitive alerts."""
        if not key:
            return True

        cooldown = max(0.0, float(cooldown_seconds))
        now = datetime.now()
        last = self._last_alerts.get(key)

        if last is not None and cooldown > 0:
            elapsed = (now - last).total_seconds()
            if elapsed < cooldown:
                return False

        self._last_alerts[key] = now
        return True
    
    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        item_class: Optional[str] = None,
        slot_id: Optional[str] = None
    ) -> Alert:
        """
        Create and store a new alert.
        
        Args:
            level: Alert severity level
            title: Alert title
            message: Alert message
            item_class: Related item (optional)
            slot_id: Related slot (optional)
            
        Returns:
            Created alert
        """
        self._alert_counter += 1
        alert_id = f"ALERT_{uuid4().hex[:12].upper()}"
        
        alert = Alert(
            alert_id=alert_id,
            level=level,
            title=title,
            message=message,
            item_class=item_class,
            slot_id=slot_id,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Trim old alerts if exceeding max
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        logger.info(f"Alert created: {alert.alert_id} - {title}")
        return alert
    
    def create_info(
        self, 
        title: str, 
        message: str, 
        **kwargs
    ) -> Alert:
        """Create INFO level alert."""
        return self.create_alert(AlertLevel.INFO, title, message, **kwargs)
    
    def create_warning(
        self, 
        title: str, 
        message: str, 
        **kwargs
    ) -> Alert:
        """Create WARNING level alert."""
        return self.create_alert(AlertLevel.WARNING, title, message, **kwargs)
    
    def create_critical(
        self, 
        title: str, 
        message: str, 
        **kwargs
    ) -> Alert:
        """Create CRITICAL level alert."""
        return self.create_alert(AlertLevel.CRITICAL, title, message, **kwargs)

    def create_alert_once(
        self,
        key: Optional[str],
        level: AlertLevel,
        title: str,
        message: str,
        cooldown_seconds: float = 60.0,
        **kwargs
    ) -> Optional[Alert]:
        """Create an alert only if cooldown has elapsed for the key."""
        if not self._should_emit(key, cooldown_seconds):
            return None

        return self.create_alert(level, title, message, **kwargs)

    def create_info_once(
        self,
        key: Optional[str],
        title: str,
        message: str,
        cooldown_seconds: float = 60.0,
        **kwargs
    ) -> Optional[Alert]:
        """Create INFO alert with cooldown protection."""
        return self.create_alert_once(
            key,
            AlertLevel.INFO,
            title,
            message,
            cooldown_seconds=cooldown_seconds,
            **kwargs
        )

    def create_warning_once(
        self,
        key: Optional[str],
        title: str,
        message: str,
        cooldown_seconds: float = 60.0,
        **kwargs
    ) -> Optional[Alert]:
        """Create WARNING alert with cooldown protection."""
        return self.create_alert_once(
            key,
            AlertLevel.WARNING,
            title,
            message,
            cooldown_seconds=cooldown_seconds,
            **kwargs
        )

    def create_critical_once(
        self,
        key: Optional[str],
        title: str,
        message: str,
        cooldown_seconds: float = 60.0,
        **kwargs
    ) -> Optional[Alert]:
        """Create CRITICAL alert with cooldown protection."""
        return self.create_alert_once(
            key,
            AlertLevel.CRITICAL,
            title,
            message,
            cooldown_seconds=cooldown_seconds,
            **kwargs
        )
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all unacknowledged alerts."""
        return [a for a in self.alerts if not a.acknowledged]
    
    def get_all_alerts(self) -> List[Alert]:
        """Get all alerts."""
        return self.alerts.copy()
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get specific alert by ID."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                return alert
        return None
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Mark an alert as acknowledged.
        
        Args:
            alert_id: Alert to acknowledge
            
        Returns:
            bool: True if found and acknowledged
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
        return False
    
    def acknowledge_all(self) -> int:
        """
        Acknowledge all active alerts.
        
        Returns:
            Number of alerts acknowledged
        """
        count = 0
        for alert in self.alerts:
            if not alert.acknowledged:
                alert.acknowledged = True
                count += 1
        
        logger.info(f"Acknowledged {count} alerts")
        return count
    
    def clear_acknowledged(self) -> int:
        """
        Remove all acknowledged alerts.
        
        Returns:
            Number of alerts removed
        """
        original_count = len(self.alerts)
        self.alerts = [a for a in self.alerts if not a.acknowledged]
        removed = original_count - len(self.alerts)
        
        logger.info(f"Cleared {removed} acknowledged alerts")
        return removed
    
    def get_critical_alerts(self) -> List[Alert]:
        """Get all critical unacknowledged alerts."""
        return [
            a for a in self.alerts 
            if a.level == AlertLevel.CRITICAL and not a.acknowledged
        ]
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """Get all alerts of a specific level."""
        return [a for a in self.alerts if a.level == level]
    
    def get_alerts_for_item(self, item_class: str) -> List[Alert]:
        """Get all alerts for a specific item."""
        return [a for a in self.alerts if a.item_class == item_class]
    
    def get_alerts_for_slot(self, slot_id: str) -> List[Alert]:
        """Get all alerts for a specific slot."""
        return [a for a in self.alerts if a.slot_id == slot_id]
    
    def get_alert_counts(self) -> Dict[str, int]:
        """Get count of alerts by level."""
        return {
            'info': len([a for a in self.alerts if a.level == AlertLevel.INFO]),
            'warning': len([a for a in self.alerts if a.level == AlertLevel.WARNING]),
            'critical': len([a for a in self.alerts if a.level == AlertLevel.CRITICAL]),
            'active': len(self.get_active_alerts()),
            'total': len(self.alerts)
        }
    
    def to_dict(self) -> List[Dict]:
        """Serialize all alerts."""
        return [alert.to_dict() for alert in self.alerts]
