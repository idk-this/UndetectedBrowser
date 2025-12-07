# config.py
"""
Configuration module - Constants and static configuration
"""
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories
APP_DIR = Path.cwd()
PROFILES_DIR = APP_DIR / "profiles"
try:
    PROFILES_DIR.mkdir(exist_ok=True)
except Exception as e:
    logger.error(f"Failed to create profiles directory: {e}")
    raise

# Files
METADATA_FILE = PROFILES_DIR / "profiles.json"

# Browser settings
DEFAULT_BROWSER_ARGS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-dev-shm-usage',
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-infobars',
    '--disable-popup-blocking',
    '--disable-blink-features=AutomationControlled'
]

# UI Colors
UI_COLORS = {
    'primary': '#1a73e8',
    'primary_hover': '#0d62d9',
    'bg_dark': '#1e1e1e',
    'bg_darker': '#171717',
    'card_bg': '#2a2d2e',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'text_gray': '#808080',
    'border': '#3a3d3e',
    'success': '#34a853',
    'warning': '#f9ab00',
    'error': '#ea4335',
}

# Theme settings
CTK_THEME = {
    "fg_color": UI_COLORS['bg_dark'],
    "hover_color": UI_COLORS['card_bg'],
    "border_color": UI_COLORS['border'],
    "text_color": UI_COLORS['text_primary'],
    "button_color": UI_COLORS['primary'],
    "button_hover_color": UI_COLORS['primary_hover'],
}

# Font settings
FONTS = {
    'title': ('Segoe UI', 24, 'bold'),
    'heading': ('Segoe UI', 16, 'bold'),
    'subheading': ('Segoe UI', 14, 'bold'),
    'body': ('Segoe UI', 12),
    'small': ('Segoe UI', 11),
}

# Fingerprint presets
FINGERPRINT_PRESETS = {
    'windows_chrome': {
        'platform': 'Win32',
        'vendor': 'Google Inc.',
        'hardware_concurrency': 8,
        'device_memory': 8,
    },
    'macos_chrome': {
        'platform': 'MacIntel',
        'vendor': 'Google Inc.',
        'hardware_concurrency': 8,
        'device_memory': 16,
    },
    'linux_chrome': {
        'platform': 'Linux x86_64',
        'vendor': 'Google Inc.',
        'hardware_concurrency': 4,
        'device_memory': 8,
    }
}