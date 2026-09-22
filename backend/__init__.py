"""
Backend API Layer for Inventory-Management-Tracking-System.

Provides Flask REST API and WebSocket support.
"""

from .app import create_app
from .routes import register_routes

__all__ = ['create_app', 'register_routes']
