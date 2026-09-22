Place real inventory photos in this folder for demo mode.

Recommended:
- 6 to 12 images
- Landscape orientation (or at least clear shelf visibility)
- Include product classes YOLO recognizes (bottle, cup, book, etc.)
- Capture slight variations (angle, item count changes) for event timeline demos

Final demo shortcut:
- Drop the final shelf demo image here (the Books / Apples / Ceramic Mugs / Headphones / Bananas / Bottled Water shelf)
- Run: python scripts/prepare_demo_frames.py

Supported extensions:
- .jpg .jpeg .png .bmp .webp

Run demo:
python main.py --config config.demo.yaml

Open dashboard:
http://127.0.0.1:5050
