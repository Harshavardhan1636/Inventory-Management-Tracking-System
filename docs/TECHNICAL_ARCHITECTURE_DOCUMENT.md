# Inventory-Management-Tracking-System - Technical Architecture Document

**Project:** Inventory-Management-Tracking-System
**Version:** 1.0.0  
**Document Version:** 1.0  
**Date:** April 2026

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Technology Stack](#3-technology-stack)
4. [System Architecture](#4-system-architecture)
5. [UML Diagrams](#5-uml-diagrams)
6. [Database Design](#6-database-design)
7. [API Specifications](#7-api-specifications)

---

## 1. Introduction

### 1.1 Purpose
This document provides a comprehensive technical architecture overview of the Inventory-Management-Tracking-System, an AI-powered vision-based inventory tracking system.

### 1.2 Scope
This document covers the system architecture, component interactions, database design, and UML diagrams for Inventory-Management-Tracking-System. Demo mode functionality is excluded as per requirements.

### 1.3 System Description
Inventory-Management-Tracking-System is an intelligent inventory management system that uses computer vision (YOLOv8) and temporal reasoning to automatically track inventory changes on retail shelves in real-time.

---

## 2. System Overview

### 2.1 Key Features
- Real-time object detection using YOLOv8
- Temporal state reasoning for noise filtering
- Automatic inventory tracking
- Web-based dashboard with live video feed
- Event logging and alert system
- RESTful API with WebSocket support

### 2.2 System Capabilities
- 30 FPS video processing
- 80 COCO object class detection
- Multi-slot shelf monitoring
- Real-time inventory updates
- Historical event tracking
- Configurable alert thresholds

---

## 3. Technology Stack

### 3.1 Core Technologies

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend Framework** | Flask | 3.0.0 | Web application server |
| **Real-time Communication** | Flask-SocketIO | 5.3.4 | WebSocket handling |
| **Object Detection** | Ultralytics YOLOv8 | 8.3.0+ | Computer vision model |
| **Deep Learning** | PyTorch | 2.6+ | Neural network backend |
| **Computer Vision** | OpenCV | 4.8.1 | Image processing |
| **Database** | SQLite | 3.x | Data persistence |
| **ORM** | SQLAlchemy | 2.0.21 | Database abstraction |
| **Configuration** | PyYAML | 6.0.1 | Config management |
| **Frontend** | HTML/CSS/JavaScript | - | User interface |

### 3.2 Development Tools
- Python 3.8+
- Pytest 7.4.3 (Testing)
- Black 23.10.1 (Code formatting)
- NumPy 1.24.3 (Numerical computing)

---

## 4. System Architecture

### 4.1 Overall Architecture

Inventory-Management-Tracking-System follows a layered architecture pattern with six distinct layers:

```
┌─────────────────────────────────────────────────────────┐
│                  Layer 6: Presentation                  │
│                  (Frontend - HTML/CSS/JS)               │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP + WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                   Layer 5: API Layer                    │
│            (Flask Routes + WebSocket Handlers)          │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼─────┐ ┌──────▼──────┐
│   Layer 4:   │ │ Layer 3: │ │  Layer 2:   │
│  Inventory   │ │Reasoning │ │   Vision    │
│ Management   │ │  Engine  │ │  Pipeline   │
└───────┬──────┘ └────┬─────┘ └──────┬──────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              Layer 1: Persistence Layer                 │
│                   (SQLite Database)                     │
└─────────────────────────────────────────────────────────┘
```

---

### 4.1.1 Frontend Layer

**Technology:** HTML5, CSS3, Vanilla JavaScript

**Components:**

1. **Dashboard (index.html)**
   - Live video stream display
   - Real-time statistics panel
   - Quick action controls
   - Recent events feed

2. **Inventory Page (inventory.html)**
   - Item list with quantities
   - CRUD operations interface
   - Search and filter functionality
   - Low stock indicators

3. **Events Page (events.html)**
   - Chronological event timeline
   - Event filtering by type
   - Confidence score display
   - Export functionality

4. **Alerts Page (alerts.html)**
   - Active alerts display
   - Alert acknowledgment interface
   - Alert level indicators
   - Clear history functionality

**JavaScript Modules:**

```javascript
// Main modules
├── main.js              // Dashboard logic
├── live_feed.js         // Video stream handling
├── inventory.js         // Inventory management
├── events.js            // Event timeline
└── websocket_client.js  // WebSocket connection
```

**Frontend Responsibilities:**
- Render user interface
- Handle user interactions
- Display live video stream
- Real-time updates via WebSocket
- Client-side form validation
- Data visualization

**Communication:**
- REST API calls for CRUD operations
- WebSocket for real-time push notifications
- MJPEG stream for video feed

---

### 4.1.2 API Request Layer

**Technology:** Flask RESTful Routes + Flask-SocketIO

**Architecture Pattern:** RESTful API with WebSocket augmentation

#### REST API Endpoints

**System Endpoints:**
```
GET  /api/health           # System health check
GET  /                     # Dashboard page
GET  /inventory            # Inventory page
GET  /events               # Events page
GET  /alerts               # Alerts page
```

**Inventory Endpoints:**
```
GET    /api/inventory              # Get all inventory
GET    /api/inventory/<item>       # Get specific item
POST   /api/inventory/<item>       # Create/update item
PUT    /api/inventory/<item>       # Adjust quantity
DELETE /api/inventory/<item>       # Delete item
```

**Event Endpoints:**
```
GET  /api/events                   # Get event history
     Query params: limit, event_type, slot_id, item_class
```

**Shelf State Endpoints:**
```
GET  /api/shelf-state              # Get current shelf state
```

**Alert Endpoints:**
```
GET    /api/alerts                 # Get all alerts
PUT    /api/alerts/<alert_id>      # Acknowledge alert
DELETE /api/alerts                 # Clear acknowledged alerts
```

**Video Stream:**
```
GET  /api/video-stream             # MJPEG video stream
```

#### WebSocket Events

**Server → Client:**
```javascript
'event'                // New state transition event
'inventory_update'     // Inventory quantity changed
'alert'                // New alert generated
'shelf_state_update'   // Slot state changed
```

**Client → Server:**
```javascript
'stream_control'       // Start/stop video processing
  Payload: { action: 'start' | 'stop' }
```

**Request Flow:**
```
Client Request → Flask Route Handler → Business Logic Layer
                                     ↓
                              Database Operations
                                     ↓
                              Response Generation
                                     ↓
                           JSON Response/Stream
```

**Error Handling:**
- 400 Bad Request (invalid input)
- 404 Not Found (resource missing)
- 409 Conflict (state conflict)
- 500 Internal Server Error

**Authentication:** Currently no authentication (development mode)

---

### 4.1.3 Backend Layer

**Technology:** Python 3.8+, Flask 3.0.0

The backend consists of multiple interconnected modules:

#### 4.1.3.1 Main Application (main.py)

**Responsibilities:**
- System initialization
- Component orchestration
- Background thread management
- Configuration loading

**Initialization Sequence:**
```python
1. Load configuration from YAML
2. Setup logging system
3. Initialize database connection
4. Create vision pipeline (camera + detector + mapper)
5. Initialize reasoning engine
6. Initialize inventory system
7. Start Flask/SocketIO server
8. Start background processing loop
```

**Background Processing Thread:**
```python
while system_running:
    # Get detections from vision pipeline
    frame, detections = vision_pipeline.get_detections()
    
    # Process through reasoning engine
    events = reasoning_engine.process_detections(detections)
    
    # Process events through decision engine
    actions = decision_engine.process_events(events)
    
    # Execute inventory actions
    for action in actions:
        inventory_manager.execute_action(action)
        
    # Generate alerts if needed
    alerts = alert_system.check_thresholds()
    
    # Broadcast updates via WebSocket
    socketio.emit('event', events)
    socketio.emit('inventory_update', inventory)
    socketio.emit('alert', alerts)
```

#### 4.1.3.2 Vision Pipeline Module

**Location:** `vision/`

**Components:**

1. **CameraStream (camera.py)**
```python
class CameraStream:
    """Threaded camera capture with frame buffering"""
    
    Responsibilities:
    - Initialize camera device
    - Continuous frame capture (background thread)
    - Frame buffering (deque)
    - FPS management
    - Camera health monitoring
    
    Key Methods:
    - start() → Start capture thread
    - get_frame() → Get latest frame
    - stop() → Stop capture
    - is_opened() → Check camera status
```

2. **ObjectDetector (detector.py)**
```python
class ObjectDetector:
    """YOLOv8 detection wrapper"""
    
    Responsibilities:
    - Load YOLOv8 model
    - Run inference on frames
    - Filter by confidence threshold
    - Calculate centroids
    - GPU/CPU management
    
    Key Methods:
    - detect(frame) → List[Detection]
    - set_confidence(threshold) → Update threshold
    
    Detection Format:
    {
        'class': str,           # Object class name
        'confidence': float,    # 0.0-1.0
        'bbox': (x1,y1,x2,y2), # Bounding box
        'centroid': (x, y)     # Center point
    }
```

3. **SlotMapper (slot_mapper.py)**
```python
class SlotMapper:
    """Maps detections to shelf grid slots"""
    
    Responsibilities:
    - Load shelf layout configuration
    - Calculate slot boundaries
    - Map centroids to slots
    - Draw grid overlay
    
    Key Methods:
    - map_to_slots(detections) → Dict[slot_id, detection]
    - get_slot_for_point(x, y) → slot_id
    - draw_grid(frame) → annotated_frame
    
    Slot ID Format: "SLOT_{row}_{col}"
```

4. **VisionPipeline (pipeline.py)**
```python
class VisionPipeline:
    """Orchestrates vision components"""
    
    Responsibilities:
    - Coordinate camera, detector, mapper
    - Handle start/stop control
    - FPS tracking
    - Annotation rendering
    
    Key Methods:
    - get_detections() → (frame, detections_by_slot)
    - start_stream() → Enable processing
    - stop_stream() → Pause processing
```

#### 4.1.3.3 Reasoning Engine Module

**Location:** `reasoning/`

**Core Innovation:** Temporal pattern analysis

**Components:**

1. **TemporalBuffer (temporal_buffer.py)**
```python
class TemporalBuffer:
    """Rolling window of detections per slot"""
    
    Data Structure:
    {
        'SLOT_0_0': deque([detection1, detection2, ...], maxlen=10),
        'SLOT_0_1': deque([...], maxlen=10),
        ...
    }
    
    Responsibilities:
    - Store recent detections (default: 10 frames)
    - Automatic old data eviction
    - Query detection history
    
    Key Methods:
    - add_detection(slot_id, detection)
    - get_history(slot_id) → List[Detection]
    - clear_slot(slot_id)
```

2. **ShelfState (shelf_state.py)**
```python
class ShelfState:
    """Current belief about shelf state"""
    
    State Model:
    {
        slot_id: str,
        expected_item: str,       # From configuration
        current_item: str | None, # Detected item
        confidence: float,
        state_status: str,        # STABLE/UNCERTAIN/TRANSITIONING
        consecutive_absences: int,
        consecutive_presences: int,
        last_confirmed: datetime
    }
    
    Key Methods:
    - is_occupied() → bool
    - is_misplaced() → bool
    - update_state(detection)
```

3. **ReasoningEngine (reasoning_engine.py)**
```python
class ReasoningEngine:
    """Temporal state reasoning logic"""
    
    Reasoning Rules (priority order):
    1. Short absence (≤2 frames) → IGNORE
    2. Sustained absence (≥5 frames) → ITEM_REMOVED
    3. Sustained mismatch (≥4 frames) → ITEM_MISPLACED
    4. Sustained presence (≥3 frames) → ITEM_ADDED
    5. Flickering detections → UNCERTAIN_STATE
    
    Process:
    For each slot:
        Get detection history from temporal buffer
        Analyze pattern (consecutive absences/presences)
        Apply reasoning rules
        Generate events if thresholds met
        Update shelf state
        
    Key Methods:
    - process_detections(detections_by_slot) → List[Event]
    - _analyze_slot(slot_id, history) → Optional[Event]
    - _aggregate_confidence(history) → float
```

4. **EventGenerator (event_generator.py)**
```python
class EventGenerator:
    """Creates structured event objects"""
    
    Event Types:
    - ITEM_ADDED
    - ITEM_REMOVED
    - ITEM_MISPLACED
    - UNCERTAIN_STATE
    - LOW_STOCK
    
    Event Structure:
    {
        event_id: int,
        event_type: str,
        slot_id: str,
        item_class: str,
        confidence: float,
        timestamp: datetime,
        metadata: dict
    }
```

#### 4.1.3.4 Inventory Management Module

**Location:** `inventory/`

**Components:**

1. **DecisionEngine (decision_engine.py)**
```python
class DecisionEngine:
    """Converts events to inventory actions"""
    
    Event → Action Mapping:
    ITEM_REMOVED     → decrement inventory
    ITEM_ADDED       → increment inventory
    ITEM_MISPLACED   → flag for review
    UNCERTAIN_STATE  → flag for verification
    LOW_STOCK        → generate alert
    
    Duplicate Prevention:
    - Track recent events per slot
    - 5-second cooldown period
    - Prevent event loops
    
    Key Methods:
    - process_events(events) → List[Action]
    - _is_duplicate(event) → bool
    - _validate_confidence(event) → bool
```

2. **InventoryManager (inventory_manager.py)**
```python
class InventoryManager:
    """Inventory CRUD operations"""
    
    Responsibilities:
    - Maintain in-memory inventory state
    - Execute increment/decrement actions
    - Prevent negative inventory
    - Low stock detection
    
    Key Methods:
    - increment(item_class, quantity=1)
    - decrement(item_class, quantity=1)
    - get_inventory() → Dict[item_class, quantity]
    - get_low_stock_items() → List[item_class]
    - set_threshold(item_class, threshold)
```

3. **AlertSystem (alert_system.py)**
```python
class AlertSystem:
    """Alert generation and management"""
    
    Alert Levels:
    - INFO: Informational
    - WARNING: Attention needed
    - CRITICAL: Urgent action required
    
    Alert Structure:
    {
        alert_id: str,
        level: str,
        title: str,
        message: str,
        item_class: str,
        slot_id: str,
        acknowledged: bool,
        timestamp: datetime
    }
    
    Key Methods:
    - create_alert(level, title, message)
    - acknowledge_alert(alert_id)
    - get_active_alerts() → List[Alert]
    - clear_acknowledged()
```

#### 4.1.3.5 Database Module

**Location:** `database/`

**Components:**

1. **Models (models.py)**
```python
# SQLAlchemy ORM Models

class Inventory(Base):
    __tablename__ = 'inventory'
    item_class: str (PK)
    quantity: int
    low_stock_threshold: int
    last_updated: datetime

class ShelfState(Base):
    __tablename__ = 'shelf_state'
    slot_id: str (PK)
    expected_item: str
    current_item: str
    confidence: float
    state_status: str
    consecutive_absences: int
    consecutive_presences: int
    last_confirmed: datetime

class EventLog(Base):
    __tablename__ = 'events_log'
    event_id: int (PK, auto)
    event_type: str
    slot_id: str
    item_class: str
    confidence: float
    timestamp: datetime
    event_metadata: str (JSON)

class InventoryAction(Base):
    __tablename__ = 'inventory_actions'
    action_id: int (PK, auto)
    action_type: str
    item_class: str
    slot_id: str
    quantity_change: int
    reason: str
    confidence: float
    timestamp: datetime

class Alert(Base):
    __tablename__ = 'alerts'
    alert_id: str (PK)
    level: str
    title: str
    message: str
    item_class: str
    slot_id: str
    acknowledged: bool
    timestamp: datetime
```

2. **DatabaseManager (db_manager.py)**
```python
class DatabaseManager:
    """Database CRUD operations"""
    
    Responsibilities:
    - Connection management
    - CRUD operations
    - Transaction handling
    - Query optimization
    
    Key Methods:
    - update_inventory(item_class, quantity)
    - log_event(event)
    - log_action(action)
    - get_events(filters) → List[Event]
    - get_inventory() → Dict
```

---

### 4.1.4 Web Scraping

**Note:** Inventory-Management-Tracking-System does not include web scraping functionality. It is a vision-based system that processes live camera feeds. If web scraping integration is required for external data sources (e.g., product catalogs, pricing), this would need to be implemented as an additional module.

**Potential Use Cases for Web Scraping (Future Enhancement):**
- Product information retrieval
- Price comparison
- Stock level verification from online sources
- Competitor inventory analysis

---

### 4.1.5 Database Layer

**Technology:** SQLite 3.x with SQLAlchemy ORM

**Database Architecture:**

```
┌─────────────────────────────────────────────────────┐
│                 SQLite Database                      │
├─────────────────────────────────────────────────────┤
│  Tables:                                            │
│  ├── inventory          (current stock levels)      │
│  ├── shelf_state        (slot state tracking)       │
│  ├── events_log         (event history)             │
│  ├── inventory_actions  (action audit trail)        │
│  └── alerts             (alert tracking)            │
├─────────────────────────────────────────────────────┤
│  Indexes:                                           │
│  ├── idx_events_timestamp                           │
│  ├── idx_events_type                                │
│  ├── idx_actions_timestamp                          │
│  └── idx_alerts_acknowledged                        │
└─────────────────────────────────────────────────────┘
```

**Database Design Principles:**
- Normalized schema (3NF)
- Indexed for query performance
- Transaction support for data integrity
- Audit trail for all changes
- Scalable to PostgreSQL if needed

**Connection Management:**
- SQLAlchemy connection pooling
- Automatic reconnection
- Transaction rollback on error
- Thread-safe operations

**Data Retention:**
- Events: Configurable (default: unlimited)
- Actions: Full history retained
- Alerts: Clearable after acknowledgment

---

## 5. UML Diagrams

### 5.2.1 Class Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Inventory-Management-Tracking-System Class Diagram                            │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│   VisionPipeline     │
├──────────────────────┤
│ - camera: Camera     │
│ - detector: Detector │
│ - mapper: SlotMapper │
│ - running: bool      │
├──────────────────────┤
│ + start_stream()     │
│ + stop_stream()      │
│ + get_detections()   │
└──────┬───────────────┘
       │ contains
       │
       ├────────────────┬────────────────┐
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│CameraStream │  │ObjectDetect │  │ SlotMapper  │
├─────────────┤  ├─────────────┤  ├─────────────┤
│-device_id   │  │-model: YOLO │  │-rows: int   │
│-buffer: dequ│  │-conf_thresh │  │-cols: int   │
│-thread      │  │-device      │  │-layout: dict│
├─────────────┤  ├─────────────┤  ├─────────────┤
│+start()     │  │+detect()    │  │+map_to_slot │
│+get_frame() │  │+set_conf()  │  │+draw_grid() │
│+stop()      │  │             │  │             │
└─────────────┘  └─────────────┘  └─────────────┘

┌──────────────────────┐
│  ReasoningEngine     │
├──────────────────────┤
│ - temporal_buffer    │
│ - shelf_state        │
│ - event_generator    │
│ - thresholds: dict   │
├──────────────────────┤
│ + process_detections │
│ + analyze_slot()     │
│ + generate_event()   │
└──────┬───────────────┘
       │ uses
       │
       ├────────────────┬────────────────┐
       │                │                │
       ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│TemporalBuff │  │ ShelfState  │  │EventGenerat │
├─────────────┤  ├─────────────┤  ├─────────────┤
│-buffers:dict│  │-states:dict │  │-event_types │
│-max_len: int│  │             │  │             │
├─────────────┤  ├─────────────┤  ├─────────────┤
│+add()       │  │+update()    │  │+create()    │
│+get_history │  │+is_occupied │  │             │
│+clear()     │  │+is_mispla..│  │             │
└─────────────┘  └─────────────┘  └─────────────┘

┌──────────────────────┐
│  DecisionEngine      │
├──────────────────────┤
│ - event_map: dict    │
│ - recent_events      │
│ - cooldown: int      │
├──────────────────────┤
│ + process_events()   │
│ + is_duplicate()     │
│ + validate_conf()    │
└──────┬───────────────┘
       │ creates actions for
       ▼
┌──────────────────────┐
│  InventoryManager    │
├──────────────────────┤
│ - inventory: dict    │
│ - thresholds: dict   │
├──────────────────────┤
│ + increment()        │
│ + decrement()        │
│ + get_inventory()    │
│ + get_low_stock()    │
└──────┬───────────────┘
       │ triggers
       ▼
┌──────────────────────┐
│    AlertSystem       │
├──────────────────────┤
│ - alerts: List       │
│ - max_alerts: int    │
├──────────────────────┤
│ + create_alert()     │
│ + acknowledge()      │
│ + get_active()       │
│ + clear_ack()        │
└──────────────────────┘

┌──────────────────────┐
│  DatabaseManager     │
├──────────────────────┤
│ - engine: Engine     │
│ - session: Session   │
├──────────────────────┤
│ + update_inventory() │
│ + log_event()        │
│ + log_action()       │
│ + get_events()       │
│ + get_alerts()       │
└──────────────────────┘

┌──────────────────────┐       ┌──────────────────────┐
│   Flask Application  │◄──────│   SocketIO           │
├──────────────────────┤       ├──────────────────────┤
│ - routes: dict       │       │ - events: dict       │
│ - app: Flask         │       │                      │
├──────────────────────┤       ├──────────────────────┤
│ + route()            │       │ + emit()             │
│ + handle_request()   │       │ + on()               │
└──────────────────────┘       └──────────────────────┘

Data Models (ORM):
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ Inventory   │  │ ShelfState  │  │ EventLog    │  │   Alert     │
├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤
│-item_class  │  │-slot_id     │  │-event_id    │  │-alert_id    │
│-quantity    │  │-expected    │  │-event_type  │  │-level       │
│-threshold   │  │-current     │  │-slot_id     │  │-title       │
│-updated_at  │  │-confidence  │  │-confidence  │  │-message     │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

---

### 5.2.2 Use Case Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     Inventory-Management-Tracking-System Use Case Diagram                       │
└────────────────────────────────────────────────────────────────┘

Actors:
┌────────┐
│ System │  (Automated processes)
│ Admin  │
└────────┘
    │
    │
┌───┴────┐
│  User  │  (End user/operator)
└───┬────┘
    │

┌──────────────────────────────────────────────────────────────┐
│                        Inventory-Management-Tracking-System System                            │
│                                                               │
│   ┌──────────────────────┐                                  │
│   │  Monitor Shelf       │◄──────────────────────┐          │
│   │  (Automated)         │                       │          │
│   └──────────────────────┘                       │          │
│                                                   │          │
│   ┌──────────────────────┐      ┌──────────────┐│          │
│   │  Detect Objects      │◄─────┤   System     ││          │
│   │                      │      │   Admin      ││          │
│   └──────────────────────┘      └──────────────┘│          │
│                                                  │          │
│   ┌──────────────────────┐                      │          │
│   │  Generate Events     │                      │          │
│   │                      │                      │          │
│   └──────────────────────┘                      │          │
│                                                  │          │
│   ┌──────────────────────┐      ┌──────────────┐          │
│   │  Update Inventory    │◄─────┤    User      │          │
│   │                      │      └──────────────┘          │
│   └──────────────────────┘             │                   │
│                                         │                   │
│   ┌──────────────────────┐             │                   │
│   │  View Dashboard      │◄────────────┤                   │
│   │                      │             │                   │
│   └──────────────────────┘             │                   │
│                                         │                   │
│   ┌──────────────────────┐             │                   │
│   │  Manage Inventory    │◄────────────┤                   │
│   │  - Add Items         │             │                   │
│   │  - Update Quantities │             │                   │
│   │  - Delete Items      │             │                   │
│   └──────────────────────┘             │                   │
│                                         │                   │
│   ┌──────────────────────┐             │                   │
│   │  View Events         │◄────────────┤                   │
│   │  - Filter Events     │             │                   │
│   │  - Export History    │             │                   │
│   └──────────────────────┘             │                   │
│                                         │                   │
│   ┌──────────────────────┐             │                   │
│   │  Manage Alerts       │◄────────────┤                   │
│   │  - View Alerts       │             │                   │
│   │  - Acknowledge       │             │                   │
│   │  - Clear History     │             │                   │
│   └──────────────────────┘             │                   │
│                                         │                   │
│   ┌──────────────────────┐             │                   │
│   │  Configure System    │◄────────────┘                   │
│   │  - Camera Settings   │                                 │
│   │  - Thresholds        │                                 │
│   │  - Shelf Layout      │                                 │
│   └──────────────────────┘                                 │
│                                                             │
│   ┌──────────────────────┐                                 │
│   │  Generate Reports    │◄────────────────────────────────┤
│   │                      │                                 │
│   └──────────────────────┘                                 │
└──────────────────────────────────────────────────────────────┘

Relationships:
- User "views" Dashboard
- User "manages" Inventory
- User "views" Events
- User "manages" Alerts
- System Admin "configures" System
- System Admin "monitors" Shelf (automated)
- System "detects" Objects (automated)
- System "generates" Events (automated)
- System "updates" Inventory (automated)
```

---

### 5.2.3 Sequence Diagram

#### Scenario: Item Removed from Shelf

```
┌────────────────────────────────────────────────────────────────────┐
│          Sequence Diagram: Item Removal Detection                  │
└────────────────────────────────────────────────────────────────────┘

Camera   Vision    Object    Slot     Reasoning  Decision Inventory  Database  WebSocket  Frontend
  │      Pipeline  Detector  Mapper   Engine     Engine   Manager      │         │         │
  │         │         │        │         │          │        │          │         │         │
  │ capture │         │        │         │          │        │          │         │         │
  ├────────►│         │        │         │          │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ detect  │        │         │          │        │          │         │         │
  │         ├────────►│        │         │          │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ detections      │         │          │        │          │         │         │
  │         │◄────────┤        │         │          │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ map_to_slots    │         │          │        │          │         │         │
  │         ├────────────────►│         │          │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ detections_by_slot        │          │        │          │         │         │
  │         │◄────────────────┤         │          │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ process_detections        │          │        │          │         │         │
  │         ├──────────────────────────►│          │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │         │        │  add_to_buffer    │        │          │         │         │
  │         │         │        │  ├──────┐         │        │          │         │         │
  │         │         │        │  │      │         │        │          │         │         │
  │         │         │        │  analyze_pattern  │        │          │         │         │
  │         │         │        │  ├──────┐         │        │          │         │         │
  │         │         │        │  │      │         │        │          │         │         │
  │         │         │        │  apply_rules      │        │          │         │         │
  │         │         │        │  ├──────┐         │        │          │         │         │
  │         │         │        │  │      │         │        │          │         │         │
  │         │         │        │  generate_event   │        │          │         │         │
  │         │         │        │  └──────┘         │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ events (ITEM_REMOVED)     │          │        │          │         │         │
  │         │◄──────────────────────────┤          │        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ process_events            │          │        │          │         │         │
  │         ├────────────────────────────────────►│        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │         │        │         │  validate_confidence         │         │         │
  │         │         │        │         │  ├──────┐        │          │         │         │
  │         │         │        │         │  │      │        │          │         │         │
  │         │         │        │         │  check_duplicate            │         │         │
  │         │         │        │         │  ├──────┐        │          │         │         │
  │         │         │        │         │  │      │        │          │         │         │
  │         │         │        │         │  create_action              │         │         │
  │         │         │        │         │  └──────┘        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ actions (decrement bottle)│          │        │          │         │         │
  │         │◄────────────────────────────────────┤        │          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ execute_action            │          │        │          │         │         │
  │         ├──────────────────────────────────────────────►│          │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │         │        │         │          │  decrement(bottle)         │         │
  │         │         │        │         │          │  ├─────┐         │         │         │
  │         │         │        │         │          │  │     │         │         │         │
  │         │         │        │         │          │  └─────┘         │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │         │        │         │          │  persist_changes │         │         │
  │         │         │        │         │          │  ├──────────────►│         │         │
  │         │         │        │         │          │  │      │        │         │         │
  │         │         │        │         │          │  │  log_event    │         │         │
  │         │         │        │         │          │  ├──────────────►│         │         │
  │         │         │        │         │          │  │      │        │         │         │
  │         │         │        │         │          │  │  log_action   │         │         │
  │         │         │        │         │          │  ├──────────────►│         │         │
  │         │         │        │         │          │  │      │        │         │         │
  │         │         │        │         │          │  check_thresholds          │         │
  │         │         │        │         │          │  ├─────┐         │         │         │
  │         │         │        │         │          │  │     │         │         │         │
  │         │         │        │         │          │  └─────┘         │         │         │
  │         │         │        │         │          │        │          │         │         │
  │         │ broadcast_updates         │          │        │          │         │         │
  │         ├───────────────────────────────────────────────────────────────────►│         │
  │         │         │        │         │          │        │          │         │         │
  │         │         │        │         │          │        │          │   emit('event')  │
  │         │         │        │         │          │        │          │         ├────────►│
  │         │         │        │         │          │        │          │         │         │
  │         │         │        │         │          │        │          │  emit('inventory')│
  │         │         │        │         │          │        │          │         ├────────►│
  │         │         │        │         │          │        │          │         │         │
  │         │         │        │         │          │        │          │         │  update_UI
  │         │         │        │         │          │        │          │         │  ├─────┐
  │         │         │        │         │          │        │          │         │  │     │
  │         │         │        │         │          │        │          │         │  └─────┘
  │         │         │        │         │          │        │          │         │         │

Time: ~0.5 seconds from detection to UI update
```

---

### 5.2.4 Activity Diagram

#### Main Processing Loop Activity Diagram

```
┌────────────────────────────────────────────────────────────┐
│              Main Processing Loop Activity                  │
└────────────────────────────────────────────────────────────┘

        ┌──────────────┐
        │    Start     │
        │    System    │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ Initialize   │
        │ All Modules  │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ Start Flask  │
        │   Server     │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ Start Camera │
        │   Thread     │
        └──────┬───────┘
               │
               ▼
    ╔══════════════════════╗
    ║   Background Loop    ║
    ║   (runs continuously)║
    ╚══════════════════════╝
               │
               ▼
        ┌──────────────┐
        │  Get Frame   │
        │ from Camera  │
        └──────┬───────┘
               │
               ▼
        ◆──────────────◆
       ╱  Frame Valid?  ╲──── No ───► [Log Error] ──┐
       ╲                ╱                            │
        ◆──────────────◆                            │
               │ Yes                                 │
               ▼                                     │
        ┌──────────────┐                            │
        │ Run YOLOv8   │                            │
        │  Detection   │                            │
        └──────┬───────┘                            │
               │                                     │
               ▼                                     │
        ┌──────────────┐                            │
        │  Map to Slots│                            │
        └──────┬───────┘                            │
               │                                     │
               ▼                                     │
        ┌──────────────┐                            │
        │ Add to Buffer│                            │
        │  (Per Slot)  │                            │
        └──────┬───────┘                            │
               │                                     │
               ▼                                     │
  ╔═══════════════════════════╗                    │
  ║ For Each Slot in Shelf    ║                    │
  ╚═══════════════════════════╝                    │
               │                                     │
               ▼                                     │
        ┌──────────────┐                            │
        │Get Detection │                            │
        │   History    │                            │
        └──────┬───────┘                            │
               │                                     │
               ▼                                     │
        ◆──────────────◆                            │
       ╱ Short Absence? ╲── Yes ──► [Ignore] ──┐   │
       ╲                ╱                       │   │
        ◆──────────────◆                       │   │
               │ No                             │   │
               ▼                                │   │
        ◆──────────────◆                       │   │
       ╱ Sustained      ╲                      │   │
       ╲ Absence (≥5)?  ╱── Yes ───┐          │   │
        ◆──────────────◆            │          │   │
               │ No                  │          │   │
               ▼                     │          │   │
        ◆──────────────◆            │          │   │
       ╱ Sustained      ╲           │          │   │
       ╲ Presence (≥3)? ╱── Yes ───┤          │   │
        ◆──────────────◆            │          │   │
               │ No                  │          │   │
               ▼                     │          │   │
        ◆──────────────◆            │          │   │
       ╱  Misplaced?    ╲── Yes ────┤          │   │
       ╲                ╱            │          │   │
        ◆──────────────◆            │          │   │
               │ No                  │          │   │
               ▼                     │          │   │
        [Continue]◄─────────────────┴──────────┴───┘
               │
               │
  ╔═══════════▼════════════╗
  ║ End Slot Loop          ║
  ╚════════════════════════╝
               │
               ▼
        ◆──────────────◆
       ╱ Events         ╲
       ╲ Generated?     ╱── No ────┐
        ◆──────────────◆            │
               │ Yes                 │
               ▼                     │
        ┌──────────────┐            │
        │Process Events│            │
        │ via Decision │            │
        │   Engine     │            │
        └──────┬───────┘            │
               │                     │
               ▼                     │
        ┌──────────────┐            │
        │ Generate     │            │
        │  Actions     │            │
        └──────┬───────┘            │
               │                     │
               ▼                     │
        ┌──────────────┐            │
        │  Execute     │            │
        │  Actions     │            │
        └──────┬───────┘            │
               │                     │
               ▼                     │
        ┌──────────────┐            │
        │ Update       │            │
        │ Inventory    │            │
        └──────┬───────┘            │
               │                     │
               ▼                     │
        ┌──────────────┐            │
        │ Log to       │            │
        │ Database     │            │
        └──────┬───────┘            │
               │                     │
               ▼                     │
        ┌──────────────┐            │
        │Check Alert   │            │
        │ Thresholds   │            │
        └──────┬───────┘            │
               │                     │
               ▼                     │
        ◆──────────────◆            │
       ╱ Generate       ╲           │
       ╲ Alerts?        ╱── Yes ────┤
        ◆──────────────◆            │
               │ No                  │
               ▼                     │
        ┌──────────────┐            │
        │ Broadcast via│            │
        │  WebSocket   │            │
        └──────┬───────┘            │
               │                     │
               ├◄────────────────────┘
               │
               ▼
        ◆──────────────◆
       ╱   System       ╲
       ╲   Running?     ╱── Yes ──► [Loop Back to Get Frame]
        ◆──────────────◆
               │ No
               ▼
        ┌──────────────┐
        │  Cleanup &   │
        │   Shutdown   │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │     End      │
        └──────────────┘
```

---

### 5.2.5 Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     Component Diagram                           │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Tier                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│  │  Dashboard    │  │  Inventory    │  │   Events      │      │
│  │  Component    │  │  Component    │  │  Component    │      │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘      │
│          │                   │                   │              │
│          └───────────────────┼───────────────────┘              │
│                              │                                  │
│  ┌───────────────────────────▼──────────────────────────┐      │
│  │         WebSocket Client Component                    │      │
│  │  (socketio.js - Real-time event handling)            │      │
│  └───────────────────────────┬──────────────────────────┘      │
└────────────────────────────┬─┴──────────────────────────────────┘
                             │
                    HTTP REST │ WebSocket
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                       API Gateway Layer                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐          │
│  │         Flask Application (app.py)                │          │
│  │  - CORS Handler                                   │          │
│  │  - Request Router                                 │          │
│  │  - Error Handler                                  │          │
│  └──────────────┬────────────────────┬───────────────┘          │
│                 │                    │                           │
│  ┌──────────────▼─────────┐  ┌──────▼─────────────────┐        │
│  │   REST Routes          │  │  WebSocket Handlers    │        │
│  │   (routes.py)          │  │  (websocket.py)        │        │
│  │  - /api/inventory      │  │  - event               │        │
│  │  - /api/events         │  │  - inventory_update    │        │
│  │  - /api/alerts         │  │  - alert               │        │
│  │  - /api/shelf-state    │  │  - stream_control      │        │
│  │  - /api/video-stream   │  │                        │        │
│  └────────────────────────┘  └────────────────────────┘        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    Business Logic
                             │
┌────────────────────────────┴────────────────────────────────────┐
│                    Business Logic Tier                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Vision Processing Component                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │CameraStream  │  │ObjectDetector│  │ SlotMapper   │  │   │
│  │  │              │  │  (YOLOv8)    │  │              │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  │         │                  │                  │          │   │
│  │         └──────────────────┼──────────────────┘          │   │
│  │                            │                             │   │
│  │         ┌──────────────────▼────────────────┐            │   │
│  │         │   VisionPipeline                  │            │   │
│  │         │   (Orchestrator)                  │            │   │
│  │         └──────────────────┬────────────────┘            │   │
│  └────────────────────────────┼─────────────────────────────┘   │
│                                │                                 │
│                                ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      Temporal Reasoning Component                        │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │TemporalBuff  │  │ ShelfState   │  │EventGeneratr │  │   │
│  │  │              │  │              │  │              │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  │         │                  │                  │          │   │
│  │         └──────────────────┼──────────────────┘          │   │
│  │                            │                             │   │
│  │         ┌──────────────────▼────────────────┐            │   │
│  │         │   ReasoningEngine                 │            │   │
│  │         │   (Temporal Analysis)             │            │   │
│  │         └──────────────────┬────────────────┘            │   │
│  └────────────────────────────┼─────────────────────────────┘   │
│                                │                                 │
│                                ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      Inventory Management Component                      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │DecisionEngin │  │InventoryMgr  │  │ AlertSystem  │  │   │
│  │  │              │  │              │  │              │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │   │
│  │         │                  │                  │          │   │
│  │         └──────────────────┴──────────────────┘          │   │
│  └────────────────────────────┬─────────────────────────────┘   │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                        Database Operations
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                      Data Access Tier                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Database Manager Component                     │   │
│  │           (db_manager.py)                                │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │         SQLAlchemy ORM Layer                     │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  └───────────────────────────┬─────────────────────────────┘   │
└────────────────────────────────┼────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Persistence Tier                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                SQLite Database                           │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │inventory │ │shelf_stat│ │events_log│ │ alerts   │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  │  ┌──────────┐                                           │   │
│  │  │inventory_│                                           │   │
│  │  │actions   │                                           │   │
│  │  └──────────┘                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Configuration Component                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ config.yaml  │  │ shelf_layout │                            │
│  │              │  │   .json      │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                  │
│  ┌────────────────────────────────────────────┐                │
│  │   ConfigLoader (config_loader.py)          │                │
│  └────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Utility Components                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Logger      │  │  Helpers     │  │   Models     │         │
│  │              │  │              │  │   (YOLOv8)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘

Component Dependencies:
━━━━━━━━━━━━━━━━━━━━
→ : Uses/Depends on
↔ : Bidirectional communication
⇒ : Data flow
```

---

### 5.2.6 Deployment Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                     Deployment Diagram                          │
└────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Physical Server/Computer                      │
│                    (Windows/Linux/macOS)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Hardware Layer                             │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  CPU: 2+ cores                                          │    │
│  │  RAM: 8GB+                                              │    │
│  │  Storage: 10GB+ SSD                                     │    │
│  │  GPU: NVIDIA (optional, CUDA support)                   │    │
│  │  Camera: USB Webcam                                     │    │
│  │  Network: Ethernet/WiFi                                 │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                      │
│  ┌────────────────────────┴───────────────────────────────┐    │
│  │         Operating System (OS Layer)                     │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Windows 10/11  OR  Ubuntu 20.04+  OR  macOS 10.15+    │    │
│  │  - Camera Drivers                                       │    │
│  │  - CUDA Toolkit (if GPU)                                │    │
│  │  - Network Stack                                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                      │
│  ┌────────────────────────┴───────────────────────────────┐    │
│  │         Runtime Environment                             │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │  Python 3.8+ Runtime                                    │    │
│  │  - Virtual Environment (venv)                           │    │
│  │  - Python Libraries (pip packages)                      │    │
│  └────────────────────────────────────────────────────────┘    │
│                           │                                      │
│  ┌────────────────────────┴───────────────────────────────┐    │
│  │         Application Layer                               │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │  Inventory-Management-Tracking-System Application (main.py)                     │   │    │
│  │  │  Process ID: <PID>                              │   │    │
│  │  │  Port: 5000                                     │   │    │
│  │  │                                                 │   │    │
│  │  │  ┌────────────────────────────────────────┐    │   │    │
│  │  │  │  Flask/SocketIO Server                 │    │   │    │
│  │  │  │  - HTTP Server (127.0.0.1:5000)        │    │   │    │
│  │  │  │  - WebSocket Server                    │    │   │    │
│  │  │  └────────────────────────────────────────┘    │   │    │
│  │  │                                                 │   │    │
│  │  │  ┌────────────────────────────────────────┐    │   │    │
│  │  │  │  Background Processing Thread          │    │   │    │
│  │  │  │  - Vision Pipeline                     │    │   │    │
│  │  │  │  - Reasoning Engine                    │    │   │    │
│  │  │  │  - Inventory Manager                   │    │   │    │
│  │  │  └────────────────────────────────────────┘    │   │    │
│  │  │                                                 │   │    │
│  │  │  ┌────────────────────────────────────────┐    │   │    │
│  │  │  │  Camera Capture Thread                 │    │   │    │
│  │  │  │  - Continuous frame capture            │    │   │    │
│  │  │  └────────────────────────────────────────┘    │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐   │    │
│  │  │  File System                                    │   │    │
│  │  │  ┌──────────────────────────────────────────┐  │   │    │
│  │  │  │  data/shelf.db (SQLite Database)         │  │   │    │
│  │  │  │  Size: ~100MB-2GB                        │  │   │    │
│  │  │  └──────────────────────────────────────────┘  │   │    │
│  │  │  ┌──────────────────────────────────────────┐  │   │    │
│  │  │  │  yolov8n.pt (Model File)                 │  │   │    │
│  │  │  │  Size: ~6MB                              │  │   │    │
│  │  │  └──────────────────────────────────────────┘  │   │    │
│  │  │  ┌──────────────────────────────────────────┐  │   │    │
│  │  │  │  config.yaml (Configuration)             │  │   │    │
│  │  │  └──────────────────────────────────────────┘  │   │    │
│  │  └─────────────────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ Network (LAN/WiFi)
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                    Client Devices                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐   ┌──────────────────┐   ┌────────────┐  │
│  │  Desktop PC      │   │  Laptop          │   │  Tablet    │  │
│  ├──────────────────┤   ├──────────────────┤   ├────────────┤  │
│  │  Web Browser     │   │  Web Browser     │   │Web Browser │  │
│  │  - Chrome/Edge   │   │  - Chrome/Edge   │   │  Safari    │  │
│  │                  │   │                  │   │            │  │
│  │  URL:            │   │  URL:            │   │  URL:      │  │
│  │  127.0.0.1:5000  │   │  192.168.1.x:5000│   │  <IP>:5000 │  │
│  │                  │   │                  │   │            │  │
│  │  ┌────────────┐  │   │  ┌────────────┐  │   │ ┌────────┐ │  │
│  │  │ Dashboard  │  │   │  │ Dashboard  │  │   │ │Dashboard│ │
│  │  │ (HTML/JS)  │  │   │  │ (HTML/JS)  │  │   │ │(HTML/JS)│ │
│  │  └────────────┘  │   │  └────────────┘  │   │ └────────┘ │  │
│  │  ┌────────────┐  │   │  ┌────────────┐  │   │            │  │
│  │  │ WebSocket  │  │   │  │ WebSocket  │  │   │            │  │
│  │  │ Connection │  │   │  │ Connection │  │   │            │  │
│  │  └────────────┘  │   │  └────────────┘  │   │            │  │
│  └──────────────────┘   └──────────────────┘   └────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Network Protocols:
━━━━━━━━━━━━━━━━━
- HTTP/HTTPS (Port 5000) - REST API
- WebSocket (Port 5000) - Real-time updates
- MJPEG Stream - Video feed

Security Notes:
━━━━━━━━━━━━━━
- Default: Local only (127.0.0.1)
- Production: Configure firewall rules
- LAN Access: Change host to 0.0.0.0
- Authentication: Not implemented (dev mode)

Deployment Variations:
━━━━━━━━━━━━━━━━━━━
1. Local Development: Single machine, 127.0.0.1
2. LAN Deployment: Server on network, clients access via IP
3. Production: Behind reverse proxy (nginx), HTTPS enabled
```

---

## 6. Database Design

### 6.1 Entity-Relationship Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                  Database ER Diagram                              │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────┐
│    INVENTORY        │
├─────────────────────┤
│ PK item_class: TEXT │
│    quantity: INT    │
│    low_stock_thresh │
│    last_updated: DT │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐          ┌─────────────────────┐
│   EVENTS_LOG        │          │   SHELF_STATE       │
├─────────────────────┤          ├─────────────────────┤
│ PK event_id: INT    │◄────┐    │ PK slot_id: TEXT    │
│    event_type: TEXT │     │    │    expected_item    │
│    slot_id: TEXT ───┼─────┼───►│    current_item     │
│    item_class: TEXT ┼─────┘    │    confidence       │
│    confidence: FLOAT│          │    state_status     │
│    timestamp: DT    │          │    consecutive_abs  │
│    event_metadata   │          │    consecutive_pres │
└─────────────────────┘          │    last_confirmed   │
                                 └─────────────────────┘
                                           │
                                           │ 1:N
                                           │
                                           ▼
┌─────────────────────┐          ┌─────────────────────┐
│ INVENTORY_ACTIONS   │          │      ALERTS         │
├─────────────────────┤          ├─────────────────────┤
│ PK action_id: INT   │          │ PK alert_id: TEXT   │
│    action_type: TEXT│          │    level: TEXT      │
│    item_class: TEXT ┼─────┐    │    title: TEXT      │
│    slot_id: TEXT    │     │    │    message: TEXT    │
│    quantity_change  │     └───►│    item_class: TEXT │
│    reason: TEXT     │          │    slot_id: TEXT    │
│    confidence: FLOAT│          │    acknowledged:BOOL│
│    timestamp: DT    │          │    timestamp: DT    │
└─────────────────────┘          └─────────────────────┘

Relationships:
- INVENTORY 1:N EVENTS_LOG (one item, many events)
- SHELF_STATE 1:N EVENTS_LOG (one slot, many events)
- INVENTORY 1:N INVENTORY_ACTIONS (one item, many actions)
- SHELF_STATE 1:N ALERTS (one slot, many alerts)
- INVENTORY 1:N ALERTS (one item, many alerts)
```

### 6.2 Table Specifications

**Table: inventory**
```sql
CREATE TABLE inventory (
    item_class TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER NOT NULL DEFAULT 2,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT positive_quantity CHECK (quantity >= 0),
    CONSTRAINT positive_threshold CHECK (low_stock_threshold >= 0)
);

CREATE INDEX idx_inventory_low_stock 
ON inventory(quantity) WHERE quantity <= low_stock_threshold;
```

**Table: shelf_state**
```sql
CREATE TABLE shelf_state (
    slot_id TEXT PRIMARY KEY,
    expected_item TEXT,
    current_item TEXT,
    confidence FLOAT DEFAULT 0.0,
    state_status TEXT DEFAULT 'UNKNOWN',
    consecutive_absences INTEGER DEFAULT 0,
    consecutive_presences INTEGER DEFAULT 0,
    last_confirmed DATETIME,
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT valid_status CHECK (state_status IN ('STABLE', 'UNCERTAIN', 'TRANSITIONING', 'UNKNOWN'))
);

CREATE INDEX idx_shelf_state_status ON shelf_state(state_status);
```

**Table: events_log**
```sql
CREATE TABLE events_log (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    slot_id TEXT NOT NULL,
    item_class TEXT,
    confidence FLOAT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_metadata TEXT,
    FOREIGN KEY (slot_id) REFERENCES shelf_state(slot_id),
    FOREIGN KEY (item_class) REFERENCES inventory(item_class),
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'item_added', 'item_removed', 'item_misplaced', 
        'uncertain_state', 'low_stock'
    ))
);

CREATE INDEX idx_events_timestamp ON events_log(timestamp DESC);
CREATE INDEX idx_events_type ON events_log(event_type);
CREATE INDEX idx_events_slot ON events_log(slot_id);
CREATE INDEX idx_events_item ON events_log(item_class);
```

**Table: inventory_actions**
```sql
CREATE TABLE inventory_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,
    item_class TEXT NOT NULL,
    slot_id TEXT,
    quantity_change INTEGER DEFAULT 0,
    reason TEXT,
    confidence FLOAT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_class) REFERENCES inventory(item_class),
    CONSTRAINT valid_action_type CHECK (action_type IN (
        'increment', 'decrement', 'set', 'adjust'
    ))
);

CREATE INDEX idx_actions_timestamp ON inventory_actions(timestamp DESC);
CREATE INDEX idx_actions_item ON inventory_actions(item_class);
```

**Table: alerts**
```sql
CREATE TABLE alerts (
    alert_id TEXT PRIMARY KEY,
    level TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    item_class TEXT,
    slot_id TEXT,
    acknowledged BOOLEAN DEFAULT 0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_class) REFERENCES inventory(item_class),
    FOREIGN KEY (slot_id) REFERENCES shelf_state(slot_id),
    CONSTRAINT valid_level CHECK (level IN ('INFO', 'WARNING', 'CRITICAL'))
);

CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_level ON alerts(level);
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
```

---

## 7. API Specifications

### 7.1 REST API Summary

**Base URL:** `http://127.0.0.1:5000/api`

**Content-Type:** `application/json`

**Authentication:** None (development mode)

### 7.2 Key Endpoints

| Method | Endpoint | Purpose | Request Body | Response |
|--------|----------|---------|--------------|----------|
| GET | `/health` | System health | None | Health status |
| GET | `/inventory` | Get all inventory | None | Inventory dict |
| POST | `/inventory/<item>` | Create/update item | {quantity, threshold} | Item details |
| PUT | `/inventory/<item>` | Adjust quantity | {adjustment, reason} | Updated item |
| DELETE | `/inventory/<item>` | Delete item | None | Success message |
| GET | `/events` | Get event history | Query params | Events array |
| GET | `/shelf-state` | Get shelf state | None | Slots dict |
| GET | `/alerts` | Get alerts | Query params | Alerts array |
| PUT | `/alerts/<id>` | Acknowledge alert | {acknowledged} | Alert details |
| GET | `/video-stream` | MJPEG stream | None | Video stream |

### 7.3 WebSocket Events

**Server → Client:**
- `event` - State transition events
- `inventory_update` - Inventory changes
- `alert` - New alerts
- `shelf_state_update` - Slot state changes

**Client → Server:**
- `stream_control` - Start/stop video processing

---

## 8. Conclusion

This document provides a comprehensive technical architecture overview of Inventory-Management-Tracking-System. The system demonstrates a well-architected approach to inventory tracking using:

- Layered architecture for separation of concerns
- Temporal reasoning for intelligent event detection
- Real-time updates via WebSocket
- Robust database design with full audit trails
- Scalable component-based design

For implementation details, refer to the source code and additional documentation files in the `docs/` directory.

---

**Document End**

_For questions or clarifications, please refer to:_
- [Architecture Documentation](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Development Guide](DEVELOPMENT.md)
