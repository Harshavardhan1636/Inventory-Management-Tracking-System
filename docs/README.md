# Inventory-Management-Tracking-System Documentation Index

Welcome to the complete documentation for Inventory-Management-Tracking-System.

## 📚 Documentation Overview

This documentation covers everything from installation to advanced development. Choose the guide that best fits your needs.

---

## 🚀 Quick Start

**New to Inventory-Management-Tracking-System?** Start here:
1. [Installation Guide](INSTALLATION.md) - Get Inventory-Management-Tracking-System up and running
2. [User Guide](USER_GUIDE.md) - Learn how to use the system
3. [Configuration Guide](CONFIGURATION.md) - Customize for your needs

---

## 📖 Complete Documentation

### For Users

**[User Guide](USER_GUIDE.md)** - Complete guide for daily usage
- Dashboard overview
- Managing inventory
- Viewing events and alerts
- Best practices
- FAQ

**[Installation Guide](INSTALLATION.md)** - Setup and installation
- System requirements
- Step-by-step installation
- GPU acceleration setup
- First run instructions
- Verification steps

**[Troubleshooting Guide](TROUBLESHOOTING.md)** - Solutions to common issues
- Installation issues
- Camera problems
- Detection issues
- Performance optimization
- Error message reference

### For Developers

**[Architecture Documentation](ARCHITECTURE.md)** - System design
- Architecture overview
- Layer descriptions
- Data flow diagrams
- Core components
- Database schema
- Design patterns

**[API Reference](API_REFERENCE.md)** - Complete API documentation
- REST endpoints
- WebSocket events
- Request/response formats
- Code examples
- Error handling

**[Development Guide](DEVELOPMENT.md)** - Contributing and extending
- Development setup
- Code style guidelines
- Testing framework
- Adding features
- Debugging techniques
- Contribution workflow

**[Configuration Guide](CONFIGURATION.md)** - All configuration options
- Configuration file structure
- Camera settings
- Detection parameters
- Reasoning thresholds
- Shelf layouts
- Use case examples

---

## 📋 Documentation by Topic

### Installation & Setup
- [System Requirements](INSTALLATION.md#system-requirements)
- [Python Installation](INSTALLATION.md#python-installation)
- [Project Setup](INSTALLATION.md#project-setup)
- [GPU Acceleration](INSTALLATION.md#gpu-acceleration)
- [First Run](INSTALLATION.md#first-run)

### Configuration
- [Camera Configuration](CONFIGURATION.md#camera-settings)
- [Detection Settings](CONFIGURATION.md#detection-settings)
- [Shelf Layouts](CONFIGURATION.md#shelf-configuration)
- [Reasoning Thresholds](CONFIGURATION.md#reasoning-settings)
- [Performance Tuning](CONFIGURATION.md#use-case-examples)

### Usage
- [Dashboard Overview](USER_GUIDE.md#dashboard-overview)
- [Live Video Feed](USER_GUIDE.md#using-the-live-feed)
- [Inventory Management](USER_GUIDE.md#managing-inventory)
- [Event Viewing](USER_GUIDE.md#viewing-events)
- [Alert Management](USER_GUIDE.md#managing-alerts)

### Development
- [Architecture Overview](ARCHITECTURE.md#system-overview)
- [Adding Features](DEVELOPMENT.md#adding-new-features)
- [Testing](DEVELOPMENT.md#testing)
- [API Integration](API_REFERENCE.md)
- [Code Style](DEVELOPMENT.md#code-style)

### Troubleshooting
- [Installation Issues](TROUBLESHOOTING.md#installation-issues)
- [Camera Problems](TROUBLESHOOTING.md#camera-issues)
- [Detection Issues](TROUBLESHOOTING.md#detection-issues)
- [Performance Issues](TROUBLESHOOTING.md#performance-issues)
- [Error Messages](TROUBLESHOOTING.md#error-messages)

---

## 🎯 Common Tasks

### I want to...

**...install Inventory-Management-Tracking-System**
→ [Installation Guide](INSTALLATION.md)

**...configure my camera**
→ [Camera Settings](CONFIGURATION.md#camera-settings)

**...improve detection accuracy**
→ [Detection Settings](CONFIGURATION.md#detection-settings) + [Troubleshooting](TROUBLESHOOTING.md#detection-issues)

**...set up a custom shelf layout**
→ [Shelf Configuration](CONFIGURATION.md#shelf-configuration)

**...use demo mode**
→ [Demo Guide](../DEMO_GUIDE.md)

**...integrate via API**
→ [API Reference](API_REFERENCE.md)

**...add new features**
→ [Development Guide](DEVELOPMENT.md#adding-new-features)

**...optimize performance**
→ [Performance Issues](TROUBLESHOOTING.md#performance-issues)

**...fix camera issues**
→ [Camera Troubleshooting](TROUBLESHOOTING.md#camera-issues)

**...understand the architecture**
→ [Architecture Documentation](ARCHITECTURE.md)

**...contribute code**
→ [Development Guide](DEVELOPMENT.md#contributing)

---

## 📊 Document Summaries

### Installation Guide
**Who:** New users, system administrators  
**What:** Complete installation instructions  
**Length:** ~8,500 words, 15-20 min read  
**Topics:** Requirements, Python setup, dependencies, GPU, verification

### User Guide
**Who:** End users, operators  
**What:** Daily usage instructions  
**Length:** ~13,500 words, 25-30 min read  
**Topics:** Dashboard, inventory, events, alerts, best practices

### Architecture Documentation
**Who:** Developers, technical users  
**What:** System design and internals  
**Length:** ~18,300 words, 35-40 min read  
**Topics:** Layers, data flow, components, database, patterns

### API Reference
**Who:** Developers, integrators  
**What:** Complete API documentation  
**Length:** ~16,200 words, 30-35 min read  
**Topics:** REST endpoints, WebSocket, examples, error handling

### Configuration Guide
**Who:** All users  
**What:** All configuration options  
**Length:** ~15,500 words, 30-35 min read  
**Topics:** All settings, tuning, use cases, optimization

### Development Guide
**Who:** Contributors, developers  
**What:** Development workflow  
**Length:** ~15,700 words, 30-35 min read  
**Topics:** Setup, style, testing, features, debugging

### Troubleshooting Guide
**Who:** All users  
**What:** Problem-solving reference  
**Length:** ~15,500 words, 30-35 min read  
**Topics:** Common issues, solutions, error messages

---

## 🔍 Quick Reference

### Key Concepts

**Temporal Reasoning** - Inventory-Management-Tracking-System's core innovation that filters noise by analyzing detection patterns over time (5-10 frames) before triggering events.

**Shelf Slots** - Grid-based regions where items are expected. Format: `SLOT_{row}_{col}` (e.g., SLOT_0_1).

**Event** - A confirmed state transition (item added/removed/misplaced) after temporal analysis.

**Detection** - Raw YOLOv8 output on a single frame (may flicker).

**Confidence Threshold** - Minimum detection confidence (0.0-1.0) to consider valid.

**Demo Mode** - Runs Inventory-Management-Tracking-System with local image sequence instead of camera (for presentations).

### Important Files

```
config.yaml              # Production configuration
config.demo.yaml         # Demo mode configuration
data/shelf.db           # Production database
data/demo_shelf.db      # Demo database
yolov8n.pt             # YOLO model (auto-downloaded)
main.py                # Application entry point
```

### Default Settings

```yaml
Camera FPS: 30
Resolution: 1280x720
Confidence: 0.5
Temporal Window: 10 frames
Removal Threshold: 5 frames
Low Stock Threshold: 2 items
API Port: 5000
Demo Port: 5050
```

### Common Commands

```bash
# Run production
python main.py

# Run with custom config
python main.py --config my_config.yaml

# Run demo mode
python scripts/run_demo.py

# Run tests
pytest tests/

# Format code
black .
```

---

## 📝 External Resources

### Official Links
- **GitHub Repository** - [Link to repo]
- **Issue Tracker** - [Link to issues]
- **Releases** - [Link to releases]

### Related Documentation
- **YOLOv8 Docs** - https://docs.ultralytics.com/
- **Flask Docs** - https://flask.palletsprojects.com/
- **OpenCV Docs** - https://docs.opencv.org/
- **SQLAlchemy Docs** - https://docs.sqlalchemy.org/

### COCO Dataset Classes
80 detectable classes: person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, traffic light, fire hydrant, stop sign, parking meter, bench, bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, umbrella, handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard, surfboard, tennis racket, **bottle**, wine glass, **cup**, fork, knife, spoon, **bowl**, banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant, bed, dining table, toilet, tv, **laptop**, mouse, remote, keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, **book**, clock, vase, scissors, teddy bear, hair drier, toothbrush

---

## 🆘 Getting Help

### Self-Service
1. Check relevant documentation section
2. Search [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Review [FAQ](USER_GUIDE.md#faq)

### Community Support
1. Search existing [GitHub Issues](../../issues)
2. Check [Discussions](../../discussions) (if enabled)

### Report Issues
Create a [new issue](../../issues/new) with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- System information
- Error messages/logs
- Configuration (sanitized)

---

## 📅 Documentation Updates

**Last Updated:** April 2026  
**Version:** 1.0.0  
**Status:** Complete

### Recent Changes
- Initial comprehensive documentation release
- All 7 guides completed
- Code examples verified
- Screenshots pending (future update)

### Planned Updates
- Add screenshots and diagrams
- Video tutorials
- Translation to other languages
- Interactive API explorer

---

## 🤝 Contributing to Documentation

Documentation contributions welcome! To contribute:

1. **Fork repository**
2. **Edit markdown files** in `docs/`
3. **Follow style:**
   - Clear, concise language
   - Code examples for technical content
   - Tables for comparison
   - Bullet points for lists
4. **Submit pull request**

See [Development Guide](DEVELOPMENT.md#contributing) for details.

---

## 📄 License

This documentation is part of Inventory-Management-Tracking-System and is licensed under the MIT License.

---

<div align="center">

**Need something specific?** Use your browser's search (Ctrl+F) or check the relevant guide above.

[⬆ Back to Top](#inventory-management-tracking-system-documentation-index)

</div>
