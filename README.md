# Inventory-Management-Tracking-System

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-nano-orange.svg)](https://github.com/ultralytics/ultralytics)

**AI-powered vision-based inventory tracking system with intelligent temporal state reasoning**

[Features](#features) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Demo Mode](#demo-mode) • [Architecture](#architecture)

</div>

---

## 🎯 Overview

Inventory-Management-Tracking-System is a production-ready computer vision system that automatically monitors retail shelves and tracks inventory changes in real-time. Unlike simple object detection systems, Inventory-Management-Tracking-System uses **temporal reasoning** to intelligently filter noise and only trigger inventory updates on sustained state changes.

### Key Innovation

Traditional vision systems suffer from false positives due to:
- Brief hand occlusions
- Lighting changes
- Detection flickering

Inventory-Management-Tracking-System solves this with a **temporal reasoning engine** that:
- ✅ Ignores short absences (1-2 frames) as likely occlusions
- ✅ Requires sustained changes (5+ frames) before triggering events
- ✅ Aggregates confidence scores over time
- ✅ Prevents duplicate events with intelligent cooldown

---

## ✨ Features

### Core Capabilities
- 🎥 **Real-time Object Detection** - YOLOv8 nano model at 30 FPS
- 🤝 **Hybrid AI Validation** - Gemini 3.1 Flash Live validates YOLO detections for stronger edge-case handling
- 🧠 **Temporal State Reasoning** - Smart noise filtering and event detection
- 📦 **Automatic Inventory Tracking** - Real-time add/remove detection
- 🌐 **Live Web Dashboard** - Video feed, stats, events, and alerts
- ⚡ **WebSocket Updates** - Instant push notifications
- 🎬 **Demo Mode** - Isolated presentation mode with local images

### Dashboard Features
- Live video stream with detection overlays
- Real-time inventory statistics
- Event timeline with filtering
- Alert management system
- Manual inventory adjustments

### Technical Features
- GPU acceleration support (CUDA)
- Configurable shelf layouts (JSON-based)
- Full audit trail (all events logged)
- RESTful API endpoints
- SQLite database persistence
- Thread-safe processing

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Webcam (optional, demo mode available)
- 8GB+ RAM recommended
- Optional: NVIDIA GPU with CUDA for acceleration

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd Inventory-Management-Tracking-System
```

2. **Create virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Optional: Enable GPU acceleration**
```bash
# For NVIDIA GPUs with CUDA 12.8
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

5. **Optional: Enable Gemini hybrid validation**
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"

# Linux/Mac
export GEMINI_API_KEY="your_api_key_here"
```

When enabled in config, YOLO remains the primary real-time detector used for frontend overlays,
while Gemini adds slot-level validation signals for counting, reasoning, temporal transitions,
misplacement handling, and inventory decision confidence.
If the Gemini API key is missing or unavailable, Inventory-Management-Tracking-System automatically falls back to YOLO-only behavior.

### Running the Application

**Production Mode (with webcam):**
```bash
python main.py
```

Then open your browser to: **http://127.0.0.1:5000**

**Demo Mode (without webcam):**
```bash
# 1. Prepare demo frames
python scripts/prepare_demo_frames.py

# 2. Launch demo
python scripts/run_demo.py
```

Then open your browser to: **http://127.0.0.1:5050**

---

## 📚 Documentation

- **[INSTALLATION.md](docs/INSTALLATION.md)** - Detailed setup and installation guide
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete API documentation
- **[CONFIGURATION.md](docs/CONFIGURATION.md)** - Configuration options
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Developer guide and contributing
- **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - Demo mode presentation guide
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

---

## 🎬 Demo Mode

Demo mode allows you to run Inventory-Management-Tracking-System without a camera, perfect for presentations and testing.

### Quick Demo Setup

1. **Capture demo photos** (optional, if you have sample images):
```bash
python scripts/capture_demo_photos.py --count 8 --interval 1.5
```

2. **Prepare demo frames**:
```bash
python scripts/prepare_demo_frames.py
```

3. **Launch demo**:
```bash
python scripts/run_demo.py
```

4. **Access dashboard**:
```
http://127.0.0.1:5050
```

### Demo Mode Features
- Uses isolated `config.demo.yaml` configuration
- Separate `data/demo_shelf.db` database
- Cycles through prepared images (5 seconds per frame)
- No impact on production data
- Perfect for screenshots and recordings

See [DEMO_GUIDE.md](DEMO_GUIDE.md) for detailed instructions.

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────┐
│   Web Dashboard (HTML/JS/CSS)           │  ← User Interface
└──────────────┬──────────────────────────┘
               │ WebSocket + REST API
┌──────────────▼──────────────────────────┐
│   Flask Backend (SocketIO)              │  ← API Layer
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌─────────┐ ┌──────────┐
│Inventory│ │Reasoning│ │  Vision  │  ← Core Layers
│ Manager │ │ Engine  │ │ Pipeline │
└────────┘ └─────────┘ └──────────┘
    │          │          │
    └──────────┼──────────┘
               ▼
      ┌────────────────┐
      │ SQLite Database│  ← Persistence
      └────────────────┘
```

### Project Structure

```
Inventory-Management-Tracking-System/
├── vision/                 # Computer vision layer
│   ├── pipeline.py        # Main orchestrator
│   ├── camera.py          # Threaded camera capture
│   ├── detector.py        # YOLOv8 wrapper
│   └── slot_mapper.py     # Grid-based slot mapping
│
├── reasoning/             # Temporal reasoning layer
│   ├── reasoning_engine.py  # Core intelligence
│   ├── temporal_buffer.py   # Rolling window buffer
│   ├── shelf_state.py       # State tracking
│   └── event_generator.py   # Event definitions
│
├── inventory/             # Inventory management
│   ├── decision_engine.py   # Event → Action conversion
│   ├── inventory_manager.py # Stock management
│   └── alert_system.py      # Alert generation
│
├── database/              # Persistence layer
│   ├── models.py          # SQLAlchemy ORM models
│   └── db_manager.py      # Database operations
│
├── backend/               # Web API layer
│   ├── app.py             # Flask application
│   ├── routes.py          # REST endpoints
│   └── websocket.py       # WebSocket handlers
│
├── frontend/              # User interface
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, assets
│
├── config/                # Configuration
│   └── shelf_layouts/     # JSON layout definitions
│
├── scripts/               # Utility scripts
│   ├── run_demo.py              # Demo launcher
│   ├── capture_demo_photos.py   # Photo capture
│   └── prepare_demo_frames.py   # Frame preparation
│
├── tests/                 # Unit tests
├── utils/                 # Utilities (logger, config loader)
├── data/                  # Runtime data (databases)
├── demo_assets/          # Demo images
├── main.py               # Application entry point
├── config.yaml           # Production configuration
├── config.demo.yaml      # Demo configuration
└── requirements.txt      # Python dependencies
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

---

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.8+ |
| **Web Framework** | Flask | 3.0.0 |
| **WebSocket** | Flask-SocketIO | 5.3.4 |
| **Object Detection** | YOLOv8 (Ultralytics) | 8.3.0+ |
| **Deep Learning** | PyTorch | 2.6+ |
| **Computer Vision** | OpenCV | 4.8.1 |
| **Hybrid Validation** | Gemini 3.1 Flash Live | Preview |
| **Database** | SQLite + SQLAlchemy | 2.0.21 |
| **Configuration** | PyYAML | 6.0.1 |
| **Testing** | Pytest | 7.4.3 |

---

## 🎯 Use Cases

- **Retail Stores** - Automatic shelf inventory tracking
- **Warehouses** - Storage bin monitoring
- **Vending Machines** - Stock level detection
- **Smart Refrigerators** - Food inventory management
- **Libraries** - Book tracking on shelves
- **Research** - Computer vision and temporal reasoning studies

---

## 📊 Performance

- **Detection Speed**: 20-30ms per frame (CPU), 5-10ms (GPU)
- **Frame Rate**: 30 FPS (configurable)
- **Reasoning Latency**: <5ms per frame
- **Database Write**: 1-5ms per operation
- **WebSocket Latency**: <10ms (LAN)

---

## 🔒 Security Notes

**Current Implementation** (Development/Demo):
- ⚠️ No authentication implemented
- ⚠️ CORS allows all origins
- ⚠️ SQLite without encryption
- ⚠️ Hardcoded secret keys

**Production Recommendations**:
- ✅ Implement JWT/OAuth authentication
- ✅ Restrict CORS to specific origins
- ✅ Use environment variables for secrets
- ✅ Switch to PostgreSQL with encryption
- ✅ Add rate limiting
- ✅ Enable HTTPS/WSS

See [SECURITY.md](docs/SECURITY.md) for security hardening guide.

---

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_reasoning.py

# Run with coverage
pytest --cov=. tests/
```

---

## 🤝 Contributing

Contributions are welcome! Please see our contribution guidelines:
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines and process
- [DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development setup and standards
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community guidelines

---

## 📚 Additional Resources

- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Complete repository organization guide
- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [CLEANUP_REPORT.md](CLEANUP_REPORT.md) - Repository maintenance report

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ultralytics YOLOv8** - Object detection model
- **Flask** - Web framework
- **OpenCV** - Computer vision library
- **PyTorch** - Deep learning framework

---

## 📧 Support

For issues, questions, or contributions:
- 🐛 **Bug Reports**: [Open an issue](../../issues)
- 💡 **Feature Requests**: [Open an issue](../../issues)
- 📖 **Documentation**: See [docs/](docs/) folder

