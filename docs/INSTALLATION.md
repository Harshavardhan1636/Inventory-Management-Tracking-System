# Installation Guide

Complete installation and setup guide for Inventory-Management-Tracking-System.

## Table of Contents
- [System Requirements](#system-requirements)
- [Python Installation](#python-installation)
- [Project Setup](#project-setup)
- [GPU Acceleration](#gpu-acceleration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 10.15+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Camera**: USB webcam (optional for demo mode)

### Recommended for Production
- **CPU**: 4+ cores (Intel i5/i7, AMD Ryzen 5/7)
- **RAM**: 8GB+
- **GPU**: NVIDIA GPU with CUDA support (optional, 5-10x speedup)
- **Storage**: 10GB+ (for database growth)
- **Network**: Stable LAN connection for WebSocket

---

## Python Installation

### Windows

1. **Download Python**
   - Visit [python.org](https://www.python.org/downloads/)
   - Download Python 3.8 or newer
   - **Important**: Check "Add Python to PATH" during installation

2. **Verify Installation**
   ```powershell
   python --version
   # Should output: Python 3.8.x or higher
   ```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.8+
sudo apt install python3.8 python3.8-venv python3-pip

# Verify installation
python3 --version
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.8

# Verify installation
python3 --version
```

---

## Project Setup

### Step 1: Clone or Download

**Option A: Git Clone**
```bash
git clone <repository-url>
cd Inventory-Management-Tracking-System
```

**Option B: Download ZIP**
1. Download and extract the project ZIP
2. Navigate to the extracted folder

### Step 2: Create Virtual Environment

**Windows:**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Your prompt should now show (venv)
```

**Linux/macOS:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Your prompt should now show (venv)
```

**Deactivating Later:**
```bash
deactivate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This installs:
- Flask 3.0.0 (web framework)
- Flask-SocketIO 5.3.4 (WebSocket)
- ultralytics 8.3.0+ (YOLOv8)
- opencv-python 4.8.1.78 (computer vision)
- torch 2.6+ (deep learning)
- SQLAlchemy 2.0.21 (database ORM)
- And more (see requirements.txt)

**Installation typically takes 2-5 minutes depending on internet speed.**

### Step 4: Verify Installation

```bash
# Check installed packages
pip list

# Look for key packages:
# - flask
# - flask-socketio
# - ultralytics
# - opencv-python
# - torch
```

---

## GPU Acceleration

### NVIDIA GPU (CUDA)

If you have an NVIDIA GPU, you can enable GPU acceleration for 5-10x faster inference.

**Step 1: Check GPU Compatibility**
```bash
# Windows/Linux
nvidia-smi

# Should show your GPU information
```

**Step 2: Install CUDA-enabled PyTorch**

```bash
# For CUDA 12.8 (latest)
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# For CUDA 11.8
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Step 3: Verify GPU Detection**

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
```

Expected output if successful:
```
CUDA available: True
Device: NVIDIA GeForce RTX 3060 (or your GPU model)
```

### Configuration

GPU is auto-detected by default. To force CPU:

**config.yaml:**
```yaml
detection:
  device: "cpu"  # Force CPU
  # device: "auto"  # Auto-detect (default)
  # device: "cuda:0"  # Force specific GPU
```

---

## Verification

### Quick Verification Test

1. **Check Python and packages:**
   ```bash
   python --version
   pip list | grep -E "flask|ultralytics|opencv|torch"
   ```

2. **Test import:**
   ```python
   python -c "import flask, ultralytics, cv2, torch; print('All imports successful!')"
   ```

3. **Run application:**
   ```bash
   python main.py
   ```

   Expected output:
   ```
   2024-01-15 10:30:00 - INFO - Loading configuration from config.yaml
   2024-01-15 10:30:01 - INFO - Database initialized
   2024-01-15 10:30:02 - INFO - YOLOv8 model loaded
   2024-01-15 10:30:03 - INFO - Camera initialized (device 0)
   2024-01-15 10:30:04 - INFO - Server running on http://127.0.0.1:5000
   ```

4. **Open browser:**
   - Navigate to: http://127.0.0.1:5000
   - You should see the Inventory-Management-Tracking-System dashboard

---

## First Run

### With Webcam

1. **Start application:**
   ```bash
   python main.py
   ```

2. **Grant camera permissions** (if prompted)

3. **Open dashboard:**
   http://127.0.0.1:5000

4. **Click "Start Stream"** to begin detection

### Without Webcam (Demo Mode)

1. **Prepare demo frames:**
   ```bash
   python scripts/prepare_demo_frames.py
   ```

2. **Launch demo:**
   ```bash
   python scripts/run_demo.py
   ```

3. **Open demo dashboard:**
   http://127.0.0.1:5050

---

## Troubleshooting

### Common Issues

#### "Python not found" or "pip not found"
- **Solution**: Python not in PATH. Reinstall Python with "Add to PATH" checked.

#### "No module named 'flask'" (or other module)
- **Solution**: Virtual environment not activated or packages not installed.
  ```bash
  # Activate venv first
  venv\Scripts\activate  # Windows
  source venv/bin/activate  # Linux/Mac
  
  # Then install
  pip install -r requirements.txt
  ```

#### "Camera initialization failed"
- **Solution 1**: Grant camera permissions in OS settings
- **Solution 2**: Try different camera device ID in config.yaml:
  ```yaml
  camera:
    device_id: 1  # Try 1, 2, 3, etc.
  ```
- **Solution 3**: Use demo mode (no camera required)

#### "CUDA out of memory"
- **Solution**: Reduce batch size or use CPU mode:
  ```yaml
  detection:
    device: "cpu"
  ```

#### YOLOv8 model download fails
- **Solution**: Download manually:
  ```bash
  wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
  # Place in project root
  ```

#### Port 5000 already in use
- **Solution**: Change port in config.yaml:
  ```yaml
  api:
    port: 5001  # Or any available port
  ```

#### Slow performance
- **Solutions**:
  1. Enable GPU acceleration (see GPU section)
  2. Reduce FPS in config.yaml:
     ```yaml
     camera:
       fps: 15  # Lower FPS
     ```
  3. Use lower resolution:
     ```yaml
     camera:
       resolution: [640, 480]  # Lower resolution
     ```

---

## Directory Structure After Installation

```
Inventory-Management-Tracking-System/
├── venv/                    # Virtual environment (created)
├── data/
│   └── shelf.db            # SQLite database (auto-created)
├── yolov8n.pt             # YOLOv8 model (auto-downloaded)
├── __pycache__/           # Python cache (auto-created)
└── [rest of project files]
```

---

## Next Steps

After successful installation:

1. **Configure your setup** - See [CONFIGURATION.md](CONFIGURATION.md)
2. **Understand the architecture** - See [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Explore the API** - See [API_REFERENCE.md](API_REFERENCE.md)
4. **Run demo mode** - See [../DEMO_GUIDE.md](../DEMO_GUIDE.md)
5. **Start development** - See [DEVELOPMENT.md](DEVELOPMENT.md)

---

## Uninstallation

To completely remove Inventory-Management-Tracking-System:

```bash
# Deactivate virtual environment
deactivate

# Remove project folder
rm -rf Inventory-Management-Tracking-System  # Linux/Mac
# or
Remove-Item -Recurse -Force Inventory-Management-Tracking-System  # Windows PowerShell
```

---

## Support

If you encounter issues not covered here, please:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Search existing [GitHub Issues](../../issues)
3. Create a new issue with:
   - Your OS and Python version
   - Full error message
   - Steps to reproduce
