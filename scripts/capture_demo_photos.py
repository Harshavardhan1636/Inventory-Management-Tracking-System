"""
Capture real inventory photos from webcam for presentation demo assets.

Usage:
  python scripts/capture_demo_photos.py --count 8 --interval 1.5
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "demo_assets" / "inventory_photos"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture demo inventory photos")
    parser.add_argument("--device", type=int, default=0, help="Camera device index")
    parser.add_argument("--count", type=int, default=8, help="Number of photos to capture")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.5,
        help="Seconds between captures"
    )
    parser.add_argument("--width", type=int, default=1280, help="Capture width")
    parser.add_argument("--height", type=int, default=720, help="Capture height")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(args.device, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(args.device)

    if not cap.isOpened():
        print(f"Unable to open camera device {args.device}")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    print(f"Capturing {args.count} photo(s) every {args.interval:.1f}s")
    print(f"Output folder: {OUTPUT_DIR}")
    print("Arrange inventory scene now...")

    # Brief warmup for auto exposure/focus.
    for _ in range(10):
        cap.read()
        time.sleep(0.05)

    captured = 0
    for idx in range(1, args.count + 1):
        ok, frame = cap.read()
        if not ok or frame is None:
            print(f"Skipped frame {idx}: capture failed")
            time.sleep(max(0.2, args.interval))
            continue

        output_path = OUTPUT_DIR / f"real_inventory_{idx:03d}.jpg"
        cv2.imwrite(str(output_path), frame)
        captured += 1
        print(f"Saved: {output_path.name}")
        time.sleep(max(0.2, args.interval))

    cap.release()
    print(f"Captured {captured}/{args.count} photos")
    return 0 if captured > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
