"""
Cache cleaning utility to reduce profile size
"""
import shutil
from pathlib import Path
from typing import List


class CacheCleaner:
    """Cleans browser cache and temporary files from profile directories"""
    
    # Directories to clean in Chrome/Chromium profiles
    CACHE_DIRS = [
        'Cache',
        'Code Cache',
        'GPUCache',
        'Service Worker/CacheStorage',
        'Service Worker/ScriptCache',
        'DawnCache',
        'ShaderCache',
    ]
    
    # Files to clean
    CACHE_FILES = [
        'Cookies',
        'Cookies-journal',
        'Network Persistent State',
        'TransportSecurity',
        'Favicons',
        'Favicons-journal',
        'Top Sites',
        'Top Sites-journal',
        'Visited Links',
        'History',
        'History-journal',
        'History Provider Cache',
        'Web Data',
        'Web Data-journal',
        'QuotaManager',
        'QuotaManager-journal',
    ]
    
    @staticmethod
    def clean_profile_cache(profile_dir: Path, keep_cookies: bool = True, keep_history: bool = True) -> int:
        """
        Clean cache from profile directory
        
        Args:
            profile_dir: Path to profile directory
            keep_cookies: If True, preserves cookies
            keep_history: If True, preserves browsing history
            
        Returns:
            Number of bytes freed
        """
        if not profile_dir.exists():
            return 0
        
        bytes_freed = 0
        
        # Chrome stores data in 'Default' profile folder
        default_profile = profile_dir / "Default"
        
        # Clean cache from both root and Default folder
        search_locations = [profile_dir]
        if default_profile.exists():
            search_locations.append(default_profile)
        
        for search_dir in search_locations:
            # Clean cache directories
            for cache_dir_name in CacheCleaner.CACHE_DIRS:
                cache_path = search_dir / cache_dir_name
                if cache_path.exists():
                    try:
                        size = CacheCleaner._get_dir_size(cache_path)
                        shutil.rmtree(cache_path, ignore_errors=True)
                        bytes_freed += size
                    except Exception as e:
                        print(f"Error cleaning {cache_dir_name}: {e}")
            
            # Clean cache files (with optional preservation)
            files_to_clean = []
            for cache_file in CacheCleaner.CACHE_FILES:
                # Skip if user wants to keep cookies
                if keep_cookies and 'Cookie' in cache_file:
                    continue
                # Skip if user wants to keep history
                if keep_history and ('History' in cache_file or 'Visited' in cache_file or 'Top Sites' in cache_file):
                    continue
                files_to_clean.append(cache_file)
            
            for cache_file_name in files_to_clean:
                cache_file = search_dir / cache_file_name
                if cache_file.exists():
                    try:
                        size = cache_file.stat().st_size
                        cache_file.unlink()
                        bytes_freed += size
                    except Exception as e:
                        print(f"Error cleaning {cache_file_name}: {e}")
        
        return bytes_freed
    
    @staticmethod
    def clean_profile_cache_aggressive(profile_dir: Path) -> int:
        """
        Aggressive cache cleaning - removes everything including cookies and history
        
        Args:
            profile_dir: Path to profile directory
            
        Returns:
            Number of bytes freed
        """
        return CacheCleaner.clean_profile_cache(
            profile_dir,
            keep_cookies=False,
            keep_history=False
        )
    
    @staticmethod
    def _get_dir_size(path: Path) -> int:
        """Calculate total size of directory"""
        total = 0
        try:
            for f in path.rglob('*'):
                if f.is_file():
                    try:
                        total += f.stat().st_size
                    except Exception:
                        pass
        except Exception:
            pass
        return total
    
    @staticmethod
    def get_cleanable_size(profile_dir: Path, keep_cookies: bool = True, keep_history: bool = True) -> int:
        """
        Calculate how much space can be freed without actually cleaning
        
        Args:
            profile_dir: Path to profile directory
            keep_cookies: If True, excludes cookies from calculation
            keep_history: If True, excludes history from calculation
            
        Returns:
            Number of bytes that can be freed
        """
        if not profile_dir.exists():
            return 0
        
        total_size = 0
        
        # Chrome stores data in 'Default' profile folder
        default_profile = profile_dir / "Default"
        
        # Check both root and Default folder
        search_locations = [profile_dir]
        if default_profile.exists():
            search_locations.append(default_profile)
        
        for search_dir in search_locations:
            # Calculate cache directories size
            for cache_dir_name in CacheCleaner.CACHE_DIRS:
                cache_path = search_dir / cache_dir_name
                if cache_path.exists():
                    total_size += CacheCleaner._get_dir_size(cache_path)
            
            # Calculate cache files size
            files_to_count = []
            for cache_file in CacheCleaner.CACHE_FILES:
                if keep_cookies and 'Cookie' in cache_file:
                    continue
                if keep_history and ('History' in cache_file or 'Visited' in cache_file or 'Top Sites' in cache_file):
                    continue
                files_to_count.append(cache_file)
            
            for cache_file_name in files_to_count:
                cache_file = search_dir / cache_file_name
                if cache_file.exists():
                    try:
                        total_size += cache_file.stat().st_size
                    except Exception:
                        pass
        
        return total_size
