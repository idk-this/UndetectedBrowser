"""
Centralized configuration management system
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration loading and access"""
    
    def __init__(self, config_path: str = "settings.json"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {
            "autosync_enabled": True,
            "drive_folder_id": "",
            "proxy_test_timeout": 10,
            "browser_engine": "chromedriver"
        }
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return True
            else:
                # Create default config file if it doesn't exist
                self._config = self._defaults.copy()
                self.save_config()
                logger.info(f"Default configuration created at {self.config_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Fall back to defaults
            self._config = self._defaults.copy()
            return False
    
    def save_config(self) -> bool:
        """Save current configuration to JSON file"""
        try:
            # Ensure the directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with optional default"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self._config[key] = value
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self._config.get(key, default)
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        else:
            return bool(value)
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = self._config.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_str(self, key: str, default: str = "") -> str:
        """Get string configuration value"""
        value = self._config.get(key, default)
        return str(value) if value is not None else default
    
    def update_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        self._config.update(config_dict)
    
    @property
    def all_settings(self) -> Dict[str, Any]:
        """Get all configuration settings"""
        return self._config.copy()


# Global configuration manager instance
config_manager = ConfigManager()