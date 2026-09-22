"""
Prepare a presentation-ready demo image sequence from real inventory photos.

Usage:
  python scripts/prepare_demo_frames.py

It reads images from demo_assets/inventory_photos and writes a normalized,
scored sequence to demo_assets/inventory_frames for demo playback.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / "demo_assets" / "inventory_photos"
OUTPUT_DIR = PROJECT_ROOT / "demo_assets" / "inventory_frames"
TARGET_SIZE = (1280, 720)
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Inventory-Management-Tracking-System demo frames")
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Allow saving frames even when there are no detections"
    )
    parser.add_argument(
        "--detector-confidence",
        type=float,
        default=0.20,
        help="Detector confidence for no-detection filtering"
    )
    parser.add_argument(
        "--min-detections",
        type=int,
        default=3,
        help="Minimum detections required for an image to be considered demo-ready"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=3,
        help="Maximum number of top-scoring frames to prepare (0 means no limit)"
    )
    return parser.parse_args()


def iter_source_images(folder: Path) -> Iterable[Path]:
    for path in sorted(folder.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTS:
            yield path


def fit_and_letterbox(image, target_size):
    target_w, target_h = target_size
    h, w = image.shape[:2]

    if h == 0 or w == 0:
        return None

    scale = min(target_w / w, target_h / h)
    resized_w = max(1, int(w * scale))
    resized_h = max(1, int(h * scale))

    resized = cv2.resize(image, (resized_w, resized_h), interpolation=cv2.INTER_AREA)

    top = (target_h - resized_h) // 2
    bottom = target_h - resized_h - top
    left = (target_w - resized_w) // 2
    right = target_w - resized_w - left

    return cv2.copyMakeBorder(
        resized,
        top,
        bottom,
        left,
        right,
        cv2.BORDER_CONSTANT,
        value=(20, 20, 20)
    )


def _build_detector(confidence_threshold: float):
    """Build detector used only for frame filtering."""
    from vision.detector import ObjectDetector

    return ObjectDetector(
        model_path=str(PROJECT_ROOT / "yolov8n.pt"),
        confidence_threshold=confidence_threshold,
        iou_threshold=0.4,
        device="auto",
        use_half_precision=True,
        classes=None,
    )


def main() -> int:
    args = parse_args()
    skip_no_detections = not args.allow_empty

    if not SOURCE_DIR.exists() or not SOURCE_DIR.is_dir():
        print(f"Source folder missing: {SOURCE_DIR}")
        return 1

    images = list(iter_source_images(SOURCE_DIR))
    if not images:
        print("No source images found.")
        print(f"Add files to: {SOURCE_DIR}")
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Remove stale prepared frames for deterministic demo playback.
    for existing in OUTPUT_DIR.glob("demo_frame_*.jpg"):
        existing.unlink(missing_ok=True)

    detector = None
    if skip_no_detections:
        detector = _build_detector(args.detector_confidence)

    prepared_candidates = []
    written = 0
    skipped_empty = []
    skipped_low = []
    for image_path in images:
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"Skipping unreadable image: {image_path.name}")
            continue

        prepared = fit_and_letterbox(image, TARGET_SIZE)
        if prepared is None:
            print(f"Skipping invalid image: {image_path.name}")
            continue

        detection_count = 0
        if detector is not None:
            detections = detector.detect(prepared)
            detection_count = len(detections)
            if detection_count == 0:
                skipped_empty.append(image_path.name)
                print(f"Skipping no-detection image: {image_path.name}")
                continue
            if detection_count < max(0, int(args.min_detections)):
                skipped_low.append((image_path.name, detection_count))
                print(
                    f"Skipping low-detection image: {image_path.name} "
                    f"({detection_count} < {args.min_detections})"
                )
                continue

        prepared_candidates.append((image_path.name, prepared, detection_count))

    if detector is not None:
        prepared_candidates.sort(key=lambda item: item[2], reverse=True)

    dropped_for_limit = []
    if args.max_frames > 0 and len(prepared_candidates) > args.max_frames:
        dropped_for_limit = prepared_candidates[args.max_frames:]
        prepared_candidates = prepared_candidates[:args.max_frames]

    for source_name, prepared, detection_count in prepared_candidates:
        output_name = f"demo_frame_{written + 1:03d}.jpg"
        output_path = OUTPUT_DIR / output_name
        cv2.imwrite(str(output_path), prepared)
        written += 1
        if detector is not None:
            print(f"Selected: {source_name} (detections={detection_count}) -> {output_name}")

    print(f"Prepared {written} frame(s) in {OUTPUT_DIR}")
    if skipped_empty:
        print(f"Skipped {len(skipped_empty)} no-detection image(s):")
        for name in skipped_empty:
            print(f" - {name}")

    if skipped_low:
        print(f"Skipped {len(skipped_low)} low-detection image(s):")
        for name, count in skipped_low:
            print(f" - {name} (detections={count})")

    if dropped_for_limit:
        print(f"Dropped {len(dropped_for_limit)} image(s) due to --max-frames={args.max_frames}:")
        for name, _, count in dropped_for_limit:
            print(f" - {name} (detections={count})")

    if written == 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
