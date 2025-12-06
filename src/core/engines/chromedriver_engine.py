"""
ChromeDriver (undetected-chromedriver) engine implementation
"""
import time
from pathlib import Path
from typing import Optional, Callable
import psutil

try:
    import undetected_chromedriver as uc
except ImportError:
    uc = None

from src.utils.fingerprint_generator import BrowserFingerprint
from src.utils.proxy_manager import ProxyConfig
from src.config import DEFAULT_BROWSER_ARGS


class ChromeDriverEngine:
    name = "chromedriver"

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
        if uc is None:
            raise RuntimeError('undetected-chromedriver not available. Install with: pip install undetected-chromedriver')

        options = uc.ChromeOptions()
        args = DEFAULT_BROWSER_ARGS.copy()
        if extra_args:
            args.extend(extra_args)
        # user data dir
        args.append(f"--user-data-dir={str(profile_dir)}")
        # proxy
        if proxy:
            server = proxy.server if '://' in proxy.server else f"http://{proxy.server}"
            args.append(f"--proxy-server={server}")
        # fingerprint basics
        if fingerprint:
            args.append(f"--user-agent={fingerprint.user_agent}")
            args.append(f"--lang={fingerprint.language}")
        args.append('--start-maximized')
        if headless:
            args.append('--headless=new')
        for a in args:
            options.add_argument(a)
        driver = uc.Chrome(options=options)

        # Get browser PID (prefer direct attribute if available)
        browser_pid = getattr(driver, 'browser_pid', None)
        
        # Fallback: find top-level process by user-data-dir and executable name, exclude helper types
        if not browser_pid:
            try:
                pdir_str = str(profile_dir)
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        name = (proc.info['name'] or '').lower()
                        cmdline_list = proc.info['cmdline'] or []
                        cmdline = ' '.join(cmdline_list)
                        if pdir_str in cmdline and (('chrome' in name) or ('msedge' in name)):
                            if not any(arg.startswith('--type=') for arg in cmdline_list):
                                browser_pid = proc.info['pid']
                                break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception:
                pass

        if browser_pid:
            register_process(browser_pid)

        # Restore previous session
        if restore_session:
            saved_urls = load_session(profile_dir)
            if saved_urls:
                try:
                    driver.get(saved_urls[0])
                except Exception as e:
                    print(f"Failed to open first tab {saved_urls[0]}: {e}")
                for url in saved_urls[1:]:
                    try:
                        driver.execute_script(f"window.open('{url}','_blank')")
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Failed to restore tab {url}: {e}")
                # Focus a non-initial tab to keep session alive if first tab is closed
                try:
                    handles = driver.window_handles
                    if handles:
                        driver.switch_to.window(handles[-1])
                except Exception:
                    pass

        # Keep browser open and periodically save session state (robust)
        last_saved = None
        while True:
            try:
                # Check if any windows remain; if none, exit loop
                handles = driver.window_handles
                if not handles:
                    break

                # Try to save session from CDP targets without changing focus
                try:
                    targets = driver.execute_cdp_cmd("Target.getTargets", {})
                    open_urls = []
                    for t in targets.get("targetInfos", []):
                        if t.get("type") == "page":
                            url = t.get("url") or ""
                            if url and url != 'about:blank' and not url.startswith('chrome://'):
                                open_urls.append(url)
                    if open_urls != last_saved:
                        save_session(profile_dir, open_urls)
                        last_saved = open_urls
                except Exception:
                    pass

            except Exception:
                # Attempt to recover by reattaching to last window if possible
                try:
                    handles = driver.window_handles
                    if handles:
                        driver.switch_to.window(handles[-1])
                    else:
                        break
                except Exception:
                    break

            time.sleep(1.0)

        try:
            driver.quit()
        except Exception:
            pass
