# Troubleshooting Guide

Common issues and solutions for Inventory-Management-Tracking-System.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Camera Issues](#camera-issues)
- [Detection Issues](#detection-issues)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)
- [Network/API Issues](#network-api-issues)
- [Error Messages](#error-messages)

---

## Installation Issues

### Python not found

**Symptoms:**
```
'python' is not recognized as an internal or external command
```

**Solutions:**
1. **Reinstall Python** with "Add to PATH" option checked
2. **Use full path:**
   ```bash
   C:\Python38\python.exe -m venv venv
   ```
3. **On Windows**, try `py` instead of `python`:
   ```bash
   py -m venv venv
   ```

---

### pip install fails

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
1. **Upgrade pip:**
   ```bash
   python -m pip install --upgrade pip
   ```

2. **Check Python version:**
   ```bash
   python --version  # Must be 3.8+
   ```

3. **Install with verbose output:**
   ```bash
   pip install -r requirements.txt -v
   ```

4. **Try without cache:**
   ```bash
   pip install -r requirements.txt --no-cache-dir
   ```

---

### Virtual environment activation fails

**Symptoms:**
```
Cannot be loaded because running scripts is disabled on this system
```

**Solutions (Windows PowerShell):**
```powershell
# Run as Administrator
Set-ExecutionPolicy RemoteSigned

# Then activate
venv\Scripts\activate
```

**Alternative:**
```powershell
# Use .ps1 file
venv\Scripts\Activate.ps1
```

---

### CUDA/PyTorch installation fails

**Symptoms:**
```
RuntimeError: CUDA out of memory
```
or
```
torch not compiled with CUDA support
```

**Solutions:**
1. **Check CUDA availability:**
   ```python
   import torch
   print(torch.cuda.is_available())
   ```

2. **Reinstall with correct CUDA version:**
   ```bash
   # For CUDA 11.8
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   
   # For CUDA 12.1
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
   ```

3. **Use CPU mode:**
   ```yaml
   # config.yaml
   detection:
     device: "cpu"
   ```

---

## Camera Issues

### Camera not detected

**Symptoms:**
```
ERROR: Failed to initialize camera on device 0
```

**Solutions:**
1. **Try different device IDs:**
   ```yaml
   # config.yaml
   camera:
     device_id: 1  # Try 1, 2, 3
   ```

2. **Check camera permissions:**
   - **Windows**: Settings → Privacy → Camera → Allow apps
   - **macOS**: System Preferences → Security & Privacy → Camera
   - **Linux**: Check `/dev/video*` permissions

3. **Close other applications** using the camera

4. **List available cameras (Windows):**
   ```python
   import cv2
   for i in range(10):
       cap = cv2.VideoCapture(i)
       if cap.isOpened():
           print(f"Camera {i} available")
           cap.release()
   ```

5. **Use demo mode as fallback:**
   ```bash
   python scripts/run_demo.py
   ```

---

### Camera shows black screen

**Symptoms:**
- Dashboard loads but video is black/blank
- No errors in console

**Solutions:**
1. **Increase warmup frames:**
   ```yaml
   camera:
     warmup_frames: 30  # Increase from 12
   ```

2. **Try different backend:**
   ```yaml
   camera:
     backend: "auto"  # Instead of "dshow"
   ```

3. **Check auto-exposure:**
   ```yaml
   camera:
     auto_exposure: 1.0  # Increase from 0.75
   ```

4. **Verify camera works externally:**
   ```python
   import cv2
   cap = cv2.VideoCapture(0)
   ret, frame = cap.read()
   cv2.imshow("Test", frame)
   cv2.waitKey(0)
   ```

---

### "No signal detected" error

**Symptoms:**
```
WARNING: Camera signal lost, switching to demo mode
```

**Solutions:**
1. **Disable strict validation:**
   ```yaml
   camera:
     strict_signal_validation: false
   ```

2. **Adjust threshold:**
   ```yaml
   camera:
     no_signal_mean_threshold: 5.0  # Lower from 8.0
   ```

3. **Check camera cable** connection

4. **Restart camera** (unplug/replug)

---

### Low FPS / Laggy video

**Symptoms:**
- Video stutters
- FPS counter shows <10 FPS

**Solutions:**
1. **Reduce resolution:**
   ```yaml
   camera:
     resolution: [640, 480]  # Lower from [1280, 720]
   ```

2. **Reduce target FPS:**
   ```yaml
   camera:
     fps: 15  # Lower from 30
   ```

3. **Use MJPG codec:**
   ```yaml
   camera:
     fourcc: "MJPG"
   ```

4. **Enable GPU:**
   ```yaml
   detection:
     device: "cuda:0"
   ```

5. **Close other applications** using CPU/GPU

---

## Detection Issues

### No detections

**Symptoms:**
- Video feed works but no bounding boxes appear
- Events log shows no activity

**Solutions:**
1. **Lower confidence threshold:**
   ```yaml
   detection:
     confidence_threshold: 0.3  # Lower from 0.5
   ```

2. **Verify objects are in COCO dataset:**
   - YOLOv8 detects 80 classes (person, bottle, cup, etc.)
   - See [COCO classes](https://docs.ultralytics.com/datasets/detect/coco/)

3. **Check model file:**
   ```bash
   ls -lh yolov8n.pt  # Should be ~6MB
   ```

4. **Test detection manually:**
   ```python
   from ultralytics import YOLO
   model = YOLO("yolov8n.pt")
   results = model("test_image.jpg")
   results[0].show()
   ```

---

### Too many false positives

**Symptoms:**
- Detections on empty slots
- Random object classifications

**Solutions:**
1. **Increase confidence threshold:**
   ```yaml
   detection:
     confidence_threshold: 0.7  # Increase from 0.5
   ```

2. **Increase reasoning thresholds:**
   ```yaml
   reasoning:
     addition_threshold: 5  # Increase from 3
     confidence_threshold: 0.8  # Increase from 0.7
   ```

3. **Enable better lighting** in camera view

4. **Clean camera lens**

---

### Wrong object classifications

**Symptoms:**
- Bottle detected as cup
- Cup detected as bottle

**Solutions:**
1. **Increase confidence threshold:**
   ```yaml
   detection:
     confidence_threshold: 0.7
   ```

2. **Use larger model:**
   ```yaml
   detection:
     model: "yolov8s.pt"  # Instead of yolov8n.pt
   ```

3. **Improve object positioning:**
   - Place objects clearly in slots
   - Avoid overlapping
   - Ensure good lighting

4. **Train custom model** for your specific items

---

### Detections disappear intermittently

**Symptoms:**
- Objects flicker in and out
- Unstable bounding boxes

**Solutions:**
1. **This is expected behavior!** Temporal reasoning handles this.

2. **Verify reasoning is working:**
   ```yaml
   reasoning:
     short_absence_threshold: 2  # Ignores 1-2 frame gaps
     temporal_window: 10  # Buffers 10 frames
   ```

3. **Check events log** - should only see sustained changes

4. **Improve lighting** to reduce flickering

---

## Performance Issues

### High CPU usage

**Symptoms:**
- 100% CPU usage
- System slowdown

**Solutions:**
1. **Enable GPU:**
   ```yaml
   detection:
     device: "cuda:0"
   ```

2. **Reduce FPS:**
   ```yaml
   camera:
     fps: 10
   ```

3. **Use lower resolution:**
   ```yaml
   camera:
     resolution: [640, 480]
   ```

4. **Close other applications**

---

### High memory usage

**Symptoms:**
- RAM usage grows over time
- System becomes slow

**Solutions:**
1. **Reduce buffer sizes:**
   ```yaml
   camera:
     buffer_size: 1  # Reduce from 2
   reasoning:
     temporal_window: 6  # Reduce from 10
   ```

2. **Restart application periodically**

3. **Check for memory leaks:**
   ```bash
   pip install memory_profiler
   python -m memory_profiler main.py
   ```

---

### Slow API responses

**Symptoms:**
- Dashboard takes long to load
- API calls timeout

**Solutions:**
1. **Enable database indexing** (already done by default)

2. **Limit event history:**
   ```python
   # In routes.py
   @app.route('/api/events')
   def get_events():
       limit = request.args.get('limit', 100)  # Add limit
   ```

3. **Use WebSocket** instead of polling

4. **Check database size:**
   ```bash
   ls -lh data/shelf.db
   ```

---

## Database Issues

### "Database locked" error

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**
1. **Close other connections:**
   - Only run one instance of Inventory-Management-Tracking-System
   - Close DB browsers (DB Browser for SQLite, etc.)

2. **Increase timeout:**
   ```python
   # database/db_manager.py
   engine = create_engine(
       f'sqlite:///{db_path}',
       connect_args={'timeout': 30}  # Increase from default
   )
   ```

3. **Use Write-Ahead Logging (WAL):**
   ```python
   # database/db_manager.py
   engine.execute("PRAGMA journal_mode=WAL")
   ```

---

### Database corruption

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions:**
1. **Backup current database:**
   ```bash
   cp data/shelf.db data/shelf.db.backup
   ```

2. **Try recovery:**
   ```bash
   sqlite3 data/shelf.db ".dump" | sqlite3 data/shelf_recovered.db
   ```

3. **Delete and recreate:**
   ```bash
   rm data/shelf.db
   python main.py  # Will create fresh database
   ```

---

### Large database file

**Symptoms:**
- `shelf.db` grows to multiple GB

**Solutions:**
1. **Vacuum database:**
   ```bash
   sqlite3 data/shelf.db "VACUUM;"
   ```

2. **Archive old events:**
   ```sql
   DELETE FROM events_log WHERE timestamp < date('now', '-30 days');
   DELETE FROM inventory_actions WHERE timestamp < date('now', '-30 days');
   VACUUM;
   ```

3. **Implement automatic cleanup:**
   ```python
   # Add to main.py
   def cleanup_old_events():
       db.execute("DELETE FROM events_log WHERE timestamp < date('now', '-7 days')")
   ```

---

## Network/API Issues

### Cannot access dashboard

**Symptoms:**
- Browser shows "Unable to connect"
- `http://127.0.0.1:5000` doesn't load

**Solutions:**
1. **Check if server is running:**
   ```
   Look for: "Running on http://127.0.0.1:5000" in console
   ```

2. **Check firewall:**
   - Allow Python through Windows Firewall
   - Temporarily disable to test

3. **Try different browser**

4. **Check port availability:**
   ```bash
   # Windows
   netstat -ano | findstr :5000
   
   # Linux/Mac
   lsof -i :5000
   ```

5. **Change port:**
   ```yaml
   api:
     port: 5001  # Use different port
   ```

---

### WebSocket connection fails

**Symptoms:**
```
WebSocket connection failed
```

**Solutions:**
1. **Check SocketIO version compatibility:**
   ```bash
   pip install flask-socketio==5.3.4 python-socketio==5.9.0
   ```

2. **Check CORS settings:**
   ```python
   # backend/app.py
   CORS(app, resources={r"/*": {"origins": "*"}})
   ```

3. **Use polling fallback:**
   ```javascript
   const socket = io({
       transports: ['websocket', 'polling']
   });
   ```

---

### CORS errors

**Symptoms:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solutions:**
1. **Update CORS settings:**
   ```python
   # backend/app.py
   CORS(app, resources={
       r"/api/*": {"origins": "*"}
   })
   ```

2. **Access from same origin:**
   ```
   Use http://127.0.0.1:5000, not http://localhost:5000
   ```

---

## Error Messages

### ImportError: No module named 'cv2'

**Solution:**
```bash
pip install opencv-python
```

---

### ImportError: No module named 'ultralytics'

**Solution:**
```bash
pip install ultralytics
```

---

### ValueError: Negative inventory not allowed

**Cause:** Trying to decrement inventory below zero

**Solution:**
1. **Manual reset:**
   ```bash
   curl -X POST http://127.0.0.1:5000/api/inventory/bottle \
     -H "Content-Type: application/json" \
     -d '{"quantity": 10}'
   ```

2. **Adjust reasoning threshold** to reduce false removals

---

### RuntimeError: CUDA out of memory

**Solutions:**
1. **Use CPU mode:**
   ```yaml
   detection:
     device: "cpu"
   ```

2. **Use smaller model:**
   ```yaml
   detection:
     model: "yolov8n.pt"  # Smallest
   ```

3. **Reduce resolution:**
   ```yaml
   camera:
     resolution: [640, 480]
   ```

---

### FileNotFoundError: yolov8n.pt

**Solution:**
```bash
# Download manually
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

# Or let YOLO download automatically (first run)
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

---

### Port already in use

**Symptoms:**
```
OSError: [Errno 98] Address already in use
```

**Solutions:**
1. **Find and kill process:**
   ```bash
   # Linux/Mac
   lsof -ti:5000 | xargs kill -9
   
   # Windows
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

2. **Use different port:**
   ```yaml
   api:
     port: 5001
   ```

---

## General Debugging Steps

### 1. Check Logs

```bash
# Enable debug logging
python main.py --debug

# Look for ERROR or WARNING messages
```

### 2. Test Components Individually

```python
# Test camera
import cv2
cap = cv2.VideoCapture(0)
print(cap.isOpened())

# Test YOLO
from ultralytics import YOLO
model = YOLO("yolov8n.pt")
print("Model loaded")

# Test database
from database.db_manager import DatabaseManager
db = DatabaseManager("test.db")
print("DB connected")
```

### 3. Check Versions

```bash
python --version
pip list | grep -E "flask|torch|opencv|ultralytics"
```

### 4. Fresh Installation

```bash
# Remove and recreate venv
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Check Configuration

```yaml
# Verify config.yaml syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

---

## Getting Help

If your issue isn't covered here:

1. **Check logs** with `--debug` flag
2. **Search [GitHub Issues](../../issues)**
3. **Create new issue** with:
   - Operating system and version
   - Python version (`python --version`)
   - Full error message
   - Steps to reproduce
   - Configuration file (sanitized)

---

## Known Limitations

- **Single camera** per instance (no multi-camera support)
- **SQLite** write performance (~1MB/sec)
- **WebSocket** limited to 100-500 concurrent clients
- **YOLOv8** only detects 80 COCO classes (without custom training)
- **Windows Defender** may flag Python scripts (false positive)

---

## Performance Optimization Checklist

- [ ] GPU acceleration enabled
- [ ] Appropriate model size (nano for CPU, small/medium for GPU)
- [ ] Resolution ≤ 1280x720
- [ ] FPS ≤ 30
- [ ] Temporal window ≤ 10
- [ ] Database vacuumed regularly
- [ ] Old events archived/deleted
- [ ] Firewall configured
- [ ] Latest package versions

---

## Next Steps

- **[Installation Guide](INSTALLATION.md)** - Complete setup instructions
- **[Configuration Guide](CONFIGURATION.md)** - Tune performance settings
- **[Development Guide](DEVELOPMENT.md)** - Debug and extend
- **[Architecture](ARCHITECTURE.md)** - Understand system design
