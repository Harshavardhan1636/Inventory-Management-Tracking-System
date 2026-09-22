"""
Inventory-Management-Tracking-System
Main Entry Point

This is the entry point for the complete system.
Run with: python main.py
"""

import sys
import signal
import time
import threading
import logging
import argparse
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import components
from utils.config_loader import load_config
from utils.logger import setup_logging
from vision import VisionPipeline
from reasoning import ReasoningEngine
from inventory import DecisionEngine, InventoryManager, AlertSystem
from database import DatabaseManager
from backend.app import create_app, get_socketio
from backend.routes import set_components
from backend.websocket import set_components as set_ws_components

# Global state
running = True
components = {}


def _load_environment_files() -> None:
    """Load .env/.evn key-value pairs into process environment."""
    env_paths = [PROJECT_ROOT / '.env', PROJECT_ROOT / '.evn']

    for env_path in env_paths:
        if not env_path.exists() or not env_path.is_file():
            continue

        try:
            with open(env_path, 'r', encoding='utf-8') as env_file:
                for raw_line in env_file:
                    line = raw_line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue

                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    if not key:
                        continue

                    os.environ.setdefault(key, value)

            logging.getLogger(__name__).info(f"Loaded environment file: {env_path.name}")
        except Exception as exc:
            logging.getLogger(__name__).warning(
                f"Unable to load environment file {env_path.name}: {exc}"
            )


def _seed_inventory_if_needed(db_manager, config, logger) -> None:
    """Seed inventory data when configured and the database is empty."""
    if not db_manager or not isinstance(config, dict):
        return

    inventory_config = config.get('inventory', {})
    if not isinstance(inventory_config, dict):
        return

    seed_on_startup = bool(inventory_config.get('seed_on_startup', False))
    seed_items = inventory_config.get('seed_items', {})
    if not seed_on_startup or not isinstance(seed_items, dict) or not seed_items:
        return

    seed_mode = str(inventory_config.get('seed_mode', 'merge')).strip().lower()
    if seed_mode not in {'merge', 'replace', 'skip'}:
        seed_mode = 'merge'

    current_inventory = db_manager.get_inventory()
    if current_inventory and seed_mode == 'skip':
        logger.info("Inventory seed skipped (seed_mode=skip)")
        return

    seeded_count = 0
    for item_class, quantity in seed_items.items():
        try:
            quantity_value = int(quantity)
        except (TypeError, ValueError):
            logger.warning(f"Skipping seed item with invalid quantity: {item_class}")
            continue

        if quantity_value < 0:
            logger.warning(f"Skipping seed item with negative quantity: {item_class}")
            continue

        item_key = str(item_class)
        if current_inventory and seed_mode == 'merge':
            if item_key in current_inventory:
                continue
            success = db_manager.update_inventory(item_key, quantity_value)
        else:
            success = db_manager.set_inventory(item_key, quantity_value)

        if success:
            seeded_count += 1

    logger.info(f"Seeded inventory with {seeded_count} item(s) using seed_mode={seed_mode}")


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    print("\nShutting down Inventory-Management-Tracking-System...")
    running = False


def _parse_args(argv=None):
    """Parse CLI arguments for runtime configuration."""
    parser = argparse.ArgumentParser(description="Inventory-Management-Tracking-System runtime")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to YAML configuration file"
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Main entry point."""
    global running, components
    args = _parse_args(argv)

    # Load optional environment files before component initialization.
    _load_environment_files()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("  Inventory-Management-Tracking-System")
    print("  Vision-based Inventory Tracking System")
    print("=" * 60)
    print()
    
    # Load configuration
    print("[1/7] Loading configuration...")
    try:
        config = load_config(args.config)
        print("      ✓ Configuration loaded")
    except Exception as e:
        print(f"      ✗ Configuration error: {e}")
        return 1
    
    # Setup logging
    print("[2/7] Setting up logging...")
    setup_logging(
        level=logging.DEBUG if config.get('system', {}).get('debug') else logging.INFO
    )
    logger = logging.getLogger(__name__)
    print("      ✓ Logging initialized")
    
    # Initialize database
    print("[3/7] Initializing database...")
    try:
        db_manager = DatabaseManager(config.get('database', {}).get('path', 'data/shelf.db'))
        components['database'] = db_manager
        print("      ✓ Database initialized")
    except Exception as e:
        print(f"      ✗ Database error: {e}")
        return 1
    
    # Seed inventory for demo/first-run scenarios
    _seed_inventory_if_needed(db_manager, config, logger)

    # Initialize vision pipeline
    print("[4/7] Initializing vision pipeline...")
    try:
        vision = VisionPipeline(config)
        components['vision'] = vision
        print("      ✓ Vision pipeline ready")
    except Exception as e:
        print(f"      ✗ Vision error: {e}")
        logger.warning(f"Vision initialization failed: {e}")
        # Continue without vision for demo mode
        vision = None
    
    # Initialize reasoning engine
    print("[5/7] Initializing reasoning engine...")
    try:
        slot_ids = vision.get_slot_ids() if vision else [f"SLOT_{r}_{c}" for r in range(2) for c in range(3)]
        expected_items = vision.get_expected_items() if vision else {}
        
        reasoning = ReasoningEngine(
            slot_ids=slot_ids,
            expected_items=expected_items,
            config=config.get('reasoning', {})
        )
        components['reasoning'] = reasoning
        print("      ✓ Reasoning engine initialized")
    except Exception as e:
        print(f"      ✗ Reasoning error: {e}")
        return 1
    
    # Initialize inventory and alerts
    print("[6/7] Initializing inventory system...")
    try:
        # Get initial inventory from database
        initial_inventory = db_manager.get_inventory()
        
        inventory_manager = InventoryManager(
            initial_inventory=initial_inventory,
            low_stock_threshold=config.get('inventory', {}).get('low_stock_threshold', 2)
        )
        components['inventory'] = inventory_manager
        
        decision_engine = DecisionEngine(config.get('inventory', {}))
        components['decision'] = decision_engine
        
        alert_system = AlertSystem()
        components['alerts'] = alert_system
        
        print("      ✓ Inventory system ready")
    except Exception as e:
        print(f"      ✗ Inventory error: {e}")
        return 1
    
    # Initialize Flask app
    print("[7/7] Starting web server...")
    try:
        components['config'] = config
        components['runtime'] = {
            'pipeline_enabled': True,
            'vision_lock': threading.Lock(),
            'stream_mode': None,
            'uploaded_media': {},
            'latest_media_id': None
        }
        
        # Set component references for API routes
        set_components(components)
        set_ws_components(components)
        
        app = create_app(config)
        socketio = get_socketio()
        
        api_config = config.get('api', {})
        host = api_config.get('host', '127.0.0.1')
        port = api_config.get('port', 5000)
        
        print("      ✓ Web server ready")
        print()
        print("=" * 60)
        print(f"  Inventory-Management-Tracking-System is running!")
        print(f"  Dashboard: http://{host}:{port}")
        print("  Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        # Start vision processing in background. The loop handles camera start/retry,
        # which keeps server startup responsive even when camera probing is slow.
        if vision:
            logger.info("Vision pipeline startup delegated to processing loop")

            # Start processing loop in background
            process_thread = threading.Thread(
                target=processing_loop,
                args=(vision, reasoning, decision_engine, inventory_manager, 
                      alert_system, db_manager, socketio),
                daemon=True
            )
            process_thread.start()
        
        # Run Flask with SocketIO
        socketio.run(
            app,
            host=host,
            port=port,
            debug=False,  # Disable debug for threaded mode
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        print(f"      ✗ Server error: {e}")
        logger.exception("Server error")
        return 1
    
    # Cleanup
    cleanup(components)
    
    return 0


def _persist_and_emit_alert(alert, db_manager, socketio) -> None:
    """Persist alert to the database and emit over WebSocket if available."""
    if alert is None:
        return

    if db_manager:
        db_manager.save_alert(alert.to_dict())

    if socketio:
        socketio.emit('alert', alert.to_dict())


def _evaluate_shelf_stock_alerts(
    reasoning,
    inventory_manager,
    alert_system,
    db_manager,
    socketio,
    config
) -> None:
    """Create shelf-level low stock alerts using fused YOLO + Gemini counts."""
    if not reasoning or not inventory_manager or not alert_system:
        return

    config = config if isinstance(config, dict) else {}
    inventory_config = config.get('inventory', {}) if isinstance(config, dict) else {}
    reasoning_config = config.get('reasoning', {}) if isinstance(config, dict) else {}

    shelf_threshold = int(inventory_config.get('shelf_low_stock_threshold', 1))
    if shelf_threshold <= 0:
        return

    count_confidence = float(
        inventory_config.get(
            'shelf_count_confidence_threshold',
            reasoning_config.get('confidence_threshold', 0.7)
        )
    )
    inventory_low_threshold = int(inventory_config.get('low_stock_threshold', 2))
    alert_cooldown_seconds = float(inventory_config.get('alert_cooldown_seconds', 60))

    counts = reasoning.get_shelf_item_counts(confidence_threshold=count_confidence)
    expected_counts = counts.get('expected_counts', {})
    observed_counts = counts.get('observed_expected_counts', {})

    for item_class, expected_total in expected_counts.items():
        if expected_total <= 0:
            continue

        observed = int(observed_counts.get(item_class, 0))
        min_required = min(shelf_threshold, expected_total)

        if observed >= min_required:
            continue

        inventory_qty = inventory_manager.get_quantity(item_class)
        shelf_title = f"Shelf Low: {item_class}"
        shelf_key = f"shelf_low:{item_class}"

        if inventory_qty > inventory_low_threshold:
            shelf_message = (
                f"Shelf count is {observed}/{expected_total}. "
                f"Inventory has {inventory_qty} units. Refill shelf from inventory."
            )
            alert = alert_system.create_warning_once(
                key=shelf_key,
                title=shelf_title,
                message=shelf_message,
                cooldown_seconds=alert_cooldown_seconds,
                item_class=item_class
            )
            _persist_and_emit_alert(alert, db_manager, socketio)
            continue

        shelf_message = (
            f"Shelf count is {observed}/{expected_total}. "
            f"Inventory is low ({inventory_qty} units). Refill inventory."
        )
        alert = alert_system.create_warning_once(
            key=shelf_key,
            title=shelf_title,
            message=shelf_message,
            cooldown_seconds=alert_cooldown_seconds,
            item_class=item_class
        )
        _persist_and_emit_alert(alert, db_manager, socketio)

        inventory_title = f"Inventory Low: {item_class}"
        inventory_key = f"inventory_low:{item_class}"
        inventory_message = (
            f"Inventory has {inventory_qty} units. "
            "Refill inventory to keep shelves stocked."
        )
        inventory_alert = alert_system.create_critical_once(
            key=inventory_key,
            title=inventory_title,
            message=inventory_message,
            cooldown_seconds=alert_cooldown_seconds,
            item_class=item_class
        )
        _persist_and_emit_alert(inventory_alert, db_manager, socketio)


def processing_loop(vision, reasoning, decision_engine, inventory_manager, 
                   alert_system, db_manager, socketio):
    """
    Main processing loop.
    
    Runs in background thread, continuously:
    1. Gets detections from vision
    2. Passes to reasoning engine
    3. Processes events through decision engine
    4. Updates inventory
    5. Generates alerts
    6. Broadcasts updates via WebSocket
    """
    global running
    logger = logging.getLogger(__name__)
    camera_config = vision.config.get('camera', {}) if vision else {}
    retry_interval = float(camera_config.get('reconnect_retry_interval_seconds', 10))
    last_restart_attempt = 0.0
    runtime = components.get('runtime', {})
    if runtime.get('vision_lock') is None:
        runtime['vision_lock'] = threading.Lock()
    
    logger.info("Processing loop started")
    
    while running:
        try:
            pipeline_enabled = runtime.get('pipeline_enabled', True)

            if not pipeline_enabled:
                if vision.is_running():
                    with runtime['vision_lock']:
                        if vision.is_running():
                            vision.stop()
                            logger.info("Vision pipeline paused by stream control")
                time.sleep(0.5)
                continue

            # Skip if vision not running
            if not vision.is_running():
                now = time.time()
                if now - last_restart_attempt >= retry_interval:
                    last_restart_attempt = now
                    with runtime['vision_lock']:
                        if runtime.get('pipeline_enabled', True) and not vision.is_running():
                            if vision.start():
                                logger.info("Vision pipeline restart succeeded")
                            else:
                                logger.warning("Vision pipeline restart attempt failed")
                time.sleep(0.5)
                continue
            
            # Get detections
            detection_data = vision.get_detections()
            detections = detection_data.get('detections', [])
            gemini_slot_hints = detection_data.get('gemini_slot_hints', {})
            
            # Process through reasoning engine
            events = reasoning.process_detections(
                detections,
                gemini_slot_hints=gemini_slot_hints,
            )
            
            # Process events through decision engine
            if events:
                current_inventory = db_manager.get_inventory()
                actions = decision_engine.process_events(events, current_inventory)
                
                # Execute actions
                for action in actions:
                    if action.action_type == 'increment':
                        db_manager.update_inventory(action.item_class, action.quantity_change)
                        inventory_manager.increment(action.item_class)
                        
                    elif action.action_type == 'decrement':
                        success = db_manager.update_inventory(action.item_class, action.quantity_change)
                        if success:
                            inventory_manager.decrement(action.item_class)
                        
                        # Check for low stock alert
                        qty = inventory_manager.get_quantity(action.item_class)
                        inventory_config = components.get('config', {}).get('inventory', {})
                        low_stock_threshold = int(inventory_config.get('low_stock_threshold', 2))
                        alert_cooldown_seconds = float(
                            inventory_config.get('alert_cooldown_seconds', 60)
                        )
                        if qty <= low_stock_threshold:
                            alert = alert_system.create_warning_once(
                                key=f"inventory_low:{action.item_class}",
                                title=f"Low Stock: {action.item_class}",
                                message=f"Only {qty} units remaining",
                                cooldown_seconds=alert_cooldown_seconds,
                                item_class=action.item_class
                            )
                            _persist_and_emit_alert(alert, db_manager, socketio)
                            
                    elif action.action_type == 'flag':
                        alert = alert_system.create_info(
                            f"Review Required",
                            action.reason,
                            slot_id=action.slot_id
                        )
                        _persist_and_emit_alert(alert, db_manager, socketio)
                    
                    # Log action
                    db_manager.log_action(action.to_dict())
                
                # Log events
                for event in events:
                    db_manager.log_event(event.to_dict())
                
                # Broadcast updates via WebSocket
                for event in events:
                    socketio.emit('event', event.to_dict())

            # Evaluate shelf-level stock counts (fused YOLO + Gemini) for alerts
            _evaluate_shelf_stock_alerts(
                reasoning,
                inventory_manager,
                alert_system,
                db_manager,
                socketio,
                components.get('config', {})
            )
            
            # Small delay to control processing rate
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            time.sleep(0.5)
    
    logger.info("Processing loop stopped")


def cleanup(components):
    """Cleanup resources on shutdown."""
    logger = logging.getLogger(__name__)
    
    logger.info("Cleaning up...")
    
    # Stop vision
    vision = components.get('vision')
    if vision:
        if hasattr(vision, 'shutdown'):
            vision.shutdown()
        else:
            vision.stop()
    
    print("\nInventory-Management-Tracking-System stopped. Goodbye!")


if __name__ == "__main__":
    sys.exit(main())
