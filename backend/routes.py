"""
REST API Routes for Inventory-Management-Tracking-System.

Defines all REST API endpoints.
"""

from flask import Blueprint, Flask, jsonify, request, render_template
from typing import Dict, Any
from pathlib import Path
from uuid import uuid4
import logging
import time
from collections import defaultdict
from threading import Lock
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# API Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Reference to core components (set by orchestrator)
_components: Dict = {}

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_MEDIA_UPLOAD_DIR = _PROJECT_ROOT / 'data' / 'attachments'
_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.wmv', '.mpg', '.mpeg'}
_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
_ALLOWED_MEDIA_EXTENSIONS = _VIDEO_EXTENSIONS | _IMAGE_EXTENSIONS
_MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB max file size

# Rate limiting state
_rate_limit_lock = Lock()
_rate_limit_storage: Dict[str, list] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX_REQUESTS = 100  # max requests per window per IP


def set_components(components: Dict) -> None:
    """Set references to core system components."""
    global _components
    _components = components
    logger.info("API components configured")


def _check_rate_limit(ip: str) -> tuple[bool, int]:
    """
    Check if IP is within rate limits.

    Returns:
        (allowed, retry_after_seconds)
    """
    now = time.time()
    cutoff = now - _RATE_LIMIT_WINDOW

    with _rate_limit_lock:
        # Clean old entries
        _rate_limit_storage[ip] = [t for t in _rate_limit_storage[ip] if t > cutoff]

        # Check limit
        if len(_rate_limit_storage[ip]) >= _RATE_LIMIT_MAX_REQUESTS:
            oldest = min(_rate_limit_storage[ip])
            retry_after = int(oldest + _RATE_LIMIT_WINDOW - now) + 1
            return False, max(1, retry_after)

        # Record this request
        _rate_limit_storage[ip].append(now)
        return True, 0


@api.before_request
def _rate_limit_before_request():
    """Apply rate limiting before each API request."""
    if request.blueprint != 'api':
        return

    ip = request.remote_addr or '127.0.0.1'
    allowed, retry_after = _check_rate_limit(ip)

    if not allowed:
        response = jsonify({
            'error': 'Rate limit exceeded',
            'retry_after': retry_after
        })
        response.headers['Retry-After'] = str(retry_after)
        return response, 429


# ===== HELPER FUNCTIONS =====

def get_component(name: str):
    """Get a component by name."""
    return _components.get(name)


def _get_runtime_controls() -> Dict[str, Any]:
    """Get mutable runtime controls shared across API and WebSocket layers."""
    runtime = _components.get('runtime')
    if runtime is None:
        runtime = {}
        _components['runtime'] = runtime

    runtime.setdefault('pipeline_enabled', True)
    runtime.setdefault('uploaded_media', {})
    runtime.setdefault('latest_media_id', None)
    return runtime


def _resolve_media_upload_dir() -> Path:
    """Resolve media upload directory from config, falling back to data/attachments."""
    config = get_component('config') or {}
    media_config = config.get('media', {}) if isinstance(config, dict) else {}
    configured_dir = media_config.get('upload_dir')

    if configured_dir:
        candidate = Path(str(configured_dir))
        if not candidate.is_absolute():
            candidate = _PROJECT_ROOT / candidate
        return candidate.resolve()

    return _DEFAULT_MEDIA_UPLOAD_DIR


# ===== PAGE ROUTES =====

def register_page_routes(app: Flask) -> None:
    """Register HTML page routes."""
    
    @app.route('/')
    def index():
        """Live dashboard page."""
        return render_template('index.html')
    
    @app.route('/inventory')
    def inventory_page():
        """Inventory management page."""
        return render_template('inventory.html')
    
    @app.route('/events')
    def events_page():
        """Event timeline page."""
        return render_template('events.html')
    
    @app.route('/alerts')
    def alerts_page():
        """Alerts page."""
        return render_template('alerts.html')


# ===== API ROUTES =====

@api.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON with status and system info
    """
    vision = get_component('vision')
    
    return jsonify({
        'status': 'healthy',
        'vision_running': vision.is_running() if vision else False,
        'camera': vision.get_camera_status() if vision else {},
        'version': '1.0.0'
    }), 200


@api.route('/media/upload', methods=['POST'])
def upload_media_attachment():
    """Upload a media file (image/video) for attachment-based detection sessions."""
    upload = request.files.get('media')
    if upload is None:
        return jsonify({'error': 'media file is required'}), 400

    original_name = secure_filename(upload.filename or '')
    if not original_name:
        return jsonify({'error': 'Invalid filename'}), 400

    suffix = Path(original_name).suffix.lower()
    if suffix not in _ALLOWED_MEDIA_EXTENSIONS:
        return jsonify({'error': 'Unsupported media type. Use image or video files only.'}), 400

    # Check file size before saving
    upload.seek(0, 2)  # Seek to end
    file_size = upload.tell()
    upload.seek(0)  # Reset to beginning

    if file_size > _MAX_FILE_SIZE_BYTES:
        return jsonify({'error': f'File too large. Maximum size is {_MAX_FILE_SIZE_BYTES // (1024*1024)} MB'}), 413

    upload_dir = _resolve_media_upload_dir()
    upload_dir.mkdir(parents=True, exist_ok=True)

    media_id = uuid4().hex
    stored_name = f"{media_id}{suffix}"
    stored_path = upload_dir / stored_name
    upload.save(str(stored_path))

    runtime = _get_runtime_controls()
    media_type = 'video' if suffix in _VIDEO_EXTENSIONS else 'image'
    media_entry = {
        'id': media_id,
        'original_name': original_name,
        'stored_name': stored_name,
        'path': str(stored_path),
        'type': media_type,
        'size_bytes': stored_path.stat().st_size
    }

    runtime['uploaded_media'][media_id] = media_entry
    runtime['latest_media_id'] = media_id

    return jsonify({
        'success': True,
        'media': media_entry
    }), 201


@api.route('/media/current', methods=['GET'])
def get_current_media_attachment():
    """Get metadata for the most recently uploaded media attachment."""
    runtime = _get_runtime_controls()
    latest_id = runtime.get('latest_media_id')
    media_store = runtime.get('uploaded_media', {})

    if not latest_id or latest_id not in media_store:
        return jsonify({'media': None}), 200

    media = media_store.get(latest_id)
    if not media:
        return jsonify({'media': None}), 200

    media_path = Path(media.get('path', ''))
    if not media_path.exists():
        media_store.pop(latest_id, None)
        runtime['latest_media_id'] = None
        return jsonify({'media': None}), 200

    return jsonify({'media': media}), 200


@api.route('/inventory', methods=['GET'])
def get_inventory():
    """
    Get current inventory.
    
    Returns:
        JSON with all inventory items
    """
    db = get_component('database')
    
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        inventory = db.get_inventory()
        return jsonify({
            'inventory': inventory,
            'total_items': len(inventory),
            'total_units': sum(inventory.values())
        }), 200
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/inventory/<item_class>', methods=['GET'])
def get_inventory_item(item_class: str):
    """
    Get single inventory item.
    
    Args:
        item_class: Item class name
        
    Returns:
        JSON with item details
    """
    db = get_component('database')
    
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        item = db.get_inventory_item(item_class)
        if item:
            return jsonify(item), 200
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        logger.error(f"Error getting item: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/inventory/add', methods=['POST'])
def add_inventory_item():
    """
    Add a new inventory item.
    
    Request Body:
        {
            "item_class": str,    # Item name/class
            "quantity": int,      # Initial quantity
            "reason": str         # Reason for adding (optional)
        }
    """
    db = get_component('database')
    
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json(silent=True) or {}
        item_class = data.get('item_class', '').strip()
        quantity = data.get('quantity', 0)
        reason = data.get('reason', 'Initial stock')
        
        if not item_class:
            return jsonify({'error': 'Item class name is required'}), 400
        
        if quantity <= 0:
            return jsonify({'error': 'Quantity must be greater than 0'}), 400
        
        # Check if item already exists
        existing = db.get_inventory_item(item_class)
        if existing:
            return jsonify({'error': 'Item already exists. Use update instead.'}), 400
        
        # Add the item (update with initial quantity)
        success = db.update_inventory(item_class, quantity)
        
        if success:
            # Log the action
            db.log_action({
                'action_type': 'add_item',
                'item_class': item_class,
                'quantity_change': quantity,
                'reason': reason
            })
            
            return jsonify({
                'success': True,
                'item_class': item_class,
                'quantity': quantity
            }), 201
        
        return jsonify({'error': 'Failed to add inventory item'}), 400
        
    except Exception as e:
        logger.error(f"Error adding inventory item: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/inventory/<item_class>/update', methods=['POST'])
def update_inventory_item(item_class: str):
    """
    Update inventory item quantity.
    
    Args:
        item_class: Item class name
        
    Request Body:
        {
            "quantity_change": int,  # positive to add, negative to remove
            "reason": str (optional)
        }
    """
    db = get_component('database')
    
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        data = request.get_json(silent=True) or {}
        quantity_change_raw = data.get('quantity_change', None)
        reason = data.get('reason', 'Manual update')

        if quantity_change_raw is None:
            return jsonify({'error': 'quantity_change is required'}), 400

        try:
            quantity_change = int(quantity_change_raw)
        except (TypeError, ValueError):
            return jsonify({'error': 'quantity_change must be an integer'}), 400

        # Validate quantity bounds (prevent abuse)
        max_quantity_change = 1000
        if abs(quantity_change) > max_quantity_change:
            return jsonify({'error': f'quantity_change magnitude cannot exceed {max_quantity_change}'}), 400

        if quantity_change == 0:
            return jsonify({'error': 'quantity_change must be non-zero'}), 400

        existing = db.get_inventory_item(item_class)
        if not existing:
            return jsonify({'error': 'Item not found'}), 404
        
        success = db.update_inventory(item_class, quantity_change)
        
        if success:
            # Log the action
            db.log_action({
                'action_type': 'manual_update',
                'item_class': item_class,
                'quantity_change': quantity_change,
                'reason': reason
            })
            
            # Get updated quantity
            item = db.get_inventory_item(item_class)
            return jsonify({
                'success': True,
                'item': item
            }), 200
        
        return jsonify({'error': 'Failed to update inventory'}), 400
        
    except Exception as e:
        logger.error(f"Error updating inventory: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/shelf-state', methods=['GET'])
@api.route('/shelf/state', methods=['GET'])
def get_shelf_state():
    """
    Get current shelf state.
    
    Returns:
        JSON with all slot states
    """
    reasoning = get_component('reasoning')
    
    if not reasoning:
        return jsonify({'error': 'Reasoning engine not available'}), 500
    
    try:
        state = reasoning.get_current_state()
        return jsonify({
            'state': state,
            'slot_count': len(state)
        }), 200
    except Exception as e:
        logger.error(f"Error getting shelf state: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/shelf/assignment', methods=['POST'])
def set_shelf_assignment():
    """Assign or clear expected item for a slot at runtime."""
    reasoning = get_component('reasoning')
    vision = get_component('vision')

    if not reasoning:
        return jsonify({'error': 'Reasoning engine not available'}), 500

    try:
        data = request.get_json(silent=True) or {}
        slot_id = str(data.get('slot_id', '')).strip()
        expected_item_raw = data.get('expected_item')

        if not slot_id:
            return jsonify({'error': 'slot_id is required'}), 400

        expected_item = None
        if expected_item_raw is not None:
            expected_item = str(expected_item_raw).strip().lower()
            if not expected_item:
                expected_item = None

        updated = reasoning.set_expected_item(slot_id, expected_item)
        if not updated:
            return jsonify({'error': 'Invalid slot_id'}), 404

        if vision:
            vision.set_expected_item(slot_id, expected_item, persist=True)

        state = reasoning.get_current_state().get(slot_id, {})
        return jsonify({
            'success': True,
            'slot_id': slot_id,
            'expected_item': state.get('expected_item'),
            'slot_state': state
        }), 200
    except Exception as e:
        logger.error(f"Error updating shelf assignment: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/events', methods=['GET'])
def get_events():
    """
    Get recent events.
    
    Query params:
        limit: Maximum events to return (default: 50)
    """
    db = get_component('database')
    
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        limit = request.args.get('limit', 50, type=int)
        events = db.get_recent_events(limit)
        return jsonify({
            'events': events,
            'count': len(events)
        }), 200
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/actions', methods=['GET'])
def get_actions():
    """
    Get recent inventory actions.
    
    Query params:
        limit: Maximum actions to return (default: 50)
    """
    db = get_component('database')
    
    if not db:
        return jsonify({'error': 'Database not available'}), 500
    
    try:
        limit = request.args.get('limit', 50, type=int)
        actions = db.get_recent_actions(limit)
        return jsonify({
            'actions': actions,
            'count': len(actions)
        }), 200
    except Exception as e:
        logger.error(f"Error getting actions: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Get active alerts.
    """
    alert_system = get_component('alerts')
    
    if not alert_system:
        return jsonify({'error': 'Alert system not available'}), 500
    
    try:
        active = alert_system.get_active_alerts()
        counts = alert_system.get_alert_counts()
        return jsonify({
            'alerts': [a.to_dict() for a in active],
            'counts': counts
        }), 200
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/alerts/<alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: str):
    """
    Acknowledge an alert.
    
    Args:
        alert_id: Alert ID to acknowledge
    """
    alert_system = get_component('alerts')
    db = get_component('database')
    
    if not alert_system:
        return jsonify({'error': 'Alert system not available'}), 500
    
    try:
        success = alert_system.acknowledge_alert(alert_id)
        
        if success and db:
            db.acknowledge_alert_db(alert_id)
        
        if success:
            return jsonify({'success': True}), 200
        return jsonify({'error': 'Alert not found'}), 404
        
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/alerts/acknowledge-all', methods=['POST'])
def acknowledge_all_alerts():
    """
    Acknowledge all active alerts.
    """
    alert_system = get_component('alerts')
    
    if not alert_system:
        return jsonify({'error': 'Alert system not available'}), 500
    
    try:
        active_alerts = alert_system.get_active_alerts()
        count = 0
        
        for alert in active_alerts:
            if alert_system.acknowledge_alert(alert.alert_id):
                count += 1
        
        return jsonify({
            'success': True,
            'acknowledged_count': count
        }), 200
        
    except Exception as e:
        logger.error(f"Error acknowledging all alerts: {e}")
        return jsonify({'error': str(e)}), 500


@api.route('/config', methods=['GET'])
def get_config():
    """
    Get current system configuration (safe subset).
    """
    config = get_component('config')
    
    if not config:
        return jsonify({'error': 'Config not available'}), 500
    
    # Return only safe parts of config
    safe_config = {
        'system': config.get('system', {}),
        'shelf': config.get('shelf', {}),
        'reasoning': config.get('reasoning', {})
    }
    
    return jsonify(safe_config), 200


@api.route('/reset', methods=['POST'])
def reset_system():
    """
    Reset system state (for demo/testing).
    """
    reasoning = get_component('reasoning')
    
    if not reasoning:
        return jsonify({'error': 'Reasoning engine not available'}), 500
    
    try:
        reasoning.reset_all()
        return jsonify({
            'success': True,
            'message': 'System state reset'
        }), 200
    except Exception as e:
        logger.error(f"Error resetting system: {e}")
        return jsonify({'error': str(e)}), 500


# ===== REGISTRATION =====

def register_routes(app: Flask) -> None:
    """Register all routes with the Flask app."""
    # Register API blueprint
    app.register_blueprint(api)

    # Register page routes
    register_page_routes(app)

    logger.info("Routes registered")
