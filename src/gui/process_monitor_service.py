"""
Process Monitor Service for tracking browser instances
"""
import threading
import time
import psutil
from typing import Set, Callable, Optional

from src.core.browser_launcher import BrowserLauncher


class ProcessMonitorService:
    """Service for monitoring browser processes and updating UI accordingly"""
    
    def __init__(self):
        self._monitored_profiles: Set[str] = set()
    
    def start_monitor(self, profile_name: str, refresh_callback: Callable, show_details_callback: Callable, 
                      selected_profile: Optional[str] = None):
        """Start monitoring a profile process"""
        if profile_name in self._monitored_profiles:
            return
            
        self._monitored_profiles.add(profile_name)
        
        def watch():
            # Try to get the registered pid first
            pid = None
            for _ in range(15):  # up to ~3s
                active = BrowserLauncher.get_active_processes().get(profile_name)
                if active:
                    pid = active.pid
                    break
                time.sleep(0.2)
            
            if pid:
                # Monitor the specific PID
                while psutil.pid_exists(pid):
                    time.sleep(1.0)
            else:
                # Fallback: monitor using is_running
                while BrowserLauncher.is_running(profile_name):
                    time.sleep(1.0)
            
            # Process ended, update UI
            self._monitored_profiles.discard(profile_name)
            try:
                refresh_callback()
            except Exception:
                # Callback may fail if UI was destroyed
                pass
            try:
                if selected_profile == profile_name:
                    show_details_callback()
            except Exception:
                # Callback may fail if UI was destroyed
                pass
                
        threading.Thread(target=watch, daemon=True).start()
    
    def stop_monitoring(self, profile_name: str):
        """Stop monitoring a specific profile"""
        self._monitored_profiles.discard(profile_name)
    
    def is_monitoring(self, profile_name: str) -> bool:
        """Check if a profile is being monitored"""
        return profile_name in self._monitored_profiles