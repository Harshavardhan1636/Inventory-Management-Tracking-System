"""
Configuration Loader for Inventory-Management-Tracking-System.

Loads and validates YAML configuration files.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Global config storage
_config: Optional[Dict[str, Any]] = None


def _resolve_path_like_entries(config: Dict[str, Any], config_file: Path) -> None:
    """Resolve known relative config paths against the config file directory."""
    base_dir = config_file.parent.resolve()

    def _resolve(section: str, key: str) -> None:
        section_value = config.get(section)
        if not isinstance(section_value, dict):
            return

        raw_value = section_value.get(key)
        if not isinstance(raw_value, str):
            return

        candidate = Path(raw_value)
        if candidate.is_absolute():
            return

        section_value[key] = str((base_dir / candidate).resolve())

    # File/directory references that should be stable regardless of process cwd.
    _resolve('camera', 'demo_fallback_frame')
    _resolve('camera', 'demo_fallback_frames_dir')
    _resolve('shelf', 'layout')
    _resolve('database', 'path')


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    global _config
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ValueError("Configuration file is empty")

        _resolve_path_like_entries(config, config_file)
        
        # Validate required sections
        _validate_config(config)
        
        _config = config
        logger.info(f"Configuration loaded from {config_path}")
        
        return config
        
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")


def get_config() -> Dict[str, Any]:
    """
    Get the currently loaded configuration.
    
    Returns:
        Configuration dictionary
        
    Raises:
        RuntimeError: If configuration hasn't been loaded
    """
    if _config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If configuration is invalid
    """
    required_sections = ['system', 'camera', 'detection', 'shelf', 'reasoning', 
                        'inventory', 'database', 'api']
    
    missing = [s for s in required_sections if s not in config]
    
    if missing:
        raise ValueError(f"Missing configuration sections: {missing}")
    
    # Validate camera settings
    camera = config.get('camera', {})
    if 'device_id' not in camera:
        raise ValueError("Camera device_id not specified")
    
    # Validate detection settings
    detection = config.get('detection', {})
    if 'model' not in detection:
        raise ValueError("Detection model not specified")
    
    conf = detection.get('confidence_threshold', 0.5)
    if not 0 <= conf <= 1:
        raise ValueError(f"confidence_threshold must be between 0 and 1, got {conf}")
    
    # Validate reasoning settings
    reasoning = config.get('reasoning', {})
    if reasoning.get('temporal_window', 10) < 1:
        raise ValueError("temporal_window must be at least 1")
    
    logger.debug("Configuration validation passed")


def get_nested(config: Dict, *keys, default: Any = None) -> Any:
    """
    Get nested configuration value safely.
    
    Args:
        config: Configuration dictionary
        *keys: Keys to traverse
        default: Default value if not found
        
    Returns:
        Configuration value or default
        
    Example:
        get_nested(config, 'camera', 'fps', default=30)
    """
    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default
    return value
