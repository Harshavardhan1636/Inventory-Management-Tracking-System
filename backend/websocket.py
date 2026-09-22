"""
WebSocket Handlers for Inventory-Management-Tracking-System.

Handles real-time video streaming and live updates.
"""

from flask_socketio import SocketIO, emit
import cv2
import base64
import threading
import time
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Reference to components
_components: Dict = {}

# Streaming state (protected by _state_lock)
_streaming = False
_stream_thread: Optional[threading.Thread] = None
_stream_mode: Optional[str] = None
_state_lock = threading.RLock()


def _get_runtime_controls() -> Dict:
    """Get runtime controls shared with main processing loop."""
    runtime = _components.get('runtime')
    if runtime is None:
        runtime = {
            'pipeline_enabled': True,
            'vision_lock': threading.Lock()
        }
        _components['runtime'] = runtime

    if runtime.get('vision_lock') is None:
        runtime['vision_lock'] = threading.Lock()

    runtime.setdefault('uploaded_media', {})
    runtime.setdefault('latest_media_id', None)
    runtime.setdefault('stream_mode', None)

    return runtime


def set_components(components: Dict) -> None:
    """Set references to core system components."""
    global _components
    _components = components


def register_websocket_handlers(socketio: SocketIO) -> None:
    """
    Register WebSocket event handlers.
    
    Args:
        socketio: Flask-SocketIO instance
    """
    
    def _start_stream_thread_if_needed() -> None:
        """Ensure there is exactly one active background frame streamer."""
        global _streaming, _stream_thread

        with _state_lock:
            if _streaming and _stream_thread and _stream_thread.is_alive():
                return

            _streaming = True
            _stream_thread = threading.Thread(
                target=stream_video,
                args=(socketio,),
                daemon=True
            )
            _stream_thread.start()

    def _stop_stream_thread() -> None:
        """Stop and join active background stream thread if present."""
        global _streaming, _stream_thread

        with _state_lock:
            _streaming = False
            if _stream_thread and _stream_thread.is_alive():
                _stream_thread.join(timeout=2.0)
            _stream_thread = None

    def _stop_pipeline(vision, runtime: Dict, log_source: str) -> None:
        """Stop pipeline execution and stream loop."""
        global _stream_mode

        runtime['pipeline_enabled'] = False
        runtime['stream_mode'] = None
        vision_lock = runtime['vision_lock']

        if vision and vision.is_running():
            try:
                with vision_lock:
                    if vision.is_running():
                        vision.stop()
                        logger.info(f"Vision pipeline stopped via {log_source}")
            except Exception as exc:
                logger.error(f"Error stopping vision pipeline via {log_source}: {exc}")

        _stop_stream_thread()
        _stream_mode = None

    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        logger.info("Client connected")
        emit('connected', {'status': 'connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logger.info("Client disconnected")

    @socketio.on('start_stream')
    def handle_start_stream():
        """Start camera-based video stream to client."""
        global _stream_mode

        vision = _components.get('vision')
        runtime = _get_runtime_controls()

        if not vision:
            emit('stream_status', {'status': 'error', 'message': 'Vision component not available'})
            return

        with _state_lock:
            if _streaming and _stream_mode == 'attachment':
                _stop_pipeline(vision, runtime, 'start_stream mode switch')
                logger.info("Switched stream mode from attachment to camera")

        runtime['pipeline_enabled'] = True
        runtime['stream_mode'] = 'camera'
        vision_lock = runtime['vision_lock']

        try:
            with vision_lock:
                if hasattr(vision, 'set_camera_input'):
                    vision.set_camera_input()

                if not vision.is_running() and runtime.get('pipeline_enabled', True):
                    if not vision.start():
                        runtime['pipeline_enabled'] = False
                        runtime['stream_mode'] = None
                        emit('stream_status', {'status': 'error', 'message': 'Failed to start camera pipeline'})
                        logger.error("Failed to start camera pipeline from start_stream")
                        return
        except Exception as exc:
            runtime['pipeline_enabled'] = False
            runtime['stream_mode'] = None
            logger.error(f"Error starting camera pipeline: {exc}")
            emit('stream_status', {'status': 'error', 'message': 'Failed to start camera pipeline'})
            return

        with _state_lock:
            if _streaming and _stream_mode == 'camera':
                emit('stream_status', {'status': 'already_running', 'mode': 'camera'})
                return

            _stream_mode = 'camera'
            _start_stream_thread_if_needed()

        emit('stream_status', {'status': 'started', 'mode': 'camera'})
        logger.info("Video stream started in camera mode")

    @socketio.on('stop_stream')
    def handle_stop_stream():
        """Stop camera-based stream session."""
        global _stream_mode

        vision = _components.get('vision')
        runtime = _get_runtime_controls()

        # Be permissive: stop request should terminate any active stream mode.
        with _state_lock:
            current_mode = _stream_mode

        if current_mode == 'attachment' and vision and hasattr(vision, 'clear_attachment_input'):
            try:
                with runtime['vision_lock']:
                    vision.clear_attachment_input()
            except Exception as exc:
                logger.error(f"Error clearing attachment input during stop_stream: {exc}")

        _stop_pipeline(vision, runtime, 'stop_stream')
        emit('stream_status', {'status': 'stopped', 'mode': 'camera'})
        logger.info("Stream stopped via stop_stream")

    @socketio.on('start_attachment_stream')
    def handle_start_attachment_stream(data=None):
        """Start attachment-based stream session using uploaded image/video media."""
        global _stream_mode

        payload = data or {}
        vision = _components.get('vision')
        runtime = _get_runtime_controls()

        if not vision:
            emit('stream_status', {'status': 'error', 'message': 'Vision component not available'})
            return

        with _state_lock:
            if _streaming and _stream_mode == 'camera':
                _stop_pipeline(vision, runtime, 'start_attachment_stream mode switch')
                logger.info("Switched stream mode from camera to attachment")

        media_store = runtime.get('uploaded_media', {})
        media_id = str(payload.get('media_id', '')).strip() or str(runtime.get('latest_media_id') or '').strip()
        loop = bool(payload.get('loop', True))

        if not media_id or media_id not in media_store:
            emit('stream_status', {'status': 'error', 'mode': 'attachment', 'message': 'Upload an image or video first.'})
            return

        media_entry = media_store.get(media_id) or {}
        media_path = str(media_entry.get('path', '')).strip()
        media_name = media_entry.get('original_name') or media_entry.get('stored_name') or 'media'

        if not media_path:
            emit('stream_status', {'status': 'error', 'mode': 'attachment', 'message': 'Uploaded media path is invalid.'})
            return

        runtime['pipeline_enabled'] = True
        runtime['stream_mode'] = 'attachment'
        vision_lock = runtime['vision_lock']

        try:
            with vision_lock:
                if not hasattr(vision, 'configure_attachment_input'):
                    emit('stream_status', {'status': 'error', 'mode': 'attachment', 'message': 'Attachment mode is not supported by vision pipeline.'})
                    return

                if not vision.configure_attachment_input(media_path, loop=loop):
                    runtime['pipeline_enabled'] = False
                    runtime['stream_mode'] = None
                    emit('stream_status', {'status': 'error', 'mode': 'attachment', 'message': 'Failed to configure attachment media.'})
                    return

                if not vision.is_running() and runtime.get('pipeline_enabled', True):
                    if not vision.start():
                        runtime['pipeline_enabled'] = False
                        runtime['stream_mode'] = None
                        emit('stream_status', {'status': 'error', 'mode': 'attachment', 'message': 'Failed to start attachment pipeline.'})
                        return
        except Exception as exc:
            runtime['pipeline_enabled'] = False
            runtime['stream_mode'] = None
            logger.error(f"Error starting attachment pipeline: {exc}")
            emit('stream_status', {'status': 'error', 'mode': 'attachment', 'message': 'Failed to start attachment pipeline.'})
            return

        with _state_lock:
            if _streaming and _stream_mode == 'attachment':
                emit('stream_status', {'status': 'already_running', 'mode': 'attachment', 'media_name': media_name})
                return

            _stream_mode = 'attachment'
            _start_stream_thread_if_needed()

        emit(
            'stream_status',
            {
                'status': 'started',
                'mode': 'attachment',
                'media_name': media_name,
                'loop': loop
            }
        )
        logger.info(f"Video stream started in attachment mode: {media_name}")

    @socketio.on('stop_attachment_stream')
    def handle_stop_attachment_stream():
        """Stop attachment-based stream session."""
        vision = _components.get('vision')
        runtime = _get_runtime_controls()

        with _state_lock:
            current_mode = _stream_mode

        if current_mode == 'camera':
            emit(
                'stream_status',
                {
                    'status': 'warning',
                    'mode': 'attachment',
                    'message': 'Camera session is active. Use Stop Stream for camera mode.'
                }
            )
            return

        _stop_pipeline(vision, runtime, 'stop_attachment_stream')

        if vision and hasattr(vision, 'clear_attachment_input'):
            try:
                with runtime['vision_lock']:
                    vision.clear_attachment_input()
            except Exception as exc:
                logger.error(f"Error clearing attachment input after stop: {exc}")

        emit('stream_status', {'status': 'stopped', 'mode': 'attachment'})
        logger.info("Attachment stream stopped")

    @socketio.on('get_status')
    def handle_get_status():
        """Get current system status."""
        vision = _components.get('vision')
        runtime = _get_runtime_controls()
        camera_status = vision.get_camera_status() if vision else {}

        with _state_lock:
            current_streaming = _streaming
            current_stream_mode = _stream_mode

        status = {
            'vision_running': vision.is_running() if vision else False,
            'streaming': current_streaming,
            'stream_mode': current_stream_mode,
            'fps': vision.get_fps() if vision else 0,
            'pipeline_enabled': runtime.get('pipeline_enabled', True),
            'camera': camera_status
        }

        emit('status', status)

    @socketio.on('request_frame')
    def handle_request_frame():
        """Get single frame on request."""
        vision = _components.get('vision')

        if not vision or not vision.is_running():
            emit('frame_error', {'error': 'Vision not running'})
            return

        try:
            frame = vision.get_annotated_frame()
            if frame is not None:
                frame_data = encode_frame(frame)
                emit('frame', {'image': frame_data})
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            emit('frame_error', {'error': str(e)})
    
    logger.info("WebSocket handlers registered")


def stream_video(socketio: SocketIO) -> None:
    """
    Stream video frames to connected clients.

    Args:
        socketio: Flask-SocketIO instance
    """
    global _streaming

    vision = _components.get('vision')

    if not vision:
        logger.error("Vision component not available for streaming")
        with _state_lock:
            _streaming = False
        socketio.emit('stream_status', {'status': 'error', 'message': 'Vision not available'})
        return

    # Auto-start vision if not running
    if not vision.is_running():
        logger.warning("Vision not running, attempting to start...")
        try:
            success = vision.start()
            if success:
                logger.info("Vision started successfully for streaming")
                time.sleep(1)  # Give it time to warm up
            else:
                logger.error("Failed to start vision for streaming")
                with _state_lock:
                    _streaming = False
                socketio.emit('stream_status', {'status': 'error', 'message': 'Failed to start vision'})
                return
        except Exception as e:
            logger.error(f"Error starting vision: {e}")
            with _state_lock:
                _streaming = False
            return

    logger.info("Starting video stream loop...")
    frame_delay = 1.0 / 25  # Target 25 FPS for smoother streaming
    frames_sent = 0
    last_signal_warning_time = 0.0

    while True:
        with _state_lock:
            if not _streaming:
                break
        try:
            if not vision.is_running():
                logger.warning("Vision stopped, waiting...")
                time.sleep(0.5)
                continue

            # Get annotated frame
            frame = vision.get_annotated_frame()

            if frame is not None:
                # Encode and emit
                try:
                    frame_data = encode_frame(frame, quality=70)
                    socketio.emit('frame', {'image': frame_data})

                    camera_status = vision.get_camera_status()
                    input_mode = camera_status.get('input_mode', 'camera')
                    if input_mode == 'attachment':
                        pass
                    elif camera_status.get('using_demo_fallback', False):
                        now = time.time()
                        if now - last_signal_warning_time >= 5.0:
                            socketio.emit(
                                'stream_status',
                                {
                                    'status': 'warning',
                                    'message': 'Camera signal unavailable; streaming demo fallback frames.'
                                }
                            )
                            last_signal_warning_time = now
                    elif not camera_status.get('has_signal', True):
                        now = time.time()
                        if now - last_signal_warning_time >= 5.0:
                            socketio.emit(
                                'stream_status',
                                {
                                    'status': 'warning',
                                    'message': 'Camera is running but no visible signal is detected. Check shutter/privacy settings.'
                                }
                            )
                            last_signal_warning_time = now
                except Exception as e:
                    logger.error(f"Error encoding/emitting frame: {e}")
            else:
                pass # Silent on empty frames to avoid log spam

            time.sleep(frame_delay)

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            time.sleep(0.5)

    logger.info("Video stream ended")


def encode_frame(frame, quality: int = 80) -> str:
    """
    Encode frame as base64 JPEG.
    
    Args:
        frame: OpenCV frame (BGR)
        quality: JPEG quality (0-100)
        
    Returns:
        Base64 encoded JPEG string
    """
    # Resize for streaming (reduce bandwidth)
    height, width = frame.shape[:2]
    if width > 800:
        scale = 800 / width
        frame = cv2.resize(frame, None, fx=scale, fy=scale)
    
    # Encode as JPEG
    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
    _, buffer = cv2.imencode('.jpg', frame, encode_params)
    
    # Convert to base64
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return f"data:image/jpeg;base64,{frame_base64}"


def emit_event_update(socketio: SocketIO, event_data: Dict) -> None:
    """
    Emit real-time event update to clients.
    
    Args:
        socketio: Flask-SocketIO instance
        event_data: Event dictionary
    """
    socketio.emit('event', event_data)


def emit_inventory_update(socketio: SocketIO, inventory_data: Dict) -> None:
    """
    Emit real-time inventory update to clients.
    
    Args:
        socketio: Flask-SocketIO instance
        inventory_data: Inventory dictionary
    """
    socketio.emit('inventory_update', inventory_data)


def emit_alert(socketio: SocketIO, alert_data: Dict) -> None:
    """
    Emit real-time alert to clients.
    
    Args:
        socketio: Flask-SocketIO instance
        alert_data: Alert dictionary
    """
    socketio.emit('alert', alert_data)


def stop_streaming() -> None:
    """Stop the video stream."""
    global _streaming, _stream_mode
    with _state_lock:
        _streaming = False
        _stream_mode = None
