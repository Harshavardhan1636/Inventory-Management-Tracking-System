"""
Flask Application Factory for Inventory-Management-Tracking-System.

Creates and configures the Flask application.
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import logging
import os

logger = logging.getLogger(__name__)

# Global SocketIO instance
socketio = SocketIO()


def create_app(config: dict = None) -> Flask:
    """
    Create and configure Flask application.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured Flask application
    """
    # Create Flask app
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'frontend', 'static')
    )
    
    # Load configuration
    app.config['SECRET_KEY'] = 'inventory-management-tracking-system-secret-key-change-in-production'
    
    if config:
        api_config = config.get('api', {})
        app.config['DEBUG'] = api_config.get('debug', False)
    
    # Enable CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize SocketIO with threading mode (best for development)
    socketio.init_app(
        app, 
        cors_allowed_origins="*", 
        async_mode='threading',
        logger=False,
        engineio_logger=False
    )
    
    # Register routes
    from .routes import register_routes
    register_routes(app)
    
    # Register WebSocket handlers
    from .websocket import register_websocket_handlers
    register_websocket_handlers(socketio)
    
    logger.info("Flask application created")
    
    return app


def get_socketio() -> SocketIO:
    """Get the SocketIO instance."""
    return socketio
