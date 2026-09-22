"""
Camera Capture Module for Inventory-Management-Tracking-System.

Provides threaded webcam capture with buffering and error handling.
"""

import cv2
import threading
import queue
import time
import sys
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CameraStream:
    """
    Threaded camera capture with buffering and error handling.
    
    This class manages webcam access in a separate thread to prevent
    blocking the main processing loop. Includes automatic reconnection
    and frame buffering.
    
    Attributes:
        device_id: Camera device index
        fps: Target frames per second
        resolution: (width, height) tuple
        buffer_size: Maximum frames to buffer
    """
    
    def __init__(
        self,
        device_id: int = 0,
        device_candidates: Optional[List[int]] = None,
        fps: int = 30,
        resolution: Tuple[int, int] = (1280, 720),
        buffer_size: int = 2,
        backend: str = "auto",
        fourcc: Optional[str] = "MJPG",
        warmup_frames: int = 8,
        auto_exposure: Optional[float] = 0.75,
        exposure: Optional[float] = None,
        gain: Optional[float] = None,
        brightness: Optional[float] = None,
        strict_signal_validation: bool = False,
        no_signal_mean_threshold: float = 2.0,
        no_signal_std_threshold: float = 1.0,
        no_signal_confirm_frames: int = 5,
        signal_recovery_confirm_frames: int = 5
    ):
        """
        Initialize camera stream.
        
        Args:
            device_id: Camera device index (0 for built-in webcam)
            fps: Target frames per second
            resolution: (width, height) tuple
            buffer_size: Maximum frames to buffer
        """
        self.device_id = device_id
        if device_candidates:
            candidates = [int(d) for d in device_candidates]
        else:
            candidates = [int(device_id)]

        # Keep order, remove duplicates, and guarantee the configured device_id is tried.
        ordered_unique: List[int] = []
        for candidate in candidates + [int(device_id)]:
            if candidate not in ordered_unique:
                ordered_unique.append(candidate)
        self.device_candidates = ordered_unique
        self.fps = fps
        self.resolution = resolution
        self.buffer_size = buffer_size
        self.backend = backend
        self.fourcc = fourcc
        self.warmup_frames = max(1, warmup_frames)
        self.auto_exposure = auto_exposure
        self.exposure = exposure
        self.gain = gain
        self.brightness = brightness
        self.strict_signal_validation = strict_signal_validation
        self.no_signal_mean_threshold = float(no_signal_mean_threshold)
        self.no_signal_std_threshold = float(no_signal_std_threshold)
        self.no_signal_confirm_frames = max(1, int(no_signal_confirm_frames))
        self.signal_recovery_confirm_frames = max(1, int(signal_recovery_confirm_frames))
        self._active_backend = cv2.CAP_ANY
        self._active_device_id = int(device_id)
        
        # Thread control
        self._capture: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._frame_queue: queue.Queue = queue.Queue(maxsize=buffer_size)
        self._running = False
        self._lock = threading.Lock()
        
        # Statistics
        self._frame_count = 0
        self._fps_actual = 0.0
        self._last_fps_time = time.time()
        self._invalid_frame_streak = 0
        self._no_signal = False
        self._no_signal_streak = 0
        self._signal_recovery_streak = 0
        self._last_valid_frame_time = 0.0
        self._last_frame_mean = 0.0
        self._last_frame_std = 0.0
        self._signal_stale_timeout = max(
            2.0,
            self.no_signal_confirm_frames / max(float(self.fps), 1.0)
        )
        
        logger.info(f"CameraStream initialized: device={device_id}, "
                   f"resolution={resolution}, fps={fps}, backend={backend}, "
               f"device_candidates={self.device_candidates}, "
                   f"signal_thresholds=(mean<{self.no_signal_mean_threshold}, "
                   f"std<{self.no_signal_std_threshold}), "
                   f"confirm_frames={self.no_signal_confirm_frames}/{self.signal_recovery_confirm_frames}")

    def _get_backend_candidates(self) -> List[int]:
        """Resolve backend preference into ordered OpenCV backends."""
        pref = (self.backend or "auto").strip().lower()

        if sys.platform != 'win32':
            return [cv2.CAP_ANY]

        mapping = {
            'dshow': cv2.CAP_DSHOW,
            'msmf': cv2.CAP_MSMF,
            'any': cv2.CAP_ANY
        }

        if pref in mapping:
            return [mapping[pref]]

        # Auto mode tries the two common Windows backends before generic fallback.
        return [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]

    def _backend_name(self, backend: int) -> str:
        """Return human-readable backend name for logs."""
        names = {
            cv2.CAP_DSHOW: 'DSHOW',
            cv2.CAP_MSMF: 'MSMF',
            cv2.CAP_ANY: 'ANY'
        }
        return names.get(backend, str(backend))

    def _apply_capture_settings(self, capture: cv2.VideoCapture) -> None:
        """Apply common camera capture settings."""
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
        capture.set(cv2.CAP_PROP_FPS, self.fps)

        # Reduce latency by keeping a shallow driver buffer where supported.
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if self.fourcc and len(self.fourcc) == 4:
            fourcc_val = cv2.VideoWriter_fourcc(*self.fourcc)
            capture.set(cv2.CAP_PROP_FOURCC, fourcc_val)

        if self.auto_exposure is not None:
            capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, float(self.auto_exposure))

        if self.exposure is not None:
            capture.set(cv2.CAP_PROP_EXPOSURE, float(self.exposure))

        if self.gain is not None:
            capture.set(cv2.CAP_PROP_GAIN, float(self.gain))

        if self.brightness is not None:
            capture.set(cv2.CAP_PROP_BRIGHTNESS, float(self.brightness))

    def _is_likely_dead_frame(self, frame: np.ndarray) -> bool:
        """Heuristic to detect invalid all-black/no-signal frames."""
        if frame is None or frame.size == 0:
            return True

        # No-signal camera frames are typically near-zero and almost uniform.
        mean_val = float(np.mean(frame))
        std_val = float(np.std(frame))
        return (
            mean_val < self.no_signal_mean_threshold
            and std_val < self.no_signal_std_threshold
        )

    def _validate_camera_feed(self, capture: cv2.VideoCapture) -> bool:
        """Read warmup frames and confirm camera is returning valid images."""
        valid_frames = 0

        for _ in range(self.warmup_frames):
            ret, frame = capture.read()
            if ret and frame is not None and frame.size > 0:
                if self.strict_signal_validation and self._is_likely_dead_frame(frame):
                    pass
                else:
                    valid_frames += 1
            time.sleep(0.02)

        # Require at least one valid frame to accept the camera.
        return valid_frames > 0

    def _mark_no_signal(self, mean_val: float = 0.0, std_val: float = 0.0) -> None:
        """Update no-signal state from a failed/dead frame sample."""
        self._last_frame_mean = float(mean_val)
        self._last_frame_std = float(std_val)
        self._no_signal_streak += 1
        self._signal_recovery_streak = 0

        if self._no_signal_streak >= self.no_signal_confirm_frames:
            if not self._no_signal:
                logger.warning(
                    "Camera is returning black/no-signal frames. "
                    "Check privacy shutter and OS camera permissions."
                )
            self._no_signal = True

    def _mark_signal_recovery(self, mean_val: float, std_val: float) -> None:
        """Update signal state from a valid frame sample."""
        self._last_frame_mean = float(mean_val)
        self._last_frame_std = float(std_val)
        self._last_valid_frame_time = time.time()
        self._signal_recovery_streak += 1

        if self._signal_recovery_streak >= self.signal_recovery_confirm_frames:
            if self._no_signal:
                logger.info("Camera signal recovered")
            self._no_signal = False
            self._no_signal_streak = 0

    def _is_signal_stale(self) -> bool:
        """Return True when no valid frame has arrived recently."""
        if self._last_valid_frame_time <= 0.0:
            return True
        return (time.time() - self._last_valid_frame_time) > self._signal_stale_timeout
    
    def start(self) -> bool:
        """
        Start camera capture thread.
        
        Returns:
            bool: True if camera started successfully
        """
        if self._running:
            logger.warning("Camera already running")
            return True
            
        # Ensure clean state
        if self._capture is not None:
            self._capture.release()
        
        # Try to open camera with reconnection
        success = self._open_camera()
        if not success:
            return False
        
        # Start capture thread
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        
        logger.info("Camera capture started")
        return True
    
    def _open_camera(self, max_attempts: int = 3, delay: float = 1.0) -> bool:
        """
        Open camera with retry logic.
        
        Args:
            max_attempts: Maximum connection attempts
            delay: Delay between attempts in seconds
            
        Returns:
            bool: True if camera opened successfully
        """
        backends = self._get_backend_candidates()

        for attempt in range(1, max_attempts + 1):
            try:
                for device_id in self.device_candidates:
                    for backend in backends:
                        capture = cv2.VideoCapture(device_id, backend)

                        if not capture.isOpened():
                            capture.release()
                            continue

                        self._apply_capture_settings(capture)

                        if not self._validate_camera_feed(capture):
                            logger.warning(
                                "Camera opened but did not provide valid frames: "
                                f"device={device_id}, backend={self._backend_name(backend)}"
                            )
                            capture.release()
                            continue

                        self._capture = capture
                        self._active_backend = backend
                        self._active_device_id = int(device_id)
                        self._invalid_frame_streak = 0
                        self._no_signal = False
                        self._no_signal_streak = 0
                        self._signal_recovery_streak = 0
                        self._last_valid_frame_time = 0.0
                        self._last_frame_mean = 0.0
                        self._last_frame_std = 0.0
                        logger.info(
                            f"Camera opened successfully on attempt {attempt} "
                            f"using {self._backend_name(backend)} on device {device_id}"
                        )
                        return True
                
            except Exception as e:
                logger.warning(f"Camera open attempt {attempt} failed: {e}")
                if self._capture:
                    self._capture.release()
                    self._capture = None
                
                if attempt < max_attempts:
                    time.sleep(delay)
        
        logger.error("Failed to open camera after all attempts")
        return False
    
    def _capture_loop(self):
        """Internal method: continuous frame capture (runs in thread)."""
        frame_delay = 1.0 / self.fps
        last_frame_time = time.time()
        
        while self._running:
            try:
                if self._capture is None or not self._capture.isOpened():
                    # Try to reconnect
                    logger.warning("Camera disconnected, attempting reconnect...")
                    if not self._open_camera():
                        time.sleep(1.0)
                        continue
                
                # Capture frame
                ret, frame = self._capture.read()
                
                if not ret or frame is None or frame.size == 0:
                    self._mark_no_signal()
                    self._invalid_frame_streak += 1
                    if self._invalid_frame_streak >= max(10, self.fps // 2):
                        logger.warning("Too many invalid frames, reopening camera...")
                        self._capture.release()
                        self._capture = None
                        self._invalid_frame_streak = 0
                    time.sleep(0.1)
                    continue

                mean_val = float(np.mean(frame))
                std_val = float(np.std(frame))
                is_dead_frame = (
                    mean_val < self.no_signal_mean_threshold
                    and std_val < self.no_signal_std_threshold
                )

                if self.strict_signal_validation and is_dead_frame:
                    self._mark_no_signal(mean_val, std_val)
                    self._invalid_frame_streak += 1
                    if self._invalid_frame_streak >= max(15, self.fps):
                        logger.warning("Repeated no-signal frames detected, reopening camera...")
                        self._capture.release()
                        self._capture = None
                        self._invalid_frame_streak = 0
                    time.sleep(0.05)
                    continue

                self._invalid_frame_streak = 0

                # Track signal quality so the app can warn users on privacy-shutter/permission cases.
                if is_dead_frame:
                    self._mark_no_signal(mean_val, std_val)
                else:
                    self._mark_signal_recovery(mean_val, std_val)
                
                # Add frame to queue (drop oldest if full)
                try:
                    self._frame_queue.put_nowait(frame)
                except queue.Full:
                    # Remove oldest frame and add new
                    try:
                        self._frame_queue.get_nowait()
                        self._frame_queue.put_nowait(frame)
                    except queue.Empty:
                        pass
                
                # Update statistics
                self._frame_count += 1
                current_time = time.time()
                elapsed = current_time - self._last_fps_time
                
                if elapsed >= 1.0:
                    self._fps_actual = self._frame_count / elapsed
                    self._frame_count = 0
                    self._last_fps_time = current_time
                
                # Frame rate control
                elapsed_frame = time.time() - last_frame_time
                sleep_time = frame_delay - elapsed_frame
                if sleep_time > 0:
                    time.sleep(sleep_time)
                last_frame_time = time.time()
                
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
        
        logger.info("Capture loop stopped")
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Get the latest frame from buffer.
        
        Returns:
            numpy.ndarray: Frame in BGR format, or None if unavailable
        """
        if not self._running:
            return None
        
        try:
            # Get latest frame (non-blocking)
            frame = None
            while not self._frame_queue.empty():
                try:
                    frame = self._frame_queue.get_nowait()
                except queue.Empty:
                    break
            return frame
        except Exception as e:
            logger.error(f"Error reading frame: {e}")
            return None
    
    def get_frame_blocking(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Get frame with blocking wait.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            Frame or None if timeout
        """
        try:
            return self._frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def stop(self):
        """Stop camera capture and release resources."""
        logger.info("Stopping camera...")
        
        self._running = False
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        # Release camera
        if self._capture:
            self._capture.release()
            self._capture = None
        
        # Clear queue
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break
        
        logger.info("Camera stopped")
    
    def is_running(self) -> bool:
        """Check if camera is actively capturing."""
        return self._running and self._capture is not None
    
    def get_fps(self) -> float:
        """Get actual FPS."""
        return self._fps_actual
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get actual resolution."""
        if self._capture:
            width = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return (width, height)
        return self.resolution

    def get_backend(self) -> str:
        """Get the currently active camera backend name."""
        return self._backend_name(self._active_backend)

    def get_active_device_id(self) -> int:
        """Get currently active camera device index."""
        return int(self._active_device_id)

    def has_signal(self) -> bool:
        """Check whether the camera appears to provide a visible video signal."""
        if not self._running:
            return False
        if self._no_signal:
            return False
        if self._is_signal_stale():
            return False
        return True

    def get_signal_stats(self) -> Dict[str, Any]:
        """Get lightweight signal diagnostics for UI/API health reporting."""
        frame_age = None
        if self._last_valid_frame_time > 0.0:
            frame_age = round(time.time() - self._last_valid_frame_time, 2)

        return {
            'has_signal': self.has_signal(),
            'active_device_id': self.get_active_device_id(),
            'device_candidates': self.device_candidates,
            'mean_brightness': round(self._last_frame_mean, 2),
            'stddev': round(self._last_frame_std, 2),
            'no_signal_streak': self._no_signal_streak,
            'signal_recovery_streak': self._signal_recovery_streak,
            'no_signal_mean_threshold': self.no_signal_mean_threshold,
            'no_signal_std_threshold': self.no_signal_std_threshold,
            'no_signal_confirm_frames': self.no_signal_confirm_frames,
            'signal_recovery_confirm_frames': self.signal_recovery_confirm_frames,
            'frame_age_seconds': frame_age,
            'signal_stale': self._is_signal_stale(),
            'signal_stale_timeout_seconds': round(self._signal_stale_timeout, 2)
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
