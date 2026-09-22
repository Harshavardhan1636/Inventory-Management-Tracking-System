# Development Guide

Guide for developers who want to contribute to or extend Inventory-Management-Tracking-System.

## Table of Contents
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Code Style](#code-style)
- [Testing](#testing)
- [Adding New Features](#adding-new-features)
- [Debugging](#debugging)
- [Contributing](#contributing)

---

## Development Setup

### Prerequisites
- Python 3.8+
- Git
- Virtual environment tool
- Code editor (VS Code, PyCharm recommended)

### Initial Setup

1. **Clone repository:**
```bash
git clone <repository-url>
cd Inventory-Management-Tracking-System
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
# Install main dependencies
pip install -r requirements.txt

# Install development dependencies
pip install black pytest pytest-cov flake8 mypy
```

4. **Install pre-commit hooks (optional):**
```bash
pip install pre-commit
pre-commit install
```

### Development Dependencies

```txt
# requirements-dev.txt
black==23.10.1        # Code formatter
pytest==7.4.3         # Testing framework
pytest-cov==4.1.0     # Coverage reporting
flake8==6.1.0         # Linting
mypy==1.6.1           # Type checking
ipython==8.17.2       # Enhanced REPL
```

---

## Project Structure

```
Inventory-Management-Tracking-System/
├── vision/                 # Computer vision layer
│   ├── __init__.py
│   ├── pipeline.py        # Main orchestrator
│   ├── camera.py          # Camera capture
│   ├── detector.py        # YOLOv8 wrapper
│   └── slot_mapper.py     # Grid mapping
│
├── reasoning/             # Temporal reasoning layer
│   ├── __init__.py
│   ├── reasoning_engine.py
│   ├── temporal_buffer.py
│   ├── shelf_state.py
│   └── event_generator.py
│
├── inventory/             # Inventory management
│   ├── __init__.py
│   ├── decision_engine.py
│   ├── inventory_manager.py
│   └── alert_system.py
│
├── database/              # Persistence layer
│   ├── __init__.py
│   ├── models.py
│   └── db_manager.py
│
├── backend/               # Web API
│   ├── __init__.py
│   ├── app.py
│   ├── routes.py
│   └── websocket.py
│
├── frontend/              # User interface
│   ├── templates/
│   └── static/
│
├── config/                # Configuration
│   └── shelf_layouts/
│
├── scripts/               # Utility scripts
├── tests/                 # Unit tests
├── utils/                 # Utilities
├── main.py               # Entry point
└── requirements.txt      # Dependencies
```

### Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `vision` | Frame capture, object detection, slot mapping |
| `reasoning` | Temporal analysis, event generation |
| `inventory` | Business logic, inventory management |
| `database` | Data persistence, ORM models |
| `backend` | HTTP API, WebSocket handlers |
| `frontend` | UI templates, static assets |
| `utils` | Logging, config loading, helpers |

---

## Code Style

### Python Style Guide

Inventory-Management-Tracking-System follows **PEP 8** with some modifications:

- **Line length**: 100 characters (not 79)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Grouped and sorted

### Formatting with Black

```bash
# Format all Python files
black .

# Check formatting without changes
black --check .

# Format specific file
black vision/pipeline.py
```

### Black Configuration

**pyproject.toml:**
```toml
[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | venv
  | build
  | dist
)/
'''
```

### Import Organization

```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import cv2
import numpy as np
from flask import Flask, jsonify

# Local application imports
from vision.pipeline import VisionPipeline
from database.db_manager import DatabaseManager
```

### Naming Conventions

```python
# Classes: PascalCase
class VisionPipeline:
    pass

# Functions/methods: snake_case
def process_detections():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_BUFFER_SIZE = 10

# Private methods: _leading_underscore
def _internal_helper():
    pass

# Variables: snake_case
detection_count = 0
```

### Docstrings

Use Google-style docstrings:

```python
def detect_objects(frame, confidence_threshold=0.5):
    """Detect objects in a frame using YOLOv8.
    
    Args:
        frame (np.ndarray): Input image frame
        confidence_threshold (float): Minimum confidence (0.0-1.0)
        
    Returns:
        list: List of detection dictionaries with keys:
            - class: str - Object class name
            - confidence: float - Detection confidence
            - bbox: tuple - Bounding box (x1, y1, x2, y2)
            - centroid: tuple - Center point (x, y)
            
    Raises:
        ValueError: If frame is None or invalid
        
    Example:
        >>> detections = detect_objects(frame, 0.6)
        >>> print(len(detections))
        5
    """
    pass
```

### Type Hints

Use type hints for function signatures:

```python
from typing import List, Dict, Optional, Tuple

def process_frame(
    frame: np.ndarray,
    slot_config: Dict[str, any]
) -> Tuple[List[Dict], np.ndarray]:
    """Process frame and return detections."""
    pass
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_reasoning.py

# Run with coverage
pytest --cov=. tests/

# Run with verbose output
pytest -v tests/

# Run specific test function
pytest tests/test_reasoning.py::test_slot_state_creation
```

### Writing Tests

**Example Test File:**
```python
# tests/test_reasoning.py
import pytest
from reasoning.shelf_state import SlotState

class TestSlotState:
    """Test SlotState class."""
    
    def test_creation(self):
        """Test slot state creation."""
        state = SlotState("SLOT_0_0", "bottle", "bottle", 0.9, "STABLE")
        assert state.slot_id == "SLOT_0_0"
        assert state.expected_item == "bottle"
        assert state.current_item == "bottle"
        assert state.confidence == 0.9
        
    def test_is_occupied(self):
        """Test occupancy detection."""
        state = SlotState("SLOT_0_0", "bottle", "bottle", 0.9)
        assert state.is_occupied() is True
        
        empty_state = SlotState("SLOT_0_1", "cup", None, 0.8)
        assert empty_state.is_occupied() is False
        
    def test_is_misplaced(self):
        """Test misplacement detection."""
        # Correct item
        state = SlotState("SLOT_0_0", "bottle", "bottle", 0.9)
        assert state.is_misplaced() is False
        
        # Wrong item
        misplaced = SlotState("SLOT_0_0", "bottle", "cup", 0.8)
        assert misplaced.is_misplaced() is True
        
        # Empty slot (not misplaced)
        empty = SlotState("SLOT_0_0", "bottle", None, 0.8)
        assert empty.is_misplaced() is False
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_reasoning.py        # Reasoning tests
├── test_database.py         # Database tests
├── test_alert_system.py     # Alert tests
├── test_vision.py           # Vision tests (future)
└── test_api.py              # API tests (future)
```

### Fixtures

**conftest.py:**
```python
import pytest
from database.db_manager import DatabaseManager

@pytest.fixture
def db():
    """Create test database."""
    db = DatabaseManager(":memory:")  # In-memory SQLite
    yield db
    db.close()
    
@pytest.fixture
def sample_detection():
    """Sample detection data."""
    return {
        "class": "bottle",
        "confidence": 0.85,
        "bbox": (100, 100, 200, 200),
        "centroid": (150, 150)
    }
```

### Coverage Goals

- **Core modules**: 80%+ coverage
- **Utilities**: 70%+ coverage
- **API routes**: 60%+ coverage

---

## Adding New Features

### Adding a New Event Type

1. **Define event in `reasoning/event_generator.py`:**
```python
class EventType:
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    ITEM_RESTOCKED = "item_restocked"  # NEW
```

2. **Add reasoning rule in `ReasoningEngine`:**
```python
def _detect_restock(self, slot_id, history):
    """Detect restocking event."""
    # Detect large quantity increase
    pass
```

3. **Map to action in `DecisionEngine`:**
```python
EVENT_ACTION_MAP = {
    "item_restocked": "alert_manager",  # NEW
}
```

4. **Add WebSocket handler:**
```python
# backend/websocket.py
@socketio.on('restock_event')
def handle_restock(data):
    # Handle restock notification
    pass
```

5. **Update frontend:**
```javascript
// static/js/events.js
socket.on('restock_event', function(data) {
    showRestockNotification(data);
});
```

### Adding a New Detection Class

**Option 1: Use existing COCO classes (80 classes available)**
```python
# Just update shelf layout
# config/shelf_layouts/retail_3x2.json
"expected_items": {
    "SLOT_0_0": "laptop",  # COCO class
    "SLOT_0_1": "keyboard"  # COCO class
}
```

**Option 2: Train custom YOLOv8 model**
```bash
# Train custom model
yolo task=detect mode=train model=yolov8n.pt data=custom_data.yaml epochs=100

# Use in config
detection:
  model: "runs/detect/train/weights/best.pt"
```

### Adding a New API Endpoint

1. **Define route in `backend/routes.py`:**
```python
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get inventory statistics."""
    stats = {
        "total_items": inventory_manager.get_total_count(),
        "low_stock_count": inventory_manager.get_low_stock_count(),
        "total_value": calculate_total_value()
    }
    return jsonify(stats), 200
```

2. **Add to API documentation**

3. **Write tests:**
```python
def test_statistics_endpoint(client):
    response = client.get('/api/statistics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_items' in data
```

### Adding a New Configuration Option

1. **Add to config schema (`config.yaml`):**
```yaml
inventory:
  enable_notifications: true  # NEW
  notification_email: "admin@example.com"  # NEW
```

2. **Update config loader validation:**
```python
# utils/config_loader.py
def validate_config(config):
    # Validate new fields
    if 'enable_notifications' in config.get('inventory', {}):
        assert isinstance(config['inventory']['enable_notifications'], bool)
```

3. **Use in code:**
```python
if self.config['inventory'].get('enable_notifications', False):
    send_email_notification()
```

---

## Debugging

### Logging

Inventory-Management-Tracking-System uses Python's `logging` module:

```python
import logging

logger = logging.getLogger(__name__)

# Log levels
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")
```

### Enable Debug Logging

**config.yaml:**
```yaml
system:
  debug: true  # Enable debug logging
```

**Or via command line:**
```bash
python main.py --debug
```

### Debug Specific Modules

```python
# main.py
import logging

logging.getLogger('vision').setLevel(logging.DEBUG)
logging.getLogger('reasoning').setLevel(logging.INFO)
```

### Visual Debugging

**Enable OpenCV windows:**
```python
# vision/pipeline.py
if debug_mode:
    cv2.imshow("Debug Frame", annotated_frame)
    cv2.waitKey(1)
```

### IPython Debugging

```python
# Insert breakpoint
import IPython; IPython.embed()

# Inspect variables
detections
frame.shape
```

### Remote Debugging (VS Code)

**launch.json:**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Inventory-Management-Tracking-System",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": false
        }
    ]
}
```

---

## Contributing

### Contribution Workflow

1. **Fork repository**
2. **Create feature branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Make changes and commit:**
   ```bash
   git add .
   git commit -m "Add my new feature"
   ```

4. **Run tests:**
   ```bash
   pytest tests/
   black --check .
   ```

5. **Push to fork:**
   ```bash
   git push origin feature/my-new-feature
   ```

6. **Create Pull Request**

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Tests
- `chore`: Maintenance

**Example:**
```
feat(reasoning): add restock detection

- Detect large quantity increases
- Generate restock events
- Add tests for restock logic

Closes #123
```

### Pull Request Checklist

- [ ] Code follows style guide (Black formatted)
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] All tests pass
- [ ] No linting errors
- [ ] Commit messages are clear

### Code Review Guidelines

**For Reviewers:**
- Check code quality and style
- Verify tests are adequate
- Look for edge cases
- Suggest improvements
- Be constructive and respectful

**For Contributors:**
- Respond to feedback promptly
- Make requested changes
- Explain design decisions
- Be open to suggestions

---

## Development Tools

### Recommended VS Code Extensions

- Python (Microsoft)
- Pylance
- Black Formatter
- GitLens
- Better Comments

### VS Code Settings

**settings.json:**
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true
}
```

### Makefile (Optional)

```makefile
.PHONY: test format lint clean

test:
	pytest tests/

format:
	black .

lint:
	flake8 .
	mypy .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
```

---

## Performance Profiling

### CPU Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code
vision_pipeline.get_detections()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)
```

### Memory Profiling

```bash
pip install memory_profiler

# Add @profile decorator
python -m memory_profiler main.py
```

---

## Release Process

1. **Update version** in `config.yaml`
2. **Update CHANGELOG.md**
3. **Run full test suite**
4. **Create git tag:**
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```
5. **Create GitHub release**
6. **Update documentation**

---

## Next Steps

- **[Architecture](ARCHITECTURE.md)** - Understand system design
- **[Testing](../tests/)** - Review existing tests
- **[API Reference](API_REFERENCE.md)** - API details
- **[Configuration](CONFIGURATION.md)** - Config options
