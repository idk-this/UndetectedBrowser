"""
Browser launching with fingerprint injection and proxy support
"""
import threading
import time
import json
import psutil
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime



from src.utils.fingerprint_generator import BrowserFingerprint, FingerprintGenerator
from src.utils.proxy_manager import ProxyConfig
from src.config import DEFAULT_BROWSER_ARGS
from src.core.engines.chromedriver_engine import ChromeDriverEngine
from src.config_manager import config_manager

class BrowserProcess:
    """Represents a running browser process"""

    def __init__(self, profile_name: str, pid: int, headless: bool):
        self.profile_name = profile_name
        self.pid = pid
        self.headless = headless
        self.started_at = datetime.now()
        self._thread = None

    def is_alive(self) -> bool:
        """Check if process is still running"""
        try:
            process = psutil.Process(self.pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def kill(self) -> bool:
        """Kill the browser process"""
        try:
            process = psutil.Process(self.pid)
            # Kill all child processes
            children = process.children(recursive=True)
            for child in children:
                try:
                    child.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # Kill main process
            process.kill()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def get_memory_usage(self) -> float:
        """Get memory usage in MB"""
        try:
            process = psutil.Process(self.pid)
            mem_info = process.memory_info()
            return mem_info.rss / (1024 * 1024)  # Convert to MB
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def get_cpu_percent(self) -> float:
        """Get CPU usage percentage"""
        try:
            process = psutil.Process(self.pid)
            return process.cpu_percent(interval=0.1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def get_uptime(self) -> str:
        """Get process uptime as string"""
        delta = datetime.now() - self.started_at
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours}h {minutes}m"

class BrowserLauncher:
    """Launches browser with custom fingerprint and proxy"""

    # Track running processes
    _active_processes: Dict[str, BrowserProcess] = {}

    @staticmethod
    def get_active_processes() -> Dict[str, BrowserProcess]:
        """Get all active browser processes"""
        # Clean up dead processes
        dead_profiles = []
        for profile_name, process in BrowserLauncher._active_processes.items():
            if not process.is_alive():
                dead_profiles.append(profile_name)

        for profile_name in dead_profiles:
            del BrowserLauncher._active_processes[profile_name]

        return BrowserLauncher._active_processes.copy()

    @staticmethod
    def is_running(profile_name: str) -> bool:
        """Check if profile browser is running"""
        process = BrowserLauncher._active_processes.get(profile_name)
        if process and process.is_alive():
            return True
        
        # Fallback detection: scan for top-level browser process by user-data-dir
        try:
            from src.core.profile_manager import ProfileManager
            pdir = ProfileManager().profile_dir(profile_name)
            pdir_str = str(pdir)
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    name = (proc.info['name'] or '').lower()
                    cmdline_list = proc.info['cmdline'] or []
                    cmdline = ' '.join(cmdline_list)
                    if pdir_str in cmdline and (('chrome' in name) or ('msedge' in name)):
                        # Exclude helper/renderer/gpu processes
                        if not any(arg.startswith('--type=') for arg in cmdline_list):
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return False

    @staticmethod
    def kill_process(profile_name: str) -> bool:
        """Kill browser process for profile"""
        process = BrowserLauncher._active_processes.get(profile_name)
        if process:
            success = process.kill()
            if success:
                del BrowserLauncher._active_processes[profile_name]
            return success
        return False

    @staticmethod
    def _save_session(profile_dir: Path, urls: List[str]):
        """Save open tabs URLs to restore later"""
        session_file = profile_dir / "last_session.json"
        session_data = {
            "urls": urls,
            "saved_at": datetime.now().isoformat()
        }
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)

    @staticmethod
    def _load_session(profile_dir: Path) -> List[str]:
        """Load previously saved tab URLs"""
        session_file = profile_dir / "last_session.json"
        if not session_file.exists():
            return []

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                return session_data.get("urls", [])
        except Exception:
            return []

    @staticmethod
    def _get_fingerprint_script(fingerprint: BrowserFingerprint) -> str:
        """Generate JavaScript to inject fingerprint"""
        return f"""
        (() => {{
            try {{
                // Override navigator properties
                if (navigator) {{
                    Object.defineProperty(navigator, 'userAgent', {{
                        get: () => '{fingerprint.user_agent}'
                    }});
                    Object.defineProperty(navigator, 'platform', {{
                        get: () => '{fingerprint.platform}'
                    }});
                    Object.defineProperty(navigator, 'vendor', {{
                        get: () => '{fingerprint.vendor}'
                    }});
                    Object.defineProperty(navigator, 'language', {{
                        get: () => '{fingerprint.language}'
                    }});
                    Object.defineProperty(navigator, 'languages', {{
                        get: () => {fingerprint.languages}
                    }});
                    Object.defineProperty(navigator, 'hardwareConcurrency', {{
                        get: () => {fingerprint.hardware_concurrency}
                    }});
                    Object.defineProperty(navigator, 'deviceMemory', {{
                        get: () => {fingerprint.device_memory}
                    }});
                    // Remove webdriver property safely
                    try {{
                        Object.defineProperty(navigator, 'webdriver', {{
                            get: () => undefined
                        }});
                    }} catch (e) {{}}
                }}

                // Override screen properties when available
                if (typeof screen !== 'undefined') {{
                    Object.defineProperty(screen, 'width', {{
                        get: () => {fingerprint.screen_width}
                    }});
                    Object.defineProperty(screen, 'height', {{
                        get: () => {fingerprint.screen_height}
                    }});
                    Object.defineProperty(screen, 'availWidth', {{
                        get: () => {fingerprint.screen_width}
                    }});
                    Object.defineProperty(screen, 'availHeight', {{
                        get: () => {fingerprint.screen_height}
                    }});
                    Object.defineProperty(screen, 'colorDepth', {{
                        get: () => {fingerprint.color_depth}
                    }});
                }}

                // Override WebGL only if available
                if (window && window.WebGLRenderingContext) {{
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(param) {{
                        if (param === 37445) {{
                            return '{fingerprint.webgl_vendor}';
                        }}
                        if (param === 37446) {{
                            return '{fingerprint.webgl_renderer}';
                        }}
                        return getParameter.call(this, param);
                    }};
                }}

                // Do not override timezone via Date; Playwright handles timezone emulation
                console.log('🎭 Fingerprint injected successfully');
            }} catch (err) {{
                // Avoid breaking internal pages
                console.debug('Fingerprint injection error:', err);
            }}
        }})();
        """

    @staticmethod
    def launch(
        profile_dir: Path,
        profile_name: str,
        fingerprint: Optional[BrowserFingerprint] = None,
        proxy: Optional[ProxyConfig] = None,
        headless: bool = False,
        extra_args: Optional[List[str]] = None,
        restore_session: bool = True,
        engine: Optional[str] = None
    ):
        """Launch browser with fingerprint and proxy (non-blocking)"""

        # Check if already running
        if BrowserLauncher.is_running(profile_name):
            raise RuntimeError(f"Profile '{profile_name}' is already running")

        def _run():
            try:
                engine_local = engine or config_manager.get_str("browser_engine", "chromedriver")

                def register(pid: int):
                    BrowserLauncher._active_processes[profile_name] = BrowserProcess(
                        profile_name=profile_name,
                        pid=pid,
                        headless=headless
                    )

                if engine_local == 'chromedriver':
                    ChromeDriverEngine().run(
                        profile_dir=profile_dir,
                        profile_name=profile_name,
                        fingerprint=fingerprint,
                        proxy=proxy,
                        headless=headless,
                        extra_args=extra_args,
                        restore_session=restore_session,
                        register_process=register,
                        save_session=BrowserLauncher._save_session,
                        load_session=BrowserLauncher._load_session,
                    )
                else:
                    raise RuntimeError(f"Unknown engine: {engine_local}")
            except Exception as e:
                print(f"Error launching browser: {e}")
            finally:
                if profile_name in BrowserLauncher._active_processes:
                    del BrowserLauncher._active_processes[profile_name]



        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread

    @staticmethod
    def launch_from_profile_manager(
        profile_manager,
        profile_name: str,
        headless: bool = False,
        extra_args: Optional[List[str]] = None,
        restore_session: bool = True,
        engine: Optional[str] = None
    ):
        """Launch browser using ProfileManager"""
        from src.core.profile_manager import ProfileManager

        profile = profile_manager.get_profile(profile_name)
        if not profile:
            raise FileNotFoundError(f"Profile '{profile_name}' not found")

        profile_dir = profile_manager.profile_dir(profile_name)

        # Load fingerprint
        fingerprint = None
        if profile.fingerprint:
            fingerprint = FingerprintGenerator.from_dict(profile.fingerprint)

        # Load proxy
        proxy = None
        if profile.proxy:
            proxy = ProxyConfig.from_dict(profile.proxy)

        # Update last launched time
        try:
            md = profile_manager._load_metadata()
            prof = md.get(profile_name)
            if prof:
                prof.last_launched = datetime.utcnow().isoformat()
                profile_manager._save_metadata(md)
        except Exception:
            pass

        return BrowserLauncher.launch(
            profile_dir=profile_dir,
            profile_name=profile_name,
            fingerprint=fingerprint,
            proxy=proxy,
            headless=headless,
            extra_args=extra_args,
            restore_session=restore_session,
            engine=engine or config_manager.get_str("browser_engine", "chromedriver")
        )