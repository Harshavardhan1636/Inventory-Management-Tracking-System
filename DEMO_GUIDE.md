# Inventory-Management-Tracking-System Demo Guide (Presentation Ready)

This guide helps you record a reliable demo video/screenshot set using real inventory photos.

## 1) Prepare Real Images

1. Capture 6-12 real photos of shelves/inventory items.
2. Prefer objects YOLO commonly recognizes: bottle, cup, book, box.
3. Save them to `demo_assets/inventory_photos`.

Optional webcam capture:

```bash
python scripts/capture_demo_photos.py --count 8 --interval 1.5
```

## 2) Build Demo Frame Sequence

Run:

```bash
python scripts/prepare_demo_frames.py
```

Output frames are generated into `demo_assets/inventory_frames` as `demo_frame_###.jpg`.
Images are scored by detections, weak/no-detection images are skipped, and top-performing frames are selected automatically.
If you want to include all frames anyway, run:

```bash
python scripts/prepare_demo_frames.py --allow-empty
```

## 3) Start Isolated Demo Runtime

Run:

```bash
python scripts/run_demo.py
```

Open: `http://127.0.0.1:5050`

This uses `config.demo.yaml` and `data/demo_shelf.db` only.
Your original runtime (`config.yaml`, `data/shelf.db`) stays untouched.
Each demo image is shown for 5 seconds before switching to the next frame.

## 4) Recording Checklist

1. Show landing dashboard and live feed.
2. Show shelf state panel updating with detections.
3. Open Events page and scroll timeline.
4. Open Inventory page to show quantity updates.
5. Open Alerts page to show generated notices.

## 5) Troubleshooting

- If launcher says no frames found: run `python scripts/prepare_demo_frames.py`.
- If detections are sparse: use clearer photos with larger visible products.
- If UI does not refresh: hard reload browser once after startup.