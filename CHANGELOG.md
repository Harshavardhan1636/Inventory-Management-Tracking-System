# Changelog

All notable changes to the Inventory-Management-Tracking-System project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-06

### Added
- Initial release of Inventory-Management-Tracking-System
- Real-time object detection using YOLOv8 nano model
- Temporal reasoning engine for intelligent event detection
- Automatic inventory tracking with add/remove detection
- Web-based dashboard with live video feed
- RESTful API with 15+ endpoints
- WebSocket support for real-time updates
- Event logging system with full audit trail
- Alert management system with 3-level severity
- Configurable shelf layouts (JSON-based)
- Demo mode for presentations without camera
- SQLite database with 5-table schema
- Comprehensive documentation (8 guides, 120,000+ words)
- Complete test suite with pytest
- Flask 3.0 backend with SocketIO
- HTML/CSS/JavaScript frontend (no frameworks)
- Camera device auto-detection
- GPU acceleration support (CUDA)
- Multi-slot shelf monitoring (customizable grid)
- Low stock alerting system
- Manual inventory adjustment interface
- Event filtering and export functionality

### Core Features
- **Vision Pipeline**: Camera capture, YOLOv8 detection, slot mapping
- **Reasoning Engine**: 10-frame temporal buffer, 5 reasoning rules
- **Decision Engine**: Event-to-action conversion with duplicate prevention
- **Inventory Manager**: CRUD operations, threshold management
- **Alert System**: INFO/WARNING/CRITICAL levels, acknowledgment tracking
- **Database Layer**: SQLAlchemy ORM, automatic schema creation

### Configuration
- YAML-based configuration system
- Camera settings (FPS, resolution, device selection)
- Detection parameters (confidence, IoU thresholds)
- Reasoning thresholds (temporal windows, cooldown periods)
- Inventory settings (low stock thresholds)
- API settings (host, port, CORS)

### Documentation
- README.md - Project overview and quick start
- INSTALLATION.md - Complete setup guide
- USER_GUIDE.md - End-user operation guide
- ARCHITECTURE.md - Technical architecture
- API_REFERENCE.md - Complete API documentation
- CONFIGURATION.md - Configuration options
- DEVELOPMENT.md - Developer guide
- TROUBLESHOOTING.md - Common issues and solutions
- TECHNICAL_ARCHITECTURE_DOCUMENT.md - Complete UML diagrams and architecture

### Demo Mode
- Demo photo capture script
- Demo frame preparation with ranking
- Isolated demo runtime (separate database and port)
- Demo recording script for presentations

### Performance
- 30 FPS video processing (configurable)
- 20-30ms detection latency (CPU), 5-10ms (GPU)
- <5ms reasoning latency
- Real-time WebSocket updates (<10ms LAN)
- Scalable to multiple concurrent clients

### Dependencies
- Python 3.8+
- Flask 3.0.0
- Flask-SocketIO 5.3.4
- Ultralytics YOLOv8 8.3.0+
- PyTorch 2.6+
- OpenCV 4.8.1
- SQLAlchemy 2.0.21
- PyYAML 6.0.1

---

## [Unreleased]

### Planned Features
- Multi-camera support
- PostgreSQL database option
- Authentication and authorization
- Role-based access control (RBAC)
- Advanced analytics dashboard
- Historical trend analysis
- Email/SMS alert notifications
- Mobile app (iOS/Android)
- Custom model training interface
- Cloud deployment support
- Kubernetes deployment configs
- Docker containerization
- CI/CD pipeline integration
- Advanced reporting system
- Data export to CSV/Excel/PDF
- Integration with ERP systems
- Barcode/QR code support
- Voice commands integration
- Dark/light theme toggle
- Multi-language support

### Known Issues
- Single camera limitation per instance
- SQLite performance limits (~1MB/sec writes)
- No authentication in current version
- CORS allows all origins (development mode)
- Hardcoded secret keys (needs environment variables)

### Future Improvements
- Performance optimization for higher FPS
- Enhanced temporal reasoning algorithms
- Machine learning for pattern prediction
- Automated inventory ordering suggestions
- Integration with POS systems
- Advanced visualization and charts
- Customizable alert conditions
- Scheduled reports
- User preferences and profiles

---

## Version History

- **1.0.0** (2026-04-06) - Initial release

---

## Contributing

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for contribution guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
