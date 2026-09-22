# Inventory-Management-Tracking-System Project Structure

This document provides an overview of the Inventory-Management-Tracking-System repository structure and organization.

## Root Directory

```
Inventory-Management-Tracking-System/
├── backend/                    # Backend API and server
├── config/                     # Configuration files
├── data/                       # Data storage
├── database/                   # Database module
├── demo_assets/                # Demo mode resources
├── docs/                       # Complete documentation
├── frontend/                   # Web dashboard
├── inventory/                  # Inventory management module
├── reasoning/                  # Temporal reasoning engine
├── scripts/                    # Utility scripts
├── tests/                      # Test suite
├── utils/                      # Shared utilities
├── vision/                     # Computer vision module
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── config.yaml                 # Production configuration
├── config.demo.yaml            # Demo configuration
├── yolov8n.pt                  # YOLOv8 model weights
├── README.md                   # Project overview
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── .gitignore                  # Git ignore rules
├── DEMO_GUIDE.md               # Demo mode guide
└── DEMO_RECORDING_SCRIPT.md    # Demo recording instructions
```

---

## Module Breakdown

### `/backend` - Backend API Server
```
backend/
├── __init__.py                 # Module initialization
├── api.py                      # Flask application setup
├── routes.py                   # REST API endpoints
└── websocket.py                # WebSocket event handlers
```

**Purpose:** Flask-based REST API and WebSocket server
**Key Files:**
- `api.py` - Application factory, CORS setup, SocketIO initialization
- `routes.py` - 15+ REST endpoints for inventory/alerts/events
- `websocket.py` - Real-time event broadcasting

---

### `/config` - Configuration Files
```
config/
└── shelf_layout.json           # Shelf grid configuration
```

**Purpose:** Runtime configuration files
**Key Files:**
- `shelf_layout.json` - Defines shelf dimensions and slot positions

---

### `/data` - Data Storage
```
data/
├── logs/                       # Application logs
│   └── inventory-management-tracking-system.log  # Main log file
└── shelf.db                    # SQLite database (gitignored)
```

**Purpose:** Persistent data storage
**Database Schema:** 5 tables (inventory, shelf_state, events_log, inventory_actions, alerts)

---

### `/database` - Database Module
```
database/
├── __init__.py                 # Module exports
├── connection.py               # Database connection management
└── models.py                   # SQLAlchemy ORM models
```

**Purpose:** Database abstraction layer
**Key Components:**
- SQLAlchemy ORM models for 5 tables
- Connection pooling and session management
- Schema auto-creation

---

### `/demo_assets` - Demo Mode Resources
```
demo_assets/
├── inventory_photos/           # Product images for demo
│   ├── Gemini_Generated_Image_86nqwm86nqwm86nq.png  (8.4 MB)
│   └── Gemini_Generated_Image_p209s8p209s8p209.png  (8.5 MB)
└── inventory_frames/           # Pre-recorded frames
    ├── demo_frame_1.jpg
    ├── demo_frame_2.jpg
    └── ...                     # Additional frames
```

**Purpose:** Assets for demo mode presentations
**Note:** Large PNG files (16.9 MB total) used for demo inventory display

---

### `/docs` - Documentation
```
docs/
├── README.md                   # Documentation index (10.3 KB)
├── INSTALLATION.md             # Setup guide (8.5 KB)
├── USER_GUIDE.md               # User manual (15.6 KB)
├── ARCHITECTURE.md             # Technical architecture (20.2 KB)
├── API_REFERENCE.md            # API documentation (16.2 KB)
├── CONFIGURATION.md            # Config options (15.5 KB)
├── DEVELOPMENT.md              # Developer guide (16.0 KB)
├── TROUBLESHOOTING.md          # Issue solutions (15.5 KB)
└── TECHNICAL_ARCHITECTURE_DOCUMENT.md  # Complete UML diagrams (98.7 KB)
```

**Purpose:** Complete project documentation (120,000+ words)
**Highlights:**
- 8 comprehensive guides
- 6 UML diagrams in ASCII format
- Cross-referenced navigation
- Production-ready documentation

---

### `/frontend` - Web Dashboard
```
frontend/
├── index.html                  # Main dashboard page
├── styles.css                  # Dashboard styling
└── app.js                      # Client-side logic
```

**Purpose:** Vanilla JavaScript web interface
**Features:**
- Real-time video feed display
- Inventory grid visualization
- Event log viewer
- Alert management panel
- Manual inventory controls

---

### `/inventory` - Inventory Management Module
```
inventory/
├── __init__.py                 # Module exports
├── manager.py                  # Inventory CRUD operations
└── slot.py                     # Slot data structure
```

**Purpose:** High-level inventory management
**Key Classes:**
- `InventoryManager` - Main inventory interface
- `Slot` - Individual shelf slot representation

---

### `/reasoning` - Temporal Reasoning Engine
```
reasoning/
├── __init__.py                 # Module exports
├── engine.py                   # Core reasoning logic
├── rules.py                    # Reasoning rules (5 rules)
└── state.py                    # Slot state tracking
```

**Purpose:** Intelligence layer for event detection
**Algorithm:**
- 10-frame temporal buffer
- 5 reasoning rules
- Duplicate prevention (5-sec cooldown)
- Noise filtering

---

### `/scripts` - Utility Scripts
```
scripts/
├── __init__.py
├── demo_photo_capture.py       # Capture demo photos
├── demo_frame_preparation.py   # Prepare demo frames
└── demo_recording_script.py    # Demo recording automation
```

**Purpose:** Development and demo utilities
**Use Cases:**
- Demo mode setup
- Testing utilities
- Maintenance scripts

---

### `/tests` - Test Suite
```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration
├── test_inventory.py           # Inventory module tests
├── test_reasoning.py           # Reasoning engine tests
├── test_vision.py              # Vision pipeline tests
└── test_database.py            # Database layer tests
```

**Purpose:** Automated testing with pytest
**Coverage:** Core modules (inventory, reasoning, vision, database)

---

### `/utils` - Shared Utilities
```
utils/
├── __init__.py
├── config_loader.py            # YAML configuration loader
└── logger.py                   # Logging configuration
```

**Purpose:** Common functionality across modules
**Components:**
- Configuration management
- Structured logging
- Helper functions

---

### `/vision` - Computer Vision Module
```
vision/
├── __init__.py                 # Module exports
├── camera.py                   # Camera capture
├── detector.py                 # YOLOv8 detection
└── slot_mapper.py              # Detection-to-slot mapping
```

**Purpose:** Vision pipeline for object detection
**Pipeline:**
1. Camera capture (OpenCV)
2. YOLOv8 detection
3. Slot mapping (bounding box → shelf grid)

---

## Configuration Files

### `config.yaml` - Production Configuration
Main configuration file with sections:
- Camera settings (FPS, resolution, device)
- Detection parameters (confidence, IoU)
- Reasoning thresholds (temporal windows)
- Inventory settings (low stock thresholds)
- API settings (host, port, CORS)

### `config.demo.yaml` - Demo Configuration
Isolated demo mode settings:
- Demo frame paths
- Separate database
- Different port (5001)

### `.gitignore` - Git Ignore Rules
Comprehensive ignore rules for:
- Python cache (`__pycache__`, `*.pyc`)
- Virtual environments
- Database files (`*.db`)
- Log files
- IDE settings
- OS files
- Test artifacts

---

## Entry Point

### `main.py` - Application Entry Point
**Purpose:** Initialize and start Inventory-Management-Tracking-System application
**Initialization Sequence:**
1. Load configuration
2. Setup logging
3. Initialize database
4. Load YOLOv8 model
5. Initialize vision pipeline
6. Create reasoning engine
7. Start Flask API server

**Background Loop:**
- Capture frame
- Detect objects
- Analyze with reasoning
- Execute actions
- Update database
- Broadcast WebSocket events

---

## Dependencies

### `requirements.txt` - Python Dependencies
**Core Dependencies:**
- Flask 3.0.0 - Web framework
- Flask-SocketIO 5.3.4 - WebSocket support
- Ultralytics 8.3.0+ - YOLOv8
- PyTorch 2.6+ - Deep learning
- OpenCV 4.8.1 - Computer vision
- SQLAlchemy 2.0.21 - ORM
- PyYAML 6.0.1 - Config parsing

**Total:** 15+ packages with transitive dependencies

---

## Model Files

### `yolov8n.pt` - YOLOv8 Nano Model
**Size:** 6.25 MB
**Type:** PyTorch model weights
**Purpose:** Object detection
**Details:**
- Nano variant (3.2M parameters)
- 80 COCO classes
- Auto-downloads if missing

---

## Data Flow

```
Camera → Vision → Reasoning → Inventory → Database
   ↓         ↓          ↓           ↓          ↓
   Frame   Detect    Analyze    Update    Persist
           ↓          ↓           ↓          ↓
         Slots    Events     Actions    WebSocket
                                             ↓
                                        Frontend
```

---

## Module Dependencies

```
main.py
  ├── utils (config, logging)
  ├── database (models, connection)
  ├── vision (camera, detector, mapper)
  ├── reasoning (engine, rules, state)
  ├── inventory (manager, slot)
  └── backend (api, routes, websocket)
      └── frontend (HTML/CSS/JS)
```

---

## File Size Summary

| Category | Files | Total Size |
|----------|-------|------------|
| **Python Code** | 30+ | ~500 KB |
| **Documentation** | 11 | ~220 KB |
| **Model** | 1 | 6.25 MB |
| **Demo Assets** | 20+ | ~17 MB |
| **Configuration** | 3 | ~10 KB |
| **Frontend** | 3 | ~50 KB |
| **Tests** | 5 | ~100 KB |
| **Total** | 73+ | ~24.6 MB |

---

## Clean Repository Status

### ✅ Removed (Cleanup Complete)
- All `__pycache__/` directories
- All `.pyc` compiled files
- `.pytest_cache/` directory
- Temporary files

### ✅ Properly Ignored
- Database files (`*.db`)
- Virtual environments
- IDE settings
- Log files
- OS temporary files

### ✅ Kept (Essential)
- Source code
- Documentation
- Configuration files
- YOLOv8 model weights
- Demo assets (for presentations)
- Tests

---

## Development Workflow

### 1. Clone Repository
```bash
git clone <repository_url>
cd Inventory-Management-Tracking-System
```

### 2. Setup Environment
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Configure
```bash
cp config.yaml config.local.yaml
# Edit config.local.yaml as needed
```

### 4. Run Application
```bash
python main.py
```

### 5. Access Dashboard
```
http://localhost:5000
```

---

## Documentation Navigation

Start with these files based on your role:

**End Users:**
- README.md → docs/INSTALLATION.md → docs/USER_GUIDE.md

**Developers:**
- README.md → docs/ARCHITECTURE.md → docs/DEVELOPMENT.md

**API Integrators:**
- docs/API_REFERENCE.md

**System Admins:**
- docs/CONFIGURATION.md → docs/TROUBLESHOOTING.md

**Academic/Professional:**
- docs/TECHNICAL_ARCHITECTURE_DOCUMENT.md

---

## Maintenance

### Regular Updates
- Update CHANGELOG.md for version releases
- Keep dependencies updated (check for security issues)
- Review and update documentation
- Maintain test coverage

### Backup Important Files
- Configuration files
- Database (`data/shelf.db`)
- Custom shelf layouts
- Logs (for debugging)

---

## Notes

- **Repository is clean:** No cache files, no temporary files
- **Well-documented:** 120,000+ words of documentation
- **Production-ready:** Comprehensive error handling and logging
- **Extensible:** Modular architecture allows easy additions
- **Tested:** Test suite covers core functionality

---

For detailed information about each module, see:
- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Technical Architecture Document](docs/TECHNICAL_ARCHITECTURE_DOCUMENT.md)
