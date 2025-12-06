"""
Proxy management and testing utilities
"""
import asyncio
import aiohttp
import time
from typing import Optional, Dict
from dataclasses import dataclass
from urllib.parse import urlparse


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
    """Test proxy connectivity and performance"""

    @staticmethod
    async def test_proxy_async(proxy_config: ProxyConfig, test_url: str = "https://httpbin.org/ip",
                               timeout: int = 10) -> Dict:
        """Test proxy connection asynchronously"""
        result = {
            "success": False,
            "latency": None,
            "ip": None,
            "error": None
        }

        # Build proxy URL
        if proxy_config.username and proxy_config.password:
            parsed = urlparse(proxy_config.server)
            if parsed.scheme:
                proxy_url = f"{parsed.scheme}://{proxy_config.username}:{proxy_config.password}@{parsed.netloc}"
            else:
                proxy_url = f"http://{proxy_config.username}:{proxy_config.password}@{proxy_config.server}"
        else:
            proxy_url = proxy_config.server if "://" in proxy_config.server else f"http://{proxy_config.server}"

        start_time = time.time()

        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.get(test_url, proxy=proxy_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        result["success"] = True
                        result["latency"] = round((time.time() - start_time) * 1000, 2)  # ms
                        result["ip"] = data.get("origin", "Unknown")
                    else:
                        result["error"] = f"HTTP {response.status}"
        except asyncio.TimeoutError:
            result["error"] = "Connection timeout"
        except aiohttp.ClientProxyConnectionError:
            result["error"] = "Proxy connection failed"
        except aiohttp.ClientConnectorError as e:
            result["error"] = f"Connection error: {str(e)}"
        except Exception as e:
            result["error"] = f"Error: {str(e)}"

        return result

    @staticmethod
    def test_proxy(proxy_config: ProxyConfig, test_url: str = "https://httpbin.org/ip", timeout: int = 10) -> Dict:
        """Test proxy connection (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            ProxyTester.test_proxy_async(proxy_config, test_url, timeout)
        )