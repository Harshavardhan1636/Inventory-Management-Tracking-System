"""
Run Inventory-Management-Tracking-System in isolated presentation demo mode.

This launcher keeps the original project configuration untouched by using
config.demo.yaml and a separate demo database.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.demo.yaml"
FRAMES_DIR = PROJECT_ROOT / "demo_assets" / "inventory_frames"
DEMO_DB_PATH = PROJECT_ROOT / "data" / "demo_shelf.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Inventory-Management-Tracking-System isolated demo mode")
    parser.add_argument(
        "--keep-db",
        action="store_true",
        help="Keep existing demo database instead of starting fresh"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not CONFIG_PATH.exists():
        print(f"Missing config file: {CONFIG_PATH}")
        return 1

    demo_frames = sorted(FRAMES_DIR.glob("demo_frame_*.jpg"))
    if not demo_frames:
        print("No prepared demo frames found.")
        print("1) Add real inventory photos to demo_assets/inventory_photos")
        print("2) Run: python scripts/prepare_demo_frames.py")
        return 1

    if not args.keep_db and DEMO_DB_PATH.exists():
        try:
            DEMO_DB_PATH.unlink(missing_ok=True)
            print("Reset demo database for a clean frontend state.")
        except PermissionError:
            print(
                "Demo database is currently in use; continuing with existing demo state. "
                "Stop other demo servers to start fully fresh."
            )

    command = [
        sys.executable,
        str(PROJECT_ROOT / "main.py"),
        "--config",
        str(CONFIG_PATH),
    ]

    print("Starting Inventory-Management-Tracking-System demo mode...")
    print("Dashboard: http://127.0.0.1:5050")
    print("Press Ctrl+C to stop")
    print()

    return subprocess.call(command, cwd=str(PROJECT_ROOT))


if __name__ == "__main__":
    raise SystemExit(main())
