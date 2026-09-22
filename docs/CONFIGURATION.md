# Configuration Guide

Complete guide to configuring Inventory-Management-Tracking-System for different use cases.

## Table of Contents
- [Configuration Files](#configuration-files)
- [System Settings](#system-settings)
- [Camera Settings](#camera-settings)
- [Detection Settings](#detection-settings)
- [Shelf Configuration](#shelf-configuration)
- [Reasoning Settings](#reasoning-settings)
- [Inventory Settings](#inventory-settings)
- [Database Settings](#database-settings)
- [API Settings](#api-settings)
- [Use Case Examples](#use-case-examples)

---

## Configuration Files

Inventory-Management-Tracking-System uses YAML configuration files for all settings.

### Primary Configurations

**config.yaml** - Production configuration
```yaml
# Default configuration for production use with webcam
```

**config.demo.yaml** - Demo/presentation configuration
```yaml
# Isolated demo mode using local image sequences
```

### Configuration Priority

1. Command-line arguments (highest)
2. Specified config file (`--config path/to/config.yaml`)
3. `config.yaml` (default)

### Loading Configuration

```bash
# Use default config.yaml
python main.py

# Use custom configuration
python main.py --config my_config.yaml

# Use demo configuration
python scripts/run_demo.py  # Automatically uses config.demo.yaml
```

---

## System Settings

```yaml
system:
  name: "Inventory-Management-Tracking-System"
  version: "1.0.0"
  debug: true  # Enable debug logging
```

### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | "Inventory-Management-Tracking-System" | System name for logs |
| `version` | string | "1.0.0" | Version identifier |
| `debug` | boolean | `true` | Enable debug-level logging |

---

## Camera Settings

```yaml
camera:
  device_id: 0
  device_candidates: [0, 1, 2, 3]
  fps: 30
  resolution: [1280, 720]
  buffer_size: 2
  backend: "dshow"
  fourcc: "MJPG"
  warmup_frames: 12
  auto_exposure: 0.75
  strict_signal_validation: true
  no_signal_mean_threshold: 8.0
  use_demo_fallback_on_no_signal: false
  
  # Demo mode settings
  force_demo_mode: false
  demo_frames_path: "demo_assets/inventory_frames"
  demo_frame_interval_seconds: 5.0
```

### Camera Device Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `device_id` | integer | `0` | Primary camera device ID |
| `device_candidates` | array | `[0, 1, 2, 3]` | Probe order if primary fails |
| `fps` | integer | `30` | Target frames per second |
| `resolution` | array | `[1280, 720]` | Width x height in pixels |
| `buffer_size` | integer | `2` | Frame buffer size |

**Recommended FPS:**
- High performance: 30 FPS
- Balanced: 20 FPS
- Low CPU: 10-15 FPS

**Recommended Resolutions:**
- Full HD: `[1920, 1080]` (higher accuracy, slower)
- HD: `[1280, 720]` (balanced - recommended)
- SD: `[640, 480]` (faster, lower accuracy)

### Backend Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `backend` | string | `"dshow"` | OpenCV video backend |
| `fourcc` | string | `"MJPG"` | Video codec |

**Available Backends:**
- Windows: `"dshow"` (DirectShow)
- Linux: `"v4l2"` (Video4Linux2)
- macOS: `"avfoundation"` (AVFoundation)
- Generic: `"auto"` (auto-detect)

**Common Codecs:**
- `"MJPG"` - Motion JPEG (recommended, high FPS)
- `"YUYV"` - YUV 4:2:2 (lower CPU)
- `"H264"` - H.264 compression

### Signal Validation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `warmup_frames` | integer | `12` | Frames to skip on startup |
| `auto_exposure` | float | `0.75` | Auto-exposure setting (0=manual, 1=auto) |
| `strict_signal_validation` | boolean | `true` | Detect "no signal" conditions |
| `no_signal_mean_threshold` | float | `8.0` | Brightness threshold for "no signal" |
| `use_demo_fallback_on_no_signal` | boolean | `false` | Auto-fallback to demo frames |

### Demo Mode

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force_demo_mode` | boolean | `false` | Force demo mode (no camera) |
| `demo_frames_path` | string | `"demo_assets/inventory_frames"` | Path to demo images |
| `demo_frame_interval_seconds` | float | `5.0` | Seconds per demo frame |

---

## Detection Settings

```yaml
detection:
  model: "yolov8n.pt"
  confidence_threshold: 0.5
  iou_threshold: 0.4
  device: "auto"
  use_half_precision: true
```

### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | `"yolov8n.pt"` | YOLOv8 model file |
| `confidence_threshold` | float | `0.5` | Minimum confidence (0.0-1.0) |
| `iou_threshold` | float | `0.4` | IoU threshold for NMS |
| `device` | string | `"auto"` | Compute device |
| `use_half_precision` | boolean | `true` | Use FP16 on GPU |

### Model Options

**Available YOLOv8 Models:**
- `yolov8n.pt` - Nano (3.2M params, fastest) ⭐ Recommended
- `yolov8s.pt` - Small (11.2M params)
- `yolov8m.pt` - Medium (25.9M params)
- `yolov8l.pt` - Large (43.7M params)
- `yolov8x.pt` - Extra Large (68.2M params, most accurate)

**Custom Models:**
```yaml
detection:
  model: "path/to/custom_model.pt"
```

### Confidence Threshold

Higher values = fewer false positives, might miss some detections
Lower values = more detections, more false positives

**Recommendations:**
- Production: `0.5` (balanced)
- High precision: `0.7-0.8` (few false positives)
- High recall: `0.3-0.4` (catch everything)
- Demo: `0.2-0.3` (varied image quality)

### Device Options

| Value | Description |
|-------|-------------|
| `"auto"` | Auto-detect (GPU if available, else CPU) |
| `"cpu"` | Force CPU |
| `"cuda:0"` | Force GPU 0 |
| `"cuda:1"` | Force GPU 1 (multi-GPU systems) |

---

## Shelf Configuration

```yaml
shelf:
  layout: "config/shelf_layouts/retail_3x2.json"
  rows: 2
  cols: 3
```

### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `layout` | string | `"config/shelf_layouts/retail_3x2.json"` | Path to layout JSON |
| `rows` | integer | `2` | Number of rows |
| `cols` | integer | `3` | Number of columns |

### Layout JSON Format

**Example: config/shelf_layouts/retail_3x2.json**

```json
{
  "name": "Retail 3x2 Layout",
  "rows": 2,
  "cols": 3,
  "shelf_region": {
    "x1": 100,
    "y1": 100,
    "x2": 1180,
    "y2": 620
  },
  "expected_items": {
    "SLOT_0_0": "bottle",
    "SLOT_0_1": "cup",
    "SLOT_0_2": "bottle",
    "SLOT_1_0": "book",
    "SLOT_1_1": "bottle",
    "SLOT_1_2": "cup"
  }
}
```

### Creating Custom Layouts

1. **Create JSON file** in `config/shelf_layouts/`
2. **Define grid** (rows x cols)
3. **Set shelf region** (bounding box in pixels)
4. **Map expected items** per slot

**Slot ID Format:** `SLOT_{row}_{col}` (0-indexed)

**Example 2x4 Layout:**
```json
{
  "name": "Vending Machine 2x4",
  "rows": 2,
  "cols": 4,
  "shelf_region": {
    "x1": 50,
    "y1": 50,
    "x2": 1230,
    "y2": 670
  },
  "expected_items": {
    "SLOT_0_0": "bottle",
    "SLOT_0_1": "bottle",
    "SLOT_0_2": "can",
    "SLOT_0_3": "can",
    "SLOT_1_0": "bottle",
    "SLOT_1_1": "bottle",
    "SLOT_1_2": "can",
    "SLOT_1_3": "can"
  }
}
```

---

## Reasoning Settings

```yaml
reasoning:
  temporal_window: 10
  short_absence_threshold: 2
  removal_threshold: 5
  addition_threshold: 3
  mismatch_threshold: 4
  confidence_threshold: 0.7
  duplicate_prevention_seconds: 5
```

### Temporal Reasoning Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `temporal_window` | integer | `10` | Frames to buffer per slot |
| `short_absence_threshold` | integer | `2` | Ignore absences ≤ this (occlusions) |
| `removal_threshold` | integer | `5` | Frames to confirm removal |
| `addition_threshold` | integer | `3` | Frames to confirm addition |
| `mismatch_threshold` | integer | `4` | Frames to confirm misplacement |
| `confidence_threshold` | float | `0.7` | Minimum confidence for events |
| `duplicate_prevention_seconds` | integer | `5` | Cooldown between same events |

### Tuning Reasoning

**For faster event detection:**
```yaml
reasoning:
  removal_threshold: 3      # Faster removal detection
  addition_threshold: 2     # Faster addition detection
  mismatch_threshold: 2     # Faster misplacement detection
```

**For more conservative (fewer false events):**
```yaml
reasoning:
  removal_threshold: 8      # Slower, more confident
  addition_threshold: 5
  mismatch_threshold: 6
  confidence_threshold: 0.8  # Higher confidence required
```

**For demo mode (fast responses):**
```yaml
reasoning:
  temporal_window: 6
  removal_threshold: 3
  addition_threshold: 2
  confidence_threshold: 0.5  # More lenient
```

---

## Inventory Settings

```yaml
inventory:
  low_stock_threshold: 2
  shelf_low_stock_threshold: 1
  shelf_count_confidence_threshold: 0.6
  alert_cooldown_seconds: 60
  seed_on_startup: true
  seed_mode: "merge"
  seed_items:
    book: 24
    apple: 36
    cup: 24
    headphones: 12
    banana: 30
    bottle: 24
  auto_update: true
  min_confidence: 0.7
  prevent_negative: true
```

### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `low_stock_threshold` | integer | `2` | Alert when quantity ≤ this |
| `shelf_low_stock_threshold` | integer | `1` | Minimum desired shelf count before alert |
| `shelf_count_confidence_threshold` | float | `0.6` | Fused confidence needed to count shelf items |
| `alert_cooldown_seconds` | integer | `60` | Cooldown between repeated alerts per item |
| `seed_on_startup` | boolean | `false` | Seed inventory when database is empty |
| `seed_mode` | string | `"merge"` | `merge` adds missing items, `replace` overwrites seed items |
| `seed_items` | object | `{}` | Inventory seed map (`item_class: quantity`) |
| `auto_update` | boolean | `true` | Auto increment/decrement |
| `min_confidence` | float | `0.7` | Min confidence for auto-updates |
| `prevent_negative` | boolean | `true` | Block negative inventory |

---

## Database Settings

```yaml
database:
  path: "data/shelf.db"
  echo: false
  pool_size: 5
  max_overflow: 10
```

### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | string | `"data/shelf.db"` | SQLite database file path |
| `echo` | boolean | `false` | Log all SQL queries |
| `pool_size` | integer | `5` | Connection pool size |
| `max_overflow` | integer | `10` | Max overflow connections |

### Database Paths

**Production:**
```yaml
database:
  path: "data/shelf.db"
```

**Demo:**
```yaml
database:
  path: "data/demo_shelf.db"
```

**Separate per-environment:**
```yaml
database:
  path: "data/shelf_production.db"  # Production
  # path: "data/shelf_staging.db"   # Staging
  # path: "data/shelf_dev.db"       # Development
```

---

## API Settings

```yaml
api:
  host: "127.0.0.1"
  port: 5000
  debug: true
  cors_origins: "*"
  secret_key: "dev-secret-key-change-in-production"
```

### Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | string | `"127.0.0.1"` | Server host address |
| `port` | integer | `5000` | Server port |
| `debug` | boolean | `true` | Flask debug mode |
| `cors_origins` | string | `"*"` | CORS allowed origins |
| `secret_key` | string | - | Flask secret key |

### Production Recommendations

```yaml
api:
  host: "0.0.0.0"  # Listen on all interfaces
  port: 5000
  debug: false  # Disable debug in production
  cors_origins: "https://yourdomain.com"  # Specific domain
  secret_key: "${FLASK_SECRET_KEY}"  # Use environment variable
```

---

## Use Case Examples

### Use Case 1: High-Performance Production

```yaml
camera:
  fps: 30
  resolution: [1280, 720]
  backend: "dshow"
  
detection:
  model: "yolov8s.pt"  # Slightly larger model
  confidence_threshold: 0.6
  device: "cuda:0"  # GPU required
  use_half_precision: true
  
reasoning:
  temporal_window: 10
  removal_threshold: 5
  confidence_threshold: 0.75
  
inventory:
  low_stock_threshold: 5
  auto_update: true
  min_confidence: 0.75
```

### Use Case 2: Low-Resource CPU Mode

```yaml
camera:
  fps: 15  # Lower FPS
  resolution: [640, 480]  # Lower resolution
  
detection:
  model: "yolov8n.pt"  # Nano model
  confidence_threshold: 0.5
  device: "cpu"
  use_half_precision: false
  
reasoning:
  temporal_window: 8
  removal_threshold: 4
  
inventory:
  low_stock_threshold: 2
```

### Use Case 3: Demo/Presentation Mode

```yaml
camera:
  force_demo_mode: true
  demo_frame_interval_seconds: 5.0
  fps: 8
  
detection:
  model: "yolov8n.pt"
  confidence_threshold: 0.2  # More lenient
  device: "cpu"
  
reasoning:
  temporal_window: 6
  removal_threshold: 3  # Faster events
  addition_threshold: 2
  confidence_threshold: 0.5
  
database:
  path: "data/demo_shelf.db"  # Separate DB
  
api:
  port: 5050  # Different port
```

### Use Case 4: Warehouse (Large Items)

```yaml
camera:
  fps: 20
  resolution: [1920, 1080]  # Higher res for detail
  
detection:
  model: "yolov8m.pt"  # Medium model
  confidence_threshold: 0.6
  device: "cuda:0"
  
shelf:
  layout: "config/shelf_layouts/warehouse_4x6.json"
  rows: 4
  cols: 6
  
reasoning:
  temporal_window: 15  # More buffering
  removal_threshold: 8  # More conservative
  confidence_threshold: 0.8
  
inventory:
  low_stock_threshold: 10  # Larger threshold
```

### Use Case 5: Vending Machine

```yaml
camera:
  fps: 30
  resolution: [1280, 720]
  
detection:
  model: "yolov8n.pt"
  confidence_threshold: 0.6
  device: "auto"
  
shelf:
  layout: "config/shelf_layouts/vending_6x4.json"
  rows: 6
  cols: 4
  
reasoning:
  temporal_window: 12
  removal_threshold: 4  # Quick detection
  addition_threshold: 4  # Detect restocking
  confidence_threshold: 0.7
  
inventory:
  low_stock_threshold: 3
  auto_update: true
```

---

## Environment Variables

Currently, Inventory-Management-Tracking-System reads configuration from YAML files. To use environment variables:

### Future Enhancement Example

```python
# config_loader.py
import os

def get_config_value(key, default):
    # Check environment variable first
    env_key = f"GSIP_{key.upper()}"
    return os.getenv(env_key, default)
```

**Usage:**
```bash
export GSIP_API_PORT=8080
export GSIP_DEVICE_ID=1
python main.py
```

---

## Configuration Validation

Inventory-Management-Tracking-System validates configuration on startup. Common errors:

### Invalid FPS
```
Error: FPS must be between 1 and 60
```
Fix: Set `camera.fps` to 1-60

### Invalid Confidence
```
Error: Confidence threshold must be between 0.0 and 1.0
```
Fix: Set thresholds to 0.0-1.0 range

### Model Not Found
```
Error: YOLOv8 model not found: custom_model.pt
```
Fix: Ensure model file exists at specified path

### Layout File Missing
```
Error: Shelf layout file not found
```
Fix: Ensure JSON file exists at `shelf.layout` path

---

## Troubleshooting Configuration

### Camera not detected
Try different `device_id` values:
```yaml
camera:
  device_candidates: [0, 1, 2, 3]  # Will probe all
```

### Slow performance
Reduce FPS and resolution:
```yaml
camera:
  fps: 15
  resolution: [640, 480]
```

### Too many false events
Increase thresholds:
```yaml
reasoning:
  removal_threshold: 8
  confidence_threshold: 0.8
```

### Missing events
Decrease thresholds:
```yaml
reasoning:
  removal_threshold: 3
  confidence_threshold: 0.5
```

---

## Next Steps

- **[Architecture](ARCHITECTURE.md)** - Understand how configuration affects system
- **[Development](DEVELOPMENT.md)** - Add new configuration options
- **[API Reference](API_REFERENCE.md)** - API endpoints for runtime configuration
