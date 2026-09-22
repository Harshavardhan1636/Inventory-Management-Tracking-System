# Architecture Documentation

Comprehensive technical architecture documentation for Inventory-Management-Tracking-System.

## Table of Contents
- [System Overview](#system-overview)
- [Architecture Layers](#architecture-layers)
- [Data Flow](#data-flow)
- [Core Components](#core-components)
- [Database Schema](#database-schema)
- [Design Patterns](#design-patterns)
- [Performance Characteristics](#performance-characteristics)

---

## System Overview

Inventory-Management-Tracking-System follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WEB FRONTEND (Dashboard)                         │
│                  (HTML/CSS/JS + WebSocket Connection)                    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ HTTP + WebSocket
                    ┌────────▼──────────┐
                    │  Flask API Server │
                    │  + SocketIO       │
                    └────────┬──────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐
   │  Database   │   │ REST Routes  │   │  WebSocket      │
   │  Manager    │   │  + Events    │   │  Handlers       │
   └─────────────┘   └──────────────┘   └─────────────────┘
        │
        └────────────────────┬────────────────────────┐
                             │                        │
                    ┌────────▼──────────┐    ┌───────▼──────────┐
                    │  Main Processing  │    │  Main.py Entry   │
                    │  Loop (Thread)    │    │  Point            │
                    └────────┬──────────┘    └──────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐
   │   Vision    │   │  Reasoning   │   │   Inventory      │
   │  Pipeline   │   │   Engine     │   │   & Decision     │
   └─────────────┘   └──────────────┘   └──────────────────┘
        │
        └────────┬────────────┐
                 │            │
        ┌────────▼─┐  ┌──────▼────────┐
        │  Camera  │  │  Detector     │
        │  Stream  │  │  (YOLOv8)     │
        └──────────┘  └──────┬────────┘
                             │
                      ┌──────▼─────────┐
                      │  Slot Mapper   │
                      │  (Frame Grid)  │
                      └────────────────┘
```

---

## Architecture Layers

### Layer 1: Vision Layer
**Purpose**: Capture video and detect objects

**Components**:
- `CameraStream` - Threaded webcam capture with frame buffering
- `ObjectDetector` - YOLOv8 wrapper with confidence filtering
- `SlotMapper` - Maps detections to shelf grid slots
- `VisionPipeline` - Orchestrates all vision components

**Key Features**:
- Multi-device camera probing (tries 0→1→2→3)
- Thread-safe frame buffering
- Demo fallback when no camera signal
- FPS tracking and overlay rendering

### Layer 2: Reasoning Layer
**Purpose**: Convert raw detections into intelligent events

**Components**:
- `TemporalBuffer` - Rolling window of recent detections
- `ShelfState` - Maintains belief about current state
- `ReasoningEngine` - Applies temporal logic rules
- `EventGenerator` - Creates structured events

**Key Innovation**:
This is the **differentiating factor** of Inventory-Management-Tracking-System. Instead of naive frame-by-frame processing:

1. **Buffering**: Stores last 10 frames of detections per slot
2. **Analysis**: Applies 5 reasoning rules with priority order
3. **Event Generation**: Only triggers on sustained changes

**Reasoning Rules** (priority order):
```python
1. Short absence (1-2 frames)     → IGNORE (likely occlusion)
2. Sustained absence (5+ frames)  → ITEM_REMOVED event
3. Sustained mismatch (4+ frames) → ITEM_MISPLACED event
4. Sustained presence (3+ frames) → ITEM_ADDED event
5. Flickering detections          → UNCERTAIN_STATE event
```

### Layer 3: Decision Layer
**Purpose**: Convert events into inventory actions

**Components**:
- `DecisionEngine` - Event → Action conversion
- `InventoryManager` - Stock level CRUD operations
- `AlertSystem` - Alert generation and tracking

**Flow**:
```
Event (ITEM_REMOVED) → Validate confidence
                    → Check duplicate (5s cooldown)
                    → Generate action (decrement)
                    → Execute action
                    → Check thresholds
                    → Generate alert if needed
```

### Layer 4: Persistence Layer
**Purpose**: Store and retrieve data

**Components**:
- `DatabaseManager` - CRUD operations
- `SQLAlchemy Models` - ORM definitions
- SQLite database

**Tables**:
- `inventory` - Current stock levels
- `shelf_state` - Per-slot state tracking
- `events_log` - Event history
- `inventory_actions` - Action audit trail
- `alerts` - Alert tracking

### Layer 5: API Layer
**Purpose**: Expose system via web interfaces

**Components**:
- `Flask App` - HTTP server
- `REST Routes` - RESTful endpoints
- `WebSocket Handlers` - Real-time push

**Protocols**:
- HTTP REST for queries/commands
- WebSocket for real-time updates
- MJPEG stream for video

### Layer 6: Presentation Layer
**Purpose**: User interface

**Components**:
- HTML templates (Jinja2)
- CSS stylesheets
- JavaScript (vanilla, no frameworks)
- WebSocket client

---

## Data Flow

### Complete Processing Cycle

```
[Camera] 30 FPS
    ↓
[CameraStream.get_frame()]
    ↓ frame: np.ndarray (1280x720x3)
    ↓
[ObjectDetector.detect()]
    ↓ detections: [{class, confidence, bbox, centroid}, ...]
    ↓
[SlotMapper.map_to_slots()]
    ↓ detections with slot_id: [{..., slot_id: "SLOT_0_1"}, ...]
    ↓
[Main Loop] (background thread)
    ↓
[TemporalBuffer.add_detection()] for each slot
    ↓ stores in deque with max length 10
    ↓
[ReasoningEngine.process_detections()]
    ↓ for each slot:
    │   1. Get detection history from buffer
    │   2. Analyze temporal pattern
    │   3. Apply reasoning rules
    │   4. Update ShelfState
    │   5. Generate events if threshold met
    ↓
events: [Event(type=ITEM_REMOVED, slot="SLOT_0_1", item="bottle", conf=0.89)]
    ↓
[DecisionEngine.process_events()]
    ↓ for each event:
    │   1. Validate confidence >= 0.7
    │   2. Check duplicate prevention (5s cooldown)
    │   3. Convert event → action
    ↓
actions: [Action(type=decrement, item="bottle", qty=-1)]
    ↓
[Execute Actions]
    ↓
    ├─ [InventoryManager.decrement("bottle")]
    │   └─ bottle: 10 → 9 (in-memory)
    │
    ├─ [DatabaseManager.update_inventory()]
    │   └─ UPDATE inventory SET quantity = 9
    │
    ├─ [DatabaseManager.log_event()]
    │   └─ INSERT INTO events_log (...)
    │
    ├─ [DatabaseManager.log_action()]
    │   └─ INSERT INTO inventory_actions (...)
    │
    ├─ [Check thresholds]
    │   └─ if quantity <= 2: generate LOW_STOCK alert
    │
    └─ [WebSocket.emit()]
        ├─ emit('event', event_dict)
        ├─ emit('inventory_update', inventory_dict)
        └─ emit('alert', alert_dict)
            ↓
[Frontend] receives WebSocket message
    ├─ Update inventory display
    ├─ Add event to timeline
    ├─ Show alert notification
    └─ Update statistics
```

---

## Core Components

### 1. Vision Pipeline (`vision/pipeline.py`)

**Responsibilities**:
- Orchestrate camera, detector, and slot mapper
- Handle frame acquisition and processing
- Manage demo mode fallback
- Render debug overlays

**Key Methods**:
```python
def get_detections():
    """Get current frame with detections"""
    1. Get frame from camera
    2. Run YOLOv8 inference
    3. Map detections to slots
    4. Return annotated frame + detections

def start_stream():
    """Start video processing"""

def stop_stream():
    """Stop video processing"""
```

**Thread Safety**:
- Uses `threading.Lock` for frame access
- Background thread for camera reading
- Queue-based frame buffering

### 2. Reasoning Engine (`reasoning/reasoning_engine.py`)

**Core Logic**:
```python
def process_detections(slot_detections):
    events = []
    
    for slot_id, detection in slot_detections.items():
        # Get temporal history
        history = temporal_buffer.get_history(slot_id)
        current_state = shelf_state.get(slot_id)
        
        # Count consecutive absences/presences
        consecutive_absences = count_consecutive_none(history)
        consecutive_presences = count_consecutive_present(history)
        
        # Apply reasoning rules (priority order)
        
        # Rule 1: Short absence → IGNORE
        if 0 < consecutive_absences <= SHORT_ABSENCE_THRESHOLD:
            continue  # Likely occlusion
        
        # Rule 2: Sustained absence → ITEM_REMOVED
        if consecutive_absences >= REMOVAL_THRESHOLD:
            if current_state.is_occupied():
                confidence = aggregate_confidence(history)
                if confidence >= CONFIDENCE_THRESHOLD:
                    event = Event(ITEM_REMOVED, slot_id, ...)
                    events.append(event)
                    shelf_state.mark_empty(slot_id)
        
        # Rule 3: Sustained mismatch → ITEM_MISPLACED
        elif consecutive_presences >= MISMATCH_THRESHOLD:
            if detection.class != current_state.expected_item:
                event = Event(ITEM_MISPLACED, slot_id, ...)
                events.append(event)
        
        # Rule 4: Sustained presence → ITEM_ADDED
        elif consecutive_presences >= ADDITION_THRESHOLD:
            if not current_state.is_occupied():
                event = Event(ITEM_ADDED, slot_id, ...)
                events.append(event)
                shelf_state.mark_occupied(slot_id)
        
        # Rule 5: Flickering → UNCERTAIN_STATE
        elif is_flickering(history):
            event = Event(UNCERTAIN_STATE, slot_id, ...)
            events.append(event)
    
    return events
```

**Thresholds** (configurable):
- `SHORT_ABSENCE_THRESHOLD`: 2 frames
- `REMOVAL_THRESHOLD`: 5 frames
- `ADDITION_THRESHOLD`: 3 frames
- `MISMATCH_THRESHOLD`: 4 frames
- `CONFIDENCE_THRESHOLD`: 0.7

### 3. Decision Engine (`inventory/decision_engine.py`)

**Event-to-Action Mapping**:
```python
EVENT_ACTION_MAP = {
    "item_removed": "decrement",
    "item_added": "increment",
    "item_misplaced": "flag_review",
    "uncertain_state": "flag_verification",
    "low_stock": "alert"
}
```

**Duplicate Prevention**:
```python
# Track recent events per slot
recent_events = {}  # {slot_id: {event_type: timestamp}}

# 5-second cooldown
COOLDOWN_SECONDS = 5

def is_duplicate(event):
    key = (event.slot_id, event.type)
    if key in recent_events:
        time_since = now - recent_events[key]
        return time_since < COOLDOWN_SECONDS
    return False
```

### 4. Database Manager (`database/db_manager.py`)

**Transactions**:
```python
def update_inventory_transactional(item, quantity_change):
    with session.begin():
        # Atomic operation
        item_obj = session.query(Inventory).filter_by(
            item_class=item
        ).first()
        
        if item_obj:
            new_qty = item_obj.quantity + quantity_change
            if new_qty < 0:
                raise ValueError("Negative inventory")
            item_obj.quantity = new_qty
            item_obj.last_updated = datetime.now()
        else:
            # Create new item
            item_obj = Inventory(
                item_class=item,
                quantity=max(0, quantity_change)
            )
            session.add(item_obj)
```

---

## Database Schema

### Tables and Relationships

```sql
-- Inventory tracking
CREATE TABLE inventory (
  item_class TEXT PRIMARY KEY,
  quantity INTEGER NOT NULL DEFAULT 0,
  low_stock_threshold INTEGER NOT NULL DEFAULT 2,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Shelf slot states
CREATE TABLE shelf_state (
  slot_id TEXT PRIMARY KEY,
  expected_item TEXT,
  current_item TEXT,
  confidence FLOAT DEFAULT 0.0,
  state_status TEXT DEFAULT 'UNKNOWN',
  consecutive_absences INTEGER DEFAULT 0,
  consecutive_presences INTEGER DEFAULT 0,
  last_confirmed DATETIME
);

-- Event history
CREATE TABLE events_log (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  slot_id TEXT NOT NULL,
  item_class TEXT,
  confidence FLOAT NOT NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  event_metadata TEXT  -- JSON
);

-- Inventory action history
CREATE TABLE inventory_actions (
  action_id INTEGER PRIMARY KEY AUTOINCREMENT,
  action_type TEXT NOT NULL,
  item_class TEXT NOT NULL,
  slot_id TEXT,
  quantity_change INTEGER DEFAULT 0,
  reason TEXT,
  confidence FLOAT,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Alerts
CREATE TABLE alerts (
  alert_id TEXT PRIMARY KEY,
  level TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  item_class TEXT,
  slot_id TEXT,
  acknowledged BOOLEAN DEFAULT 0,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes (for performance)

```sql
CREATE INDEX idx_events_timestamp ON events_log(timestamp DESC);
CREATE INDEX idx_events_type ON events_log(event_type);
CREATE INDEX idx_actions_timestamp ON inventory_actions(timestamp DESC);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
```

---

## Design Patterns

### 1. Factory Pattern
**Location**: `main.py` initialization

```python
def create_vision_pipeline(config):
    camera = CameraStream(config['camera'])
    detector = ObjectDetector(config['detection'])
    mapper = SlotMapper(config['shelf'])
    return VisionPipeline(camera, detector, mapper)
```

### 2. Observer Pattern
**Location**: WebSocket event broadcasting

```python
# Publisher
def emit_event(event):
    socketio.emit('event', event.to_dict(), broadcast=True)

# Subscribers (JavaScript clients)
socket.on('event', function(data) {
    updateEventTimeline(data);
});
```

### 3. Strategy Pattern
**Location**: Configurable reasoning thresholds

```python
class ReasoningEngine:
    def __init__(self, config):
        self.short_absence_threshold = config['short_absence_threshold']
        self.removal_threshold = config['removal_threshold']
        # Can change strategy without code changes
```

### 4. Dependency Injection
**Location**: Throughout component initialization

```python
# Dependencies injected through constructors
reasoning_engine = ReasoningEngine(
    temporal_buffer=buffer,
    shelf_state=state,
    config=config
)
```

---

## Performance Characteristics

### Latency Breakdown

```
Camera capture:        33ms  (30 FPS = 33ms/frame)
YOLOv8 inference:      20ms  (CPU), 5ms (GPU)
Slot mapping:          <1ms
Temporal buffering:    <1ms
Reasoning analysis:    <5ms
Decision processing:   <1ms
Database write:        1-5ms
WebSocket emit:        <1ms
────────────────────────────
Total per frame:       ~60ms (CPU), ~45ms (GPU)
```

### Throughput

- **Video Processing**: 15-30 FPS (depending on hardware)
- **Event Processing**: 100+ events/second
- **Database Writes**: 200+ transactions/second
- **WebSocket Messages**: 1000+ messages/second

### Memory Usage

- **Base**: ~300MB (Python + Flask)
- **YOLOv8 Model**: ~20MB (nano variant)
- **Frame Buffers**: ~50MB (720p x 2 buffers)
- **Temporal Buffers**: ~10MB (10 frames x 6 slots)
- **Total**: ~400-500MB typical

### Scalability Limits

- **Single camera per instance** (architectural constraint)
- **SQLite write limit**: ~1MB/sec
- **WebSocket connections**: 100-500 concurrent (Python threading)
- **Database size**: 6 months @ 1000 items ≈ 2GB

---

## Thread Model

```
Main Thread
  └─ Flask/SocketIO Server
      ├─ HTTP Request Handlers
      └─ WebSocket Handlers

Background Thread #1
  └─ Main Processing Loop
      ├─ Get detections (blocks on vision)
      ├─ Reasoning engine
      ├─ Decision engine
      └─ Database writes

Background Thread #2
  └─ Camera Capture Thread
      └─ Continuous frame reading

Background Thread #3
  └─ SocketIO Background Tasks
      └─ Heartbeat, cleanup
```

**Synchronization**:
- `vision_lock` - Protects camera access
- `db_session_lock` - Protects database writes (SQLAlchemy handles most)
- `event_queue` - Thread-safe queue for events

---

## Configuration System

### Hierarchy

```
1. config.yaml (default)
2. config.demo.yaml (demo mode)
3. Command-line arguments (override)
4. Environment variables (not implemented)
```

### Structure

```yaml
system:          # System metadata
camera:          # Camera settings
detection:       # YOLOv8 settings
shelf:           # Shelf layout
reasoning:       # Temporal reasoning
inventory:       # Inventory management
database:        # Database connection
api:             # Web server settings
```

See [CONFIGURATION.md](CONFIGURATION.md) for full details.

---

## Extension Points

### Adding New Event Types

1. Define in `reasoning/event_generator.py`
2. Add reasoning rule in `ReasoningEngine`
3. Map to action in `DecisionEngine`
4. Handle in WebSocket client

### Adding New Detection Classes

1. YOLOv8 supports 80 COCO classes by default
2. For custom classes: Train custom YOLOv8 model
3. Update `expected_items` in shelf layout JSON

### Adding New Shelf Layouts

1. Create JSON in `config/shelf_layouts/`
2. Define rows, cols, shelf_region, expected_items
3. Reference in config.yaml

---

## Next Steps

- **[API Reference](API_REFERENCE.md)** - REST and WebSocket API
- **[Configuration Guide](CONFIGURATION.md)** - All configuration options
- **[Development Guide](DEVELOPMENT.md)** - Contributing and extending
