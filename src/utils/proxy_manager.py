"""
Proxy management utilities
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from src.config_manager import config_manager

logger = logging.getLogger(__name__)

@dataclass
class ProxyConfig:
    """Proxy configuration"""
    server: str  # host:port or full URL
    username: Optional[str] = None
    password: Optional[str] = None

    def to_playwright_format(self) -> dict:
        """Convert to Playwright proxy format"""
        server = self.server if "://" in self.server else f"http://{self.server}"
        config = {"server": server}
        if self.username and self.password:
            config["username"] = self.username
            config["password"] = self.password
        return config

    def to_dict(self) -> dict:
        return {
            "server": self.server,
            "username": self.username,
            "password": self.password
        }

    @staticmethod
    def from_dict(data: dict) -> 'ProxyConfig':
        return ProxyConfig(**data)

    def __str__(self) -> str:
        if self.username and self.password:
            return f"{self.username}:***@{self.server}"
        return self.server

class ProxyTester:
    """Proxy connectivity tester"""
    
    @staticmethod
    async def test_proxy(proxy: ProxyConfig, test_url: Optional[str] = None) -> bool:
        """Test proxy connectivity"""
        # Get timeout from configuration
        timeout = config_manager.get_int("proxy_test_timeout", 10)
        if not test_url:
            test_url = config_manager.get_str("proxy_test_url", "https://httpbin.org/ip")
            
        # Implementation would go here
        # This is a placeholder for the actual proxy testing logic
        logger.info(f"Testing proxy {proxy} with timeout {timeout}s")
        return True
