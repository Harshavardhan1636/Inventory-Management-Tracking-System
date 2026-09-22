"""
Object Detection Module for Inventory-Management-Tracking-System.

Wraps YOLOv8 for clean object detection interface.
"""

from ultralytics import YOLO
import torch
import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ObjectDetector:
    """
    YOLOv8-based object detection with confidence filtering.
    
    Wraps Ultralytics YOLOv8 model to provide clean detection interface
    for the shelf intelligence system.
    
    Attributes:
        model: YOLOv8 model instance
        confidence_threshold: Minimum detection confidence
        iou_threshold: IoU threshold for NMS
        device: Computation device ('cpu' or 'cuda')
    """
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.4,
        device: str = "auto",
        use_half_precision: bool = True,
        classes: Optional[List[int]] = None
    ):
        """
        Initialize object detector.
        
        Args:
            model_path: Path to YOLO model weights
            confidence_threshold: Minimum detection confidence (0-1)
            iou_threshold: IoU threshold for NMS
            device: 'auto', 'cpu', 'cuda', or 'cuda:N'
            use_half_precision: Use FP16 on CUDA for higher throughput
            classes: List of class IDs to detect (None = all)
        """
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = self._resolve_device(device)
        self.use_half_precision = use_half_precision and self.device.startswith('cuda')
        self.classes = classes
        
        # Load model
        try:
            logger.info(f"Loading YOLOv8 model: {model_path}")
            self.model = YOLO(model_path)
            self.model.to(self.device)

            if self.device.startswith('cuda'):
                # Enable cuDNN autotuning for fixed-size real-time inference.
                torch.backends.cudnn.benchmark = True
                if hasattr(torch, "set_float32_matmul_precision"):
                    torch.set_float32_matmul_precision("high")
                gpu_index = self._parse_cuda_index(self.device)
                gpu_name = torch.cuda.get_device_name(gpu_index)
                logger.info(
                    f"Using GPU device {self.device} ({gpu_name}), fp16={self.use_half_precision}"
                )
            else:
                logger.info(f"Using CPU device ({self.device})")
            
            # Get class names
            self._class_names = self.model.names
            
            logger.info(f"Model loaded successfully with {len(self._class_names)} classes")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise RuntimeError(f"Failed to load YOLOv8 model: {e}")

    def _resolve_device(self, requested_device: str) -> str:
        """Resolve requested device with safe GPU fallback behavior."""
        requested = (requested_device or "auto").strip().lower()

        if requested in ("auto", "gpu"):
            if torch.cuda.is_available() and torch.cuda.device_count() > 0:
                return "cuda:0"
            return "cpu"

        if requested.startswith("cuda"):
            if not torch.cuda.is_available() or torch.cuda.device_count() == 0:
                logger.warning("CUDA requested but unavailable, falling back to CPU")
                return "cpu"

            idx = self._parse_cuda_index(requested)
            if idx >= torch.cuda.device_count():
                logger.warning(
                    f"Requested CUDA device index {idx} not found, using cuda:0"
                )
                return "cuda:0"

            return f"cuda:{idx}"

        return "cpu"

    def _parse_cuda_index(self, device_name: str) -> int:
        """Extract CUDA index from 'cuda' or 'cuda:N' notation."""
        if ":" not in device_name:
            return 0

        try:
            return max(0, int(device_name.split(":", 1)[1]))
        except ValueError:
            return 0
    
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run object detection on a frame.
        
        Args:
            frame: Input image (BGR format, numpy array)
            
        Returns:
            List of detections, each containing:
            {
                'class_id': int,
                'class_name': str,
                'confidence': float,
                'bbox': [x1, y1, x2, y2],  # absolute coordinates
                'centroid': [cx, cy]
            }
        """
        if frame is None:
            return []
        
        try:
            # Run inference
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=self.classes,
                device=self.device,
                half=self.use_half_precision,
                verbose=False
            )
            
            # Process results
            detections = self._filter_detections(results[0])
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def _filter_detections(self, result) -> List[Dict[str, Any]]:
        """
        Filter and structure YOLO results.
        
        Args:
            result: Single YOLO result object
            
        Returns:
            List of structured detections
        """
        detections = []
        
        if result.boxes is None:
            return detections
        
        boxes = result.boxes
        
        for i in range(len(boxes)):
            # Get bounding box (xyxy format)
            box = boxes.xyxy[i].cpu().numpy()
            x1, y1, x2, y2 = map(int, box)
            
            # Get class and confidence
            class_id = int(boxes.cls[i].cpu().numpy())
            confidence = float(boxes.conf[i].cpu().numpy())
            class_name = self._class_names.get(class_id, f"class_{class_id}")
            
            # Calculate centroid
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            
            detection = {
                'class_id': class_id,
                'class_name': class_name,
                'confidence': round(confidence, 4),
                'bbox': [x1, y1, x2, y2],
                'centroid': [cx, cy]
            }
            
            detections.append(detection)
        
        return detections
    
    def get_class_names(self) -> Dict[int, str]:
        """
        Get dictionary of class ID to class name.
        
        Returns:
            Dict mapping class ID to name
        """
        return self._class_names.copy()
    
    def get_class_name(self, class_id: int) -> str:
        """
        Get class name for a class ID.
        
        Args:
            class_id: Class ID
            
        Returns:
            Class name or 'unknown'
        """
        return self._class_names.get(class_id, "unknown")
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        Update confidence threshold.
        
        Args:
            threshold: New threshold (0-1)
        """
        if 0 <= threshold <= 1:
            self.confidence_threshold = threshold
            logger.info(f"Confidence threshold set to {threshold}")
        else:
            logger.warning(f"Invalid threshold value: {threshold}")
    
    def set_classes(self, classes: Optional[List[int]]) -> None:
        """
        Set classes to detect.
        
        Args:
            classes: List of class IDs or None for all
        """
        self.classes = classes
        if classes:
            class_names = [self._class_names.get(c, f"class_{c}") for c in classes]
            logger.info(f"Detecting classes: {class_names}")
        else:
            logger.info("Detecting all classes")
