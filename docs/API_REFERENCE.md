# API Reference

Complete REST API and WebSocket API documentation for Inventory-Management-Tracking-System.

## Table of Contents
- [Base URL](#base-url)
- [REST API Endpoints](#rest-api-endpoints)
- [WebSocket API](#websocket-api)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Examples](#examples)

---

## Base URL

**Production Mode:**
```
http://127.0.0.1:5000
```

**Demo Mode:**
```
http://127.0.0.1:5050
```

---

## REST API Endpoints

### System Health

#### GET /api/health
Get system health status and camera information.

**Request:**
```http
GET /api/health HTTP/1.1
Host: 127.0.0.1:5000
```

**Response:**
```json
{
  "status": "healthy",
  "camera_active": true,
  "camera_device": 0,
  "fps": 29.5,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**Status Codes:**
- `200 OK` - System healthy
- `500 Internal Server Error` - System issue

---

### Inventory Management

#### GET /api/inventory
Get all inventory items.

**Request:**
```http
GET /api/inventory HTTP/1.1
Host: 127.0.0.1:5000
```

**Response:**
```json
{
  "bottle": {
    "quantity": 5,
    "low_stock_threshold": 2,
    "last_updated": "2024-01-15T10:30:00",
    "is_low_stock": false
  },
  "cup": {
    "quantity": 1,
    "low_stock_threshold": 2,
    "last_updated": "2024-01-15T10:25:00",
    "is_low_stock": true
  }
}
```

**Status Codes:**
- `200 OK` - Success

---

#### GET /api/inventory/{item_class}
Get specific item details.

**Request:**
```http
GET /api/inventory/bottle HTTP/1.1
Host: 127.0.0.1:5000
```

**Response:**
```json
{
  "item_class": "bottle",
  "quantity": 5,
  "low_stock_threshold": 2,
  "last_updated": "2024-01-15T10:30:00",
  "is_low_stock": false
}
```

**Status Codes:**
- `200 OK` - Item found
- `404 Not Found` - Item does not exist

---

#### POST /api/inventory/{item_class}
Create or update inventory item.

**Request:**
```http
POST /api/inventory/bottle HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "quantity": 10,
  "low_stock_threshold": 3
}
```

**Response:**
```json
{
  "message": "Inventory updated successfully",
  "item_class": "bottle",
  "quantity": 10,
  "low_stock_threshold": 3
}
```

**Status Codes:**
- `200 OK` - Updated existing item
- `201 Created` - Created new item
- `400 Bad Request` - Invalid data

---

#### PUT /api/inventory/{item_class}
Adjust inventory quantity (increment/decrement).

**Request:**
```http
PUT /api/inventory/bottle HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "adjustment": -2,
  "reason": "Manual correction"
}
```

**Response:**
```json
{
  "message": "Inventory adjusted successfully",
  "item_class": "bottle",
  "old_quantity": 10,
  "new_quantity": 8,
  "adjustment": -2
}
```

**Status Codes:**
- `200 OK` - Adjustment successful
- `400 Bad Request` - Invalid adjustment (e.g., would result in negative)
- `404 Not Found` - Item does not exist

---

#### DELETE /api/inventory/{item_class}
Delete inventory item.

**Request:**
```http
DELETE /api/inventory/bottle HTTP/1.1
Host: 127.0.0.1:5000
```

**Response:**
```json
{
  "message": "Item deleted successfully",
  "item_class": "bottle"
}
```

**Status Codes:**
- `200 OK` - Deleted successfully
- `404 Not Found` - Item does not exist

---

### Events

#### GET /api/events
Get event history with optional filtering.

**Request:**
```http
GET /api/events?limit=50&event_type=item_removed&slot_id=SLOT_0_1 HTTP/1.1
Host: 127.0.0.1:5000
```

**Query Parameters:**
- `limit` (int, optional) - Maximum events to return (default: 100)
- `event_type` (string, optional) - Filter by event type
- `slot_id` (string, optional) - Filter by slot ID
- `item_class` (string, optional) - Filter by item class

**Response:**
```json
{
  "events": [
    {
      "event_id": 123,
      "event_type": "item_removed",
      "slot_id": "SLOT_0_1",
      "item_class": "bottle",
      "confidence": 0.89,
      "timestamp": "2024-01-15T10:30:45.123456",
      "metadata": {}
    },
    {
      "event_id": 122,
      "event_type": "item_added",
      "slot_id": "SLOT_0_2",
      "item_class": "cup",
      "confidence": 0.92,
      "timestamp": "2024-01-15T10:28:30.654321",
      "metadata": {}
    }
  ],
  "count": 2,
  "limit": 50
}
```

**Event Types:**
- `item_added` - Item detected in previously empty slot
- `item_removed` - Item removed from slot
- `item_misplaced` - Wrong item in slot
- `uncertain_state` - Flickering/unclear state
- `low_stock` - Stock below threshold

**Status Codes:**
- `200 OK` - Success

---

### Shelf State

#### GET /api/shelf-state
Get current state of all shelf slots.

**Request:**
```http
GET /api/shelf-state HTTP/1.1
Host: 127.0.0.1:5000
```

**Response:**
```json
{
  "slots": {
    "SLOT_0_0": {
      "slot_id": "SLOT_0_0",
      "expected_item": "bottle",
      "current_item": "bottle",
      "confidence": 0.92,
      "state_status": "STABLE",
      "is_occupied": true,
      "is_misplaced": false,
      "last_confirmed": "2024-01-15T10:30:45"
    },
    "SLOT_0_1": {
      "slot_id": "SLOT_0_1",
      "expected_item": "cup",
      "current_item": null,
      "confidence": 0.85,
      "state_status": "STABLE",
      "is_occupied": false,
      "is_misplaced": false,
      "last_confirmed": "2024-01-15T10:30:30"
    }
  },
  "total_slots": 6,
  "occupied_count": 4,
  "empty_count": 2
}
```

**State Status Values:**
- `STABLE` - Confident about current state
- `UNCERTAIN` - Flickering detections
- `TRANSITIONING` - In process of change

**Status Codes:**
- `200 OK` - Success

---

### Alerts

#### GET /api/alerts
Get all alerts with optional filtering.

**Request:**
```http
GET /api/alerts?level=WARNING&acknowledged=false HTTP/1.1
Host: 127.0.0.1:5000
```

**Query Parameters:**
- `level` (string, optional) - Filter by level (INFO, WARNING, CRITICAL)
- `acknowledged` (boolean, optional) - Filter by acknowledgment status
- `item_class` (string, optional) - Filter by item class

**Response:**
```json
{
  "alerts": [
    {
      "alert_id": "alert_1705315845_low_stock_bottle",
      "level": "WARNING",
      "title": "Low Stock Alert",
      "message": "bottle inventory is below threshold (1/2)",
      "item_class": "bottle",
      "slot_id": null,
      "acknowledged": false,
      "timestamp": "2024-01-15T10:30:45.123456"
    }
  ],
  "count": 1,
  "unacknowledged_count": 1
}
```

**Alert Levels:**
- `INFO` - Informational
- `WARNING` - Requires attention
- `CRITICAL` - Urgent action needed

**Status Codes:**
- `200 OK` - Success

---

#### PUT /api/alerts/{alert_id}
Acknowledge or clear an alert.

**Request:**
```http
PUT /api/alerts/alert_1705315845_low_stock_bottle HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "acknowledged": true
}
```

**Response:**
```json
{
  "message": "Alert acknowledged",
  "alert_id": "alert_1705315845_low_stock_bottle",
  "acknowledged": true
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Alert does not exist

---

#### DELETE /api/alerts
Clear all acknowledged alerts.

**Request:**
```http
DELETE /api/alerts HTTP/1.1
Host: 127.0.0.1:5000
```

**Response:**
```json
{
  "message": "Cleared 5 acknowledged alerts",
  "cleared_count": 5
}
```

**Status Codes:**
- `200 OK` - Success

---

### Video Stream

#### GET /api/video-stream
Get live MJPEG video stream.

**Request:**
```http
GET /api/video-stream HTTP/1.1
Host: 127.0.0.1:5000
```

**Response:**
- Content-Type: `multipart/x-mixed-replace; boundary=frame`
- Continuous JPEG frames

**Usage in HTML:**
```html
<img src="http://127.0.0.1:5000/api/video-stream" alt="Live Feed">
```

**Status Codes:**
- `200 OK` - Stream active

---

### Web Pages

#### GET /
Dashboard homepage with live feed.

#### GET /inventory
Inventory management page.

#### GET /events
Event timeline page.

#### GET /alerts
Alerts management page.

---

## WebSocket API

### Connection

**JavaScript Client:**
```javascript
const socket = io('http://127.0.0.1:5000');

socket.on('connect', function() {
    console.log('Connected to Inventory-Management-Tracking-System server');
});

socket.on('disconnect', function() {
    console.log('Disconnected from Inventory-Management-Tracking-System server');
});
```

**Python Client:**
```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to Inventory-Management-Tracking-System server')

@sio.event
def disconnect():
    print('Disconnected from Inventory-Management-Tracking-System server')

sio.connect('http://127.0.0.1:5000')
```

---

### Server → Client Events

#### Event: `event`
Broadcast when a new state transition event occurs.

**Payload:**
```json
{
  "event_id": 123,
  "event_type": "item_removed",
  "slot_id": "SLOT_0_1",
  "item_class": "bottle",
  "confidence": 0.89,
  "timestamp": "2024-01-15T10:30:45.123456",
  "metadata": {}
}
```

**JavaScript Handler:**
```javascript
socket.on('event', function(data) {
    console.log('New event:', data.event_type);
    addEventToTimeline(data);
});
```

---

#### Event: `inventory_update`
Broadcast when inventory quantities change.

**Payload:**
```json
{
  "bottle": {
    "quantity": 4,
    "low_stock_threshold": 2,
    "last_updated": "2024-01-15T10:30:45",
    "is_low_stock": false
  }
}
```

**JavaScript Handler:**
```javascript
socket.on('inventory_update', function(data) {
    updateInventoryDisplay(data);
});
```

---

#### Event: `alert`
Broadcast when a new alert is generated.

**Payload:**
```json
{
  "alert_id": "alert_1705315845_low_stock_bottle",
  "level": "WARNING",
  "title": "Low Stock Alert",
  "message": "bottle inventory is below threshold (1/2)",
  "item_class": "bottle",
  "slot_id": null,
  "acknowledged": false,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

**JavaScript Handler:**
```javascript
socket.on('alert', function(data) {
    showAlertNotification(data);
});
```

---

#### Event: `shelf_state_update`
Broadcast when shelf slot states change.

**Payload:**
```json
{
  "slot_id": "SLOT_0_1",
  "expected_item": "cup",
  "current_item": null,
  "confidence": 0.85,
  "state_status": "STABLE",
  "is_occupied": false,
  "last_confirmed": "2024-01-15T10:30:45"
}
```

**JavaScript Handler:**
```javascript
socket.on('shelf_state_update', function(data) {
    updateShelfSlot(data.slot_id, data);
});
```

---

### Client → Server Events

#### Event: `stream_control`
Control video stream (start/stop).

**Payload:**
```json
{
  "action": "start"
}
```

**Actions:**
- `start` - Start video processing
- `stop` - Stop video processing

**JavaScript Example:**
```javascript
// Start stream
socket.emit('stream_control', { action: 'start' });

// Stop stream
socket.emit('stream_control', { action: 'stop' });
```

**Response:**
No direct response. Stream starts/stops, and subsequent video frames reflect the change.

---

## Data Models

### Inventory Item
```json
{
  "item_class": "bottle",
  "quantity": 5,
  "low_stock_threshold": 2,
  "last_updated": "2024-01-15T10:30:00",
  "is_low_stock": false
}
```

### Event
```json
{
  "event_id": 123,
  "event_type": "item_removed",
  "slot_id": "SLOT_0_1",
  "item_class": "bottle",
  "confidence": 0.89,
  "timestamp": "2024-01-15T10:30:45.123456",
  "metadata": {}
}
```

### Alert
```json
{
  "alert_id": "alert_1705315845_low_stock_bottle",
  "level": "WARNING",
  "title": "Low Stock Alert",
  "message": "bottle inventory is below threshold (1/2)",
  "item_class": "bottle",
  "slot_id": null,
  "acknowledged": false,
  "timestamp": "2024-01-15T10:30:45.123456"
}
```

### Shelf Slot State
```json
{
  "slot_id": "SLOT_0_1",
  "expected_item": "cup",
  "current_item": "bottle",
  "confidence": 0.92,
  "state_status": "STABLE",
  "is_occupied": true,
  "is_misplaced": true,
  "last_confirmed": "2024-01-15T10:30:45"
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "Error message",
  "status": 400,
  "details": "Additional error details"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource does not exist |
| 409 | Conflict - Operation conflicts with current state |
| 500 | Internal Server Error - Server-side error |

---

## Examples

### Example 1: Get Current Inventory and Display

```javascript
// Fetch current inventory
fetch('http://127.0.0.1:5000/api/inventory')
  .then(response => response.json())
  .then(data => {
    for (const [item, details] of Object.entries(data)) {
      console.log(`${item}: ${details.quantity} units`);
      if (details.is_low_stock) {
        console.warn(`⚠️ ${item} is low!`);
      }
    }
  });
```

### Example 2: Manual Inventory Adjustment

```javascript
// Decrement bottle count by 1
fetch('http://127.0.0.1:5000/api/inventory/bottle', {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    adjustment: -1,
    reason: 'Manual sale'
  })
})
  .then(response => response.json())
  .then(data => {
    console.log(`Adjusted ${data.item_class}: ${data.old_quantity} → ${data.new_quantity}`);
  });
```

### Example 3: Real-time Event Monitoring

```javascript
const socket = io('http://127.0.0.1:5000');

// Listen for all events
socket.on('event', function(event) {
  console.log(`[${event.timestamp}] ${event.event_type}: ${event.item_class} in ${event.slot_id}`);
});

// Listen for inventory updates
socket.on('inventory_update', function(inventory) {
  console.log('Inventory updated:', inventory);
});

// Listen for alerts
socket.on('alert', function(alert) {
  if (alert.level === 'CRITICAL') {
    console.error(`🚨 ${alert.title}: ${alert.message}`);
  } else {
    console.warn(`⚠️ ${alert.title}: ${alert.message}`);
  }
});
```

### Example 4: Python REST Client

```python
import requests

BASE_URL = 'http://127.0.0.1:5000'

# Get inventory
response = requests.get(f'{BASE_URL}/api/inventory')
inventory = response.json()
print(inventory)

# Update inventory
response = requests.post(
    f'{BASE_URL}/api/inventory/bottle',
    json={'quantity': 10, 'low_stock_threshold': 3}
)
print(response.json())

# Get events
response = requests.get(
    f'{BASE_URL}/api/events',
    params={'limit': 10, 'event_type': 'item_removed'}
)
events = response.json()
for event in events['events']:
    print(f"{event['timestamp']}: {event['event_type']}")
```

### Example 5: Python WebSocket Client

```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to Inventory-Management-Tracking-System')

@sio.on('event')
def on_event(data):
    print(f"Event: {data['event_type']} - {data['item_class']}")

@sio.on('inventory_update')
def on_inventory_update(data):
    print(f"Inventory updated: {data}")

@sio.on('alert')
def on_alert(data):
    print(f"Alert: {data['title']} - {data['message']}")

sio.connect('http://127.0.0.1:5000')
sio.wait()
```

---

## Rate Limiting

Currently, Inventory-Management-Tracking-System does not implement rate limiting. For production use, consider:
- Adding rate limiting middleware
- Implementing API keys
- Adding authentication/authorization

---

## CORS

CORS is currently configured to allow all origins (`*`). For production:

```python
# backend/app.py
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

## Next Steps

- **[Configuration Guide](CONFIGURATION.md)** - Configure API settings
- **[Architecture](ARCHITECTURE.md)** - Understand system design
- **[Development](DEVELOPMENT.md)** - Extend the API
