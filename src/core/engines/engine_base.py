"""
Engine base interface for browser engines
"""
from pathlib import Path
from typing import Optional, Callable

from src.utils.fingerprint_generator import BrowserFingerprint
from src.utils.proxy_manager import ProxyConfig


class EngineBase:
    """Base class for browser engines"""
    name: str = "base"

    def run(
        self,
        profile_dir: Path,
        profile_name: str,
        fingerprint: Optional[BrowserFingerprint],
        proxy: Optional[ProxyConfig],
        headless: bool,
        extra_args: Optional[list],
        restore_session: bool,
        register_process: Callable[[int], None],
        save_session: Callable[[Path, list], None],
        load_session: Callable[[Path], list],
    ) -> None:
        """Run the browser synchronously. Implemented by concrete engines."""
        raise NotImplementedError
