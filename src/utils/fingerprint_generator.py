"""
Fingerprint generation utilities
Generates realistic browser fingerprints to avoid detection
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class BrowserFingerprint:
    """Browser fingerprint configuration"""
    user_agent: str
    platform: str
    vendor: str
    renderer: str
    language: str
    languages: List[str]
    screen_width: int
    screen_height: int
    viewport_width: int
    viewport_height: int
    hardware_concurrency: int
    device_memory: int
    color_depth: int
    timezone: str
    webgl_vendor: str
    webgl_renderer: str

    def to_dict(self) -> dict:
        return asdict(self)

class FingerprintGenerator:
    """Generates realistic browser fingerprints"""

    # Chrome versions (recent)
    CHROME_VERSIONS = [
        "120.0.6099.109", "119.0.6045.159", "118.0.5993.88",
        "117.0.5938.92", "116.0.5845.96"
    ]

    # Screen resolutions (common)
    SCREEN_RESOLUTIONS = [
        (1920, 1080), (1366, 768), (1440, 900), (1536, 864),
        (1680, 1050), (2560, 1440), (3840, 2160)
    ]

    # WebGL configurations
    WEBGL_CONFIGS = [
        {
            'vendor': 'Google Inc. (NVIDIA)',
            'renderer': 'ANGLE (NVIDIA GeForce GTX 1660 Ti Direct3D11 vs_5_0 ps_5_0)'
        },
        {
            'vendor': 'Google Inc. (Intel)',
            'renderer': 'ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)'
        },
        {
            'vendor': 'Google Inc. (AMD)',
            'renderer': 'ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)'
        },
        {
            'vendor': 'Google Inc. (Apple)',
            'renderer': 'ANGLE (Apple, Apple M1, OpenGL 4.1)'
        },
    ]

    TIMEZONES = [
        'Europe/London', 'America/New_York', 'Europe/Paris',
        'America/Los_Angeles', 'Europe/Berlin', 'Asia/Tokyo',
        'Australia/Sydney', 'America/Chicago', 'Europe/Madrid',
        'Asia/Shanghai', 'Europe/Kiev'
    ]

    @staticmethod
    def generate_user_agent(os_type: str = 'windows') -> str:
        """Generate realistic User Agent string"""
        chrome_version = random.choice(FingerprintGenerator.CHROME_VERSIONS)

        os_strings = {
            'windows': f'Windows NT 10.0; Win64; x64',
            'macos': f'Macintosh; Intel Mac OS X 10_15_7',
            'linux': f'X11; Linux x86_64'
        }

        os_string = os_strings.get(os_type, os_strings['windows'])

        return (
            f'Mozilla/5.0 ({os_string}) '
            f'AppleWebKit/537.36 (KHTML, like Gecko) '
            f'Chrome/{chrome_version} Safari/537.36'
        )

    @staticmethod
    def generate(os_type: str = 'windows', custom_user_agent: Optional[str] = None) -> BrowserFingerprint:
        """Generate complete browser fingerprint"""

        # Screen resolution
        screen_width, screen_height = random.choice(FingerprintGenerator.SCREEN_RESOLUTIONS)
        viewport_width = screen_width - random.randint(0, 20)
        viewport_height = screen_height - random.randint(60, 150)

        # WebGL
        webgl_config = random.choice(FingerprintGenerator.WEBGL_CONFIGS)

        # Platform-specific settings
        platforms = {
            'windows': {
                'platform': 'Win32',
                'vendor': 'Google Inc.',
                'renderer': 'Google Inc. (NVIDIA)',
            },
            'macos': {
                'platform': 'MacIntel',
                'vendor': 'Google Inc.',
                'renderer': 'Google Inc. (Apple)',
            },
            'linux': {
                'platform': 'Linux x86_64',
                'vendor': 'Google Inc.',
                'renderer': 'Google Inc. (NVIDIA)',
            }
        }

        platform_config = platforms.get(os_type, platforms['windows'])

        # Hardware specs
        hardware_concurrency = random.choice([4, 8, 12, 16])
        device_memory = random.choice([4, 8, 16, 32])

        # Language
        languages_options = [
            (['en-US', 'en'], 'en-US'),
            (['ru-RU', 'ru', 'en-US', 'en'], 'ru-RU'),
            (['de-DE', 'de', 'en-US', 'en'], 'de-DE'),
            (['fr-FR', 'fr', 'en-US', 'en'], 'fr-FR'),
        ]
        languages, language = random.choice(languages_options)

        return BrowserFingerprint(
            user_agent=custom_user_agent or FingerprintGenerator.generate_user_agent(os_type),
            platform=platform_config['platform'],
            vendor=platform_config['vendor'],
            renderer=platform_config['renderer'],
            language=language,
            languages=languages,
            screen_width=screen_width,
            screen_height=screen_height,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            hardware_concurrency=hardware_concurrency,
            device_memory=device_memory,
            color_depth=24,
            timezone=random.choice(FingerprintGenerator.TIMEZONES),
            webgl_vendor=webgl_config['vendor'],
            webgl_renderer=webgl_config['renderer']
        )

    @staticmethod
    def from_dict(data: dict) -> BrowserFingerprint:
        """Create fingerprint from dictionary"""
        return BrowserFingerprint(**data)