"""
Vision Pipeline Module for Inventory-Management-Tracking-System.

Unified interface for the complete vision perception layer.
"""

import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import time
import logging

from .camera import CameraStream
from .detector import ObjectDetector
from .slot_mapper import SlotMapper
from .gemini_verifier import GeminiHybridVerifier

logger = logging.getLogger(__name__)


class VisionPipeline:
    """
    Unified interface for the complete vision perception layer.
    
    Orchestrates camera capture, object detection, and slot mapping
    into a single pipeline.
    
    Attributes:
        camera: CameraStream instance
        detector: ObjectDetector instance
        slot_mapper: SlotMapper instance
    """
    
    def __init__(self, config: Dict):
        """
        Initialize complete vision pipeline.
        
        Args:
            config: Configuration dictionary containing:
                - camera: Camera settings
                - detection: Detection settings
                - shelf: Shelf layout settings
        """
        self.config = config
        
        # Extract configuration
        camera_config = config.get('camera', {})
        detection_config = config.get('detection', {})
        shelf_config = config.get('shelf', {})
        
        # Initialize camera
        self.camera = CameraStream(
            device_id=camera_config.get('device_id', 0),
            device_candidates=camera_config.get('device_candidates'),
            fps=camera_config.get('fps', 30),
            resolution=tuple(camera_config.get('resolution', [1280, 720])),
            buffer_size=camera_config.get('buffer_size', 2),
            backend=camera_config.get('backend', 'auto'),
            fourcc=camera_config.get('fourcc', 'MJPG'),
            warmup_frames=camera_config.get('warmup_frames', 8),
            auto_exposure=camera_config.get('auto_exposure', 0.75),
            exposure=camera_config.get('exposure'),
            gain=camera_config.get('gain'),
            brightness=camera_config.get('brightness'),
            strict_signal_validation=camera_config.get('strict_signal_validation', False),
            no_signal_mean_threshold=camera_config.get('no_signal_mean_threshold', 2.0),
            no_signal_std_threshold=camera_config.get('no_signal_std_threshold', 1.0),
            no_signal_confirm_frames=camera_config.get('no_signal_confirm_frames', 5),
            signal_recovery_confirm_frames=camera_config.get('signal_recovery_confirm_frames', 5)
        )
        
        # Initialize detector
        self.detector = ObjectDetector(
            model_path=detection_config.get('model', 'yolov8n.pt'),
            confidence_threshold=detection_config.get('confidence_threshold', 0.5),
            iou_threshold=detection_config.get('iou_threshold', 0.4),
            device=detection_config.get('device', 'auto'),
            use_half_precision=detection_config.get('use_half_precision', True),
            classes=detection_config.get('classes') or None
        )
        
        # Get resolution for slot mapper
        resolution = camera_config.get('resolution', [1280, 720])
        
        # Initialize slot mapper
        self.slot_mapper = SlotMapper(
            frame_width=resolution[0],
            frame_height=resolution[1],
            layout_config_path=shelf_config.get('layout', 'config/shelf_layouts/retail_3x2.json')
        )
        
        # State
        self._running = False
        self._last_frame: Optional[np.ndarray] = None
        self._last_detections: List[Dict] = []
        self._last_gemini_slot_hints: Dict[str, Dict[str, Any]] = {}
        self._input_mode = 'camera'
        self._attachment_path: Optional[Path] = None
        self._attachment_name: Optional[str] = None
        self._attachment_kind: Optional[str] = None
        self._attachment_loop = True
        self._attachment_image_frame: Optional[np.ndarray] = None
        self._attachment_video_capture: Optional[cv2.VideoCapture] = None
        self._using_demo_fallback = False
        self._force_demo_mode = bool(camera_config.get('force_demo_mode', False))
        self._demo_only_running = False
        self._gemini_conflict_threshold = float(
            config.get('gemini', {}).get('conflict_confidence_threshold', 0.75)
        )
        self._gemini_disagreement_penalty = max(
            0.1,
            min(1.0, float(config.get('gemini', {}).get('disagreement_penalty', 0.5)))
        )
        self._gemini_agreement_weight = max(
            0.0,
            min(1.0, float(config.get('gemini', {}).get('agreement_weight', 0.3)))
        )

        # Optional no-signal fallback to keep the full stack testable without camera signal.
        self._demo_fallback_enabled = camera_config.get('use_demo_fallback_on_no_signal', False)
        self._demo_frames: List[np.ndarray] = []
        self._demo_index = 0
        self._demo_frame_interval_seconds = max(
            0.0,
            float(camera_config.get('demo_frame_interval_seconds', 1.0))
        )
        self._demo_last_switch_ts = 0.0

        if self._demo_fallback_enabled:
            self._load_demo_fallback_frames(
                single_frame_path=camera_config.get('demo_fallback_frame'),
                frames_dir=camera_config.get('demo_fallback_frames_dir', 'demo_output')
            )

        # Optional Gemini verifier (secondary validation only; YOLO remains primary).
        self.gemini_verifier = GeminiHybridVerifier(
            config=config.get('gemini', {}),
            slot_ids=self.slot_mapper.get_all_slot_ids(),
            expected_items=self.slot_mapper.expected_items,
        )
        
        logger.info("VisionPipeline initialized")

    def _release_attachment_capture(self) -> None:
        """Release any open video capture used for attachment mode."""
        if self._attachment_video_capture is not None:
            self._attachment_video_capture.release()
            self._attachment_video_capture = None

    def _is_video_attachment(self, path: Path) -> bool:
        """Return True when the file extension indicates a video file."""
        return path.suffix.lower() in {
            '.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.wmv', '.mpg', '.mpeg'
        }

    def set_camera_input(self) -> None:
        """Switch pipeline input source back to the live camera feed."""
        self._input_mode = 'camera'
        self._demo_only_running = False
        self._using_demo_fallback = False

    def configure_attachment_input(self, media_path: str, loop: bool = True) -> bool:
        """Configure pipeline to use a static image or looping video as input."""
        candidate = Path(media_path)
        if not candidate.exists() or not candidate.is_file():
            logger.error(f"Attachment media file not found: {media_path}")
            return False

        self._release_attachment_capture()
        self._attachment_image_frame = None

        if self._is_video_attachment(candidate):
            capture = cv2.VideoCapture(str(candidate))
            if not capture.isOpened():
                logger.error(f"Unable to open attachment video: {media_path}")
                capture.release()
                return False

            # Validate at least one frame exists and rewind.
            ok, frame = capture.read()
            if not ok or frame is None or frame.size == 0:
                logger.error(f"Attachment video has no readable frames: {media_path}")
                capture.release()
                return False
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

            self._attachment_video_capture = capture
            self._attachment_kind = 'video'
        else:
            frame = cv2.imread(str(candidate))
            if frame is None or frame.size == 0:
                logger.error(f"Unable to decode attachment image: {media_path}")
                return False

            self._attachment_image_frame = cv2.resize(frame, self.camera.resolution)
            self._attachment_kind = 'image'

        self._attachment_path = candidate.resolve()
        self._attachment_name = candidate.name
        self._attachment_loop = bool(loop)
        self._input_mode = 'attachment'
        self._demo_only_running = False
        self._using_demo_fallback = False

        if self.camera.is_running():
            self.camera.stop()

        logger.info(
            f"Attachment input configured: {self._attachment_name} "
            f"(type={self._attachment_kind}, loop={self._attachment_loop})"
        )
        return True

    def clear_attachment_input(self) -> None:
        """Clear attachment source and return pipeline to camera mode."""
        self._release_attachment_capture()
        self._attachment_path = None
        self._attachment_name = None
        self._attachment_kind = None
        self._attachment_image_frame = None
        self._attachment_loop = True
        self.set_camera_input()

    def _get_attachment_frame(self) -> Optional[np.ndarray]:
        """Read next frame from configured attachment source."""
        if self._attachment_kind == 'image':
            if self._attachment_image_frame is None:
                return None
            return self._attachment_image_frame.copy()

        if self._attachment_kind != 'video':
            return None

        capture = self._attachment_video_capture
        if capture is None:
            return None

        ok, frame = capture.read()
        if (not ok or frame is None or frame.size == 0) and self._attachment_loop:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = capture.read()

        if not ok or frame is None or frame.size == 0:
            return None

        return cv2.resize(frame, self.camera.resolution)

    def _load_demo_fallback_frames(self, single_frame_path: Optional[str], frames_dir: str) -> None:
        """Load fallback frames that are used only when camera has no visible signal."""
        frame_paths: List[Path] = []

        if single_frame_path:
            candidate = Path(single_frame_path)
            if candidate.exists():
                frame_paths.append(candidate)
            else:
                logger.warning(f"Demo fallback frame not found: {single_frame_path}")

        if not frame_paths:
            directory = Path(frames_dir)
            if directory.exists() and directory.is_dir():
                frame_paths.extend(
                    sorted(
                        [
                            p for p in directory.iterdir()
                            if p.is_file() and p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
                        ]
                    )
                )

        for path in frame_paths:
            frame = cv2.imread(str(path))
            if frame is None:
                continue
            resized = cv2.resize(frame, self.camera.resolution)
            self._demo_frames.append(resized)

        if self._demo_frames:
            logger.warning(
                f"Loaded {len(self._demo_frames)} demo fallback frame(s) for no-signal camera mode"
            )
        else:
            logger.warning("Demo fallback enabled but no valid fallback frames were loaded")

    def _get_demo_fallback_frame(self) -> Optional[np.ndarray]:
        """Return the demo frame, switching at the configured interval."""
        if not self._demo_frames:
            return None

        if self._demo_last_switch_ts <= 0.0:
            self._demo_last_switch_ts = time.monotonic()

        if len(self._demo_frames) > 1 and self._demo_frame_interval_seconds > 0.0:
            now = time.monotonic()
            if now - self._demo_last_switch_ts >= self._demo_frame_interval_seconds:
                self._demo_index = (self._demo_index + 1) % len(self._demo_frames)
                self._demo_last_switch_ts = now

        return self._demo_frames[self._demo_index % len(self._demo_frames)].copy()
    
    def start(self) -> bool:
        """
        Start vision pipeline.
        
        Returns:
            bool: True if started successfully
        """
        if self._input_mode == 'attachment':
            if self._attachment_kind is None:
                logger.error("Attachment mode requested but no attachment source is configured")
                return False

            if self._attachment_kind == 'video' and self._attachment_video_capture is not None:
                self._attachment_video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

            if self.camera.is_running():
                self.camera.stop()

            if self._running:
                logger.warning("Vision pipeline already running in attachment mode")
                return True

            self._running = True
            self._demo_only_running = False
            logger.info("Vision pipeline started in attachment mode")
            return True

        if self._running and (self._demo_only_running or self.camera.is_running()):
            logger.warning("Vision pipeline already running")
            return True

        # Presentation/demo mode can run entirely from local image frames.
        if self._force_demo_mode:
            if not self._demo_frames:
                logger.error("Force demo mode enabled but no demo frames are available")
                return False
            self._demo_index = 0
            self._demo_last_switch_ts = 0.0
            self._running = True
            self._demo_only_running = True
            self._using_demo_fallback = True
            logger.warning("Vision pipeline started in force demo mode (image sequence)")
            return True

        if self._running and not self.camera.is_running():
            success = self.camera.start()
            if success:
                logger.info("Vision pipeline camera input resumed")
            else:
                logger.error("Failed to resume camera input")
            return success
        
        success = self.camera.start()
        if success:
            self._running = True
            self._demo_only_running = False
            logger.info("Vision pipeline started")
        else:
            logger.error("Failed to start vision pipeline")
        
        return success
    
    def stop(self):
        """Stop vision pipeline."""
        self._running = False
        self._demo_only_running = False
        self._demo_last_switch_ts = 0.0
        self._using_demo_fallback = False
        if self.camera.is_running():
            self.camera.stop()
        logger.info("Vision pipeline stopped")

    def shutdown(self) -> None:
        """Fully release pipeline resources for process shutdown."""
        self.stop()
        if self.gemini_verifier:
            self.gemini_verifier.close()

    def _apply_gemini_confidence_fusion(
        self,
        detections: List[Dict[str, Any]],
        slot_hints: Dict[str, Dict[str, Any]],
    ) -> None:
        """
        Fuse Gemini slot hints into per-detection confidence used by reasoning.

        Frontend overlays still show YOLO confidence directly.
        """
        for detection in detections:
            base_conf = float(detection.get('confidence', 0.0))
            fused_conf = base_conf
            slot_id = detection.get('slot_id')

            detection['fused_confidence'] = round(fused_conf, 4)
            detection['gemini_status'] = 'unavailable'
            detection['gemini_item_class'] = None
            detection['gemini_confidence'] = 0.0
            detection['gemini_agreement'] = 'unknown'

            if not slot_id:
                continue

            hint = slot_hints.get(slot_id)
            if not hint:
                continue

            hint_status = str(hint.get('status', 'unknown'))
            hint_item = hint.get('item_class')
            hint_conf = float(hint.get('confidence', 0.0))

            detection['gemini_status'] = hint_status
            detection['gemini_item_class'] = hint_item
            detection['gemini_confidence'] = round(hint_conf, 4)
            detection['gemini_agreement'] = str(hint.get('agreement', 'unknown'))

            yolo_item = str(detection.get('class_name', '')).lower()

            if hint_status == 'item' and hint_item == yolo_item:
                fused_conf = (
                    (1.0 - self._gemini_agreement_weight) * base_conf
                    + self._gemini_agreement_weight * hint_conf
                )
                fused_conf = min(1.0, fused_conf + 0.05)
            elif hint_conf >= self._gemini_conflict_threshold and (
                (hint_status == 'item' and hint_item != yolo_item)
                or hint_status == 'empty'
            ):
                fused_conf = max(0.05, base_conf * self._gemini_disagreement_penalty)

            detection['fused_confidence'] = round(float(fused_conf), 4)
    
    def get_detections(self) -> Dict[str, Any]:
        """
        Get current detections with slot assignments.
        
        Returns:
            {
                'timestamp': str,
                'frame': np.ndarray or None,
                'detections': [
                    {
                        'class_id': int,
                        'class_name': str,
                        'confidence': float,
                        'bbox': [x1, y1, x2, y2],
                        'centroid': [cx, cy],
                        'slot_id': str or None
                    },
                    ...
                ]
            }
        """
        # Get frame from current input source.
        if self._input_mode == 'attachment':
            frame = self._get_attachment_frame()
            self._using_demo_fallback = False
        elif self._demo_only_running:
            frame = self._get_demo_fallback_frame()
            self._using_demo_fallback = frame is not None
        else:
            frame = self.camera.read_frame()
            self._using_demo_fallback = False

        if (
            self._input_mode == 'camera'
            and
            not self._demo_only_running
            and self._demo_fallback_enabled
            and (frame is None or not self.camera.has_signal())
        ):
            demo_frame = self._get_demo_fallback_frame()
            if demo_frame is not None:
                frame = demo_frame
                self._using_demo_fallback = True
        
        if frame is None:
            # Return last known data if no new frame
            return {
                'timestamp': datetime.now().isoformat(),
                'frame': self._last_frame,
                'detections': self._last_detections,
                'gemini_slot_hints': self._last_gemini_slot_hints,
                'gemini_status': self.gemini_verifier.get_status()
            }
        
        self._last_frame = frame
        
        # Run detection
        detections = self.detector.detect(frame)
        
        # Assign slots to detections
        for detection in detections:
            centroid = tuple(detection['centroid'])
            slot_id = self.slot_mapper.map_to_slot(centroid)
            detection['slot_id'] = slot_id

        # Update optional Gemini verifier and fuse confidence for reasoning.
        gemini_slot_hints = self.gemini_verifier.update(frame, detections)
        self._last_gemini_slot_hints = gemini_slot_hints
        if gemini_slot_hints:
            self._apply_gemini_confidence_fusion(detections, gemini_slot_hints)
        else:
            for detection in detections:
                detection['fused_confidence'] = round(float(detection.get('confidence', 0.0)), 4)
                detection['gemini_status'] = 'unavailable'
                detection['gemini_item_class'] = None
                detection['gemini_confidence'] = 0.0
                detection['gemini_agreement'] = 'unknown'
        
        self._last_detections = detections
        
        return {
            'timestamp': datetime.now().isoformat(),
            'frame': frame,
            'detections': detections,
            'gemini_slot_hints': gemini_slot_hints,
            'gemini_status': self.gemini_verifier.get_status(),
        }
    
    def get_annotated_frame(self) -> Optional[np.ndarray]:
        """
        Get frame with bounding boxes and slot grid drawn.
        Uses cached frame/detections to avoid consuming from camera queue
        (which would starve the processing loop).
        
        Returns:
            Annotated frame or None if no frame available
        """
        frame = self._last_frame
        detections = self._last_detections
        
        if frame is None:
            return None
        
        # Draw slot grid first
        annotated = self.slot_mapper.draw_slots(frame)
        
        # Draw each detection
        for detection in detections:
            # Color based on slot assignment
            if detection['slot_id']:
                color = (0, 255, 0)  # Green if in slot
            else:
                color = (0, 165, 255)  # Orange if outside
            
            annotated = self.slot_mapper.draw_detection(annotated, detection, color)
        
        # Add FPS overlay
        fps = self.get_fps()
        cv2.putText(
            annotated,
            f"FPS: {fps:.1f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        # Surface fallback/no-signal conditions directly in-frame.
        if self._input_mode == 'attachment':
            attachment_label = self._attachment_name or 'media file'
            cv2.putText(
                annotated,
                f"ATTACHMENT MODE: {attachment_label}",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 200, 0),
                2
            )
        elif self._using_demo_fallback:
            cv2.putText(
                annotated,
                "DEMO FALLBACK ACTIVE (camera has no visible signal)",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 215, 255),
                2
            )
        elif not self.camera.has_signal():
            cv2.putText(
                annotated,
                "NO CAMERA SIGNAL - Check shutter/permissions",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
        
        # Add detection count
        det_count = len(detections)
        cv2.putText(
            annotated,
            f"Detections: {det_count}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )
        
        return annotated
    
    def get_slot_detections(self) -> Dict[str, Optional[Dict]]:
        """
        Get detection for each slot.
        
        Returns:
            Dict mapping slot_id to detection (or None if empty)
        """
        data = self.get_detections()
        
        # Create mapping of slot to detection
        slot_detections = {slot_id: None for slot_id in self.slot_mapper.get_all_slot_ids()}
        
        for detection in data['detections']:
            slot_id = detection.get('slot_id')
            if slot_id and slot_id in slot_detections:
                # If multiple detections in slot, keep highest confidence
                existing = slot_detections[slot_id]
                if existing is None or detection['confidence'] > existing['confidence']:
                    slot_detections[slot_id] = detection
        
        return slot_detections
    
    def is_running(self) -> bool:
        """Check if pipeline is running."""
        if self._input_mode == 'attachment':
            return self._running and self._attachment_kind is not None
        if self._demo_only_running:
            return self._running
        return self._running and self.camera.is_running()
    
    def get_fps(self) -> float:
        """Get current FPS."""
        if self._input_mode == 'attachment':
            return float(self.config.get('camera', {}).get('fps', 0))
        return self.camera.get_fps()

    def get_input_mode(self) -> str:
        """Get current frame input mode."""
        return self._input_mode
    
    def get_slot_ids(self) -> List[str]:
        """Get all slot IDs."""
        return self.slot_mapper.get_all_slot_ids()
    
    def get_expected_items(self) -> Dict[str, str]:
        """Get expected items for each slot."""
        return self.slot_mapper.expected_items.copy()

    def set_expected_item(self, slot_id: str, item_class: Optional[str], persist: bool = True) -> bool:
        """Assign or clear expected item for a slot and sync Gemini verifier context."""
        success = self.slot_mapper.set_expected_item(slot_id, item_class, persist=persist)
        if not success:
            return False

        normalized = str(item_class).strip().lower() if item_class is not None else None
        if normalized:
            self.gemini_verifier.expected_items[slot_id] = normalized
        else:
            self.gemini_verifier.expected_items.pop(slot_id, None)

        return True

    def get_camera_status(self) -> Dict[str, Any]:
        """Get camera diagnostics and runtime status for health endpoints/UI."""
        base_stats = self.camera.get_signal_stats()

        if self._input_mode == 'attachment':
            base_stats.update(
                {
                    'has_signal': True,
                    'signal_stale': False,
                    'frame_age_seconds': 0.0,
                    'active_device_id': -1,
                    'device_candidates': []
                }
            )
        elif self._demo_only_running:
            base_stats.update(
                {
                    'has_signal': True,
                    'signal_stale': False,
                    'frame_age_seconds': 0.0,
                    'active_device_id': -1
                }
            )

        return {
            'running': self.is_running(),
            'fps': round(self.get_fps(), 2),
            'backend': (
                'ATTACHMENT'
                if self._input_mode == 'attachment'
                else (self.camera.get_backend() if not self._demo_only_running else 'DEMO')
            ),
            'resolution': list(self.camera.get_resolution()),
            'input_mode': self._input_mode,
            'attachment_active': self._input_mode == 'attachment',
            'attachment_type': self._attachment_kind,
            'attachment_name': self._attachment_name,
            'attachment_loop': self._attachment_loop,
            'using_demo_fallback': self._using_demo_fallback,
            'force_demo_mode': self._demo_only_running,
            'demo_fallback_frames': len(self._demo_frames),
            'demo_frame_interval_seconds': self._demo_frame_interval_seconds,
            'current_demo_frame_index': self._demo_index,
            'gemini': self.gemini_verifier.get_status(),
            **base_stats
        }
