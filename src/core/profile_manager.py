"""
Core profile management functionality
"""
import json
import logging
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Callable, Any
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config import PROFILES_DIR, METADATA_FILE
from src.config_manager import config_manager

from src.core.browser_launcher import BrowserLauncher
from src.utils.fingerprint_generator import BrowserFingerprint, FingerprintGenerator
from src.utils.proxy_manager import ProxyConfig

logger = logging.getLogger(__name__)

# Custom exceptions for better error handling
class ProfileError(Exception):
    """Base exception for profile-related errors"""
    pass

class ProfileNotFoundError(ProfileError):
    """Raised when a profile is not found"""
    pass

class ProfileAlreadyExistsError(ProfileError):
    """Raised when trying to create a profile that already exists"""
    pass

class ProfileIOError(ProfileError):
    """Raised when there are IO errors with profile operations"""
    pass

class ProfileValidationError(ProfileError):
    """Raised when profile data validation fails"""
    pass

class ProfileMetadata:
    """Metadata for a browser profile"""
    def __init__(self, name: str, created: str, path: str, fingerprint: Optional[Dict] = None,
                 proxy: Optional[Dict] = None, notes: str = "", engine: str = "chromedriver",
                 last_launched: str = ""):
        self.name = name
        self.created = created
        self.path = path
        self.fingerprint = fingerprint
        self.proxy = proxy
        self.notes = notes
        # Use profile-specific engine setting, fallback to global config, then default to chromedriver
        self.engine = engine if engine != "chromedriver" else config_manager.get_str("browser_engine", engine)
        self.last_launched = last_launched

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'created': self.created,
            'path': self.path,
            'fingerprint': self.fingerprint,
            'proxy': self.proxy,
            'notes': self.notes,
            'engine': self.engine,
            'last_launched': self.last_launched
        }

    @staticmethod
    def from_dict(data: dict) -> 'ProfileMetadata':
        return ProfileMetadata(
            name=data.get('name', ''),
            created=data.get('created', ''),
            path=data.get('path', ''),
            fingerprint=data.get('fingerprint'),
            proxy=data.get('proxy'),
            notes=data.get('notes', ''),
            engine=data.get('engine', 'chromedriver'),
            last_launched=data.get('last_launched', '')
        )

    def get_instance_state(self) -> Dict[str, any]:
        """Get current state of this profile instance"""
        is_running = BrowserLauncher.is_running(self.name)
        
        # Try to get process info
        pid = None
        start_time = None
        
        if is_running:
            active_processes = BrowserLauncher.get_active_processes()
            process = active_processes.get(self.name)
            if process:
                pid = process.pid
                start_time = process.started_at.isoformat() if process.started_at else None
        
        return {
            'profile_name': self.name,
            'is_running': is_running,
            'pid': pid,
            'start_time': start_time
        }

    def start_instance(self, profile_manager, headless: bool = False, extra_args: Optional[List[str]] = None,
                       restore_session: bool = True, engine: Optional[str] = None):
        """Start this profile instance"""
        return BrowserLauncher.launch_from_profile_manager(
            profile_manager,
            self.name,
            headless=headless,
            extra_args=extra_args,
            restore_session=restore_session,
            engine=engine
        )

    def stop_instance(self) -> bool:
        """Stop this running profile instance"""
        return BrowserLauncher.kill_process(self.name)


class ProfileManager:
    """Manages browser profiles with fingerprints and proxies"""

    def __init__(self):
        self.profiles_dir = PROFILES_DIR
        self.metadata_file = METADATA_FILE
        self._ensure_metadata()

    def _ensure_metadata(self):
        """Ensure metadata file exists"""
        try:
            if not self.metadata_file.exists():
                self._save_metadata({})
        except Exception as e:
            logger.error(f"Failed to ensure metadata file exists: {e}")
            raise ProfileIOError(f"Could not initialize metadata file: {str(e)}") from e

    def _handle_io_errors(func: Callable) -> Callable:
        """Decorator to handle common IO errors consistently"""
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except PermissionError as e:
                logger.error(f"Permission denied in {func.__name__}: {e}")
                raise ProfileIOError(f"Permission denied: {str(e)}") from e
            except OSError as e:
                logger.error(f"OS error in {func.__name__}: {e}")
                raise ProfileIOError(f"System error: {str(e)}") from e
            except ProfileError:
                # Re-raise our custom exceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise ProfileError(f"Unexpected error in {func.__name__}: {str(e)}") from e
        return wrapper

    @_handle_io_errors
    def _load_metadata(self) -> Dict[str, ProfileMetadata]:
        """Load profiles metadata"""
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {name: ProfileMetadata.from_dict(meta) for name, meta in data.items()}
        except FileNotFoundError:
            logger.warning(f"Metadata file not found: {self.metadata_file}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in metadata file: {e}")
            raise ProfileIOError(f"Corrupted metadata file: {str(e)}") from e

    @_handle_io_errors
    def _save_metadata(self, metadata: Dict[str, ProfileMetadata]):
        """Save profiles metadata"""
        data = {name: meta.to_dict() for name, meta in metadata.items()}
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def profile_dir(self, name: str) -> Path:
        """Get profile directory path"""
        if not name.strip():
            raise ProfileValidationError("Profile name cannot be empty")
        
        # Sanitize name to prevent directory traversal
        safe = "_".join(name.split())
        if ".." in safe or "/" in safe or "\\" in safe:
            raise ProfileValidationError("Profile name contains invalid characters")
            
        return self.profiles_dir / safe

    def list_profiles(self) -> Dict[str, ProfileMetadata]:
        """Get all profiles"""
        return self._load_metadata()

    def get_profile(self, name: str) -> Optional[ProfileMetadata]:
        """Get specific profile metadata"""
        metadata = self._load_metadata()
        return metadata.get(name)

    def create_profile(
            self,
            name: str,
            os_type: str = 'windows',
            custom_user_agent: Optional[str] = None,
            proxy: Optional[ProxyConfig] = None,
            notes: str = "",
            engine: str = "chromedriver"
    ) -> bool:
        """Create new profile with fingerprint and optional proxy"""
        try:
            pdir = self.profile_dir(name)
            if pdir.exists():
                logger.warning(f"Profile directory already exists: {pdir}")
                raise ProfileAlreadyExistsError(f"Profile '{name}' already exists")

            # Create directory
            pdir.mkdir(parents=True)

            # Generate fingerprint
            fingerprint = FingerprintGenerator.generate(os_type, custom_user_agent)

            # Create notes file
            notes_content = f"Profile created: {datetime.utcnow().isoformat()}\n"
            if notes:
                notes_content += f"\nNotes:\n{notes}\n"
            (pdir / "notes.txt").write_text(notes_content, encoding='utf-8')

            # Save fingerprint to profile directory
            (pdir / "fingerprint.json").write_text(
                json.dumps(fingerprint.to_dict(), indent=2),
                encoding='utf-8'
            )

            # Save proxy config if provided
            if proxy:
                (pdir / "proxy.json").write_text(
                    json.dumps(proxy.to_dict(), indent=2),
                    encoding='utf-8'
                )

            # Update metadata
            metadata = self._load_metadata()
            metadata[name] = ProfileMetadata(
                name=name,
                created=datetime.utcnow().isoformat(),
                path=str(pdir),
                fingerprint=fingerprint.to_dict(),
                proxy=proxy.to_dict() if proxy else None,
                notes=notes,
                engine=engine
            )
            self._save_metadata(metadata)

            logger.info(f"Successfully created profile: {name}")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied creating profile '{name}': {e}")
            # Clean up partially created profile directory
            if 'pdir' in locals() and pdir.exists():
                shutil.rmtree(pdir, ignore_errors=True)
            raise ProfileIOError(f"Permission denied creating profile '{name}': {str(e)}") from e
        except OSError as e:
            logger.error(f"OS error creating profile '{name}': {e}")
            # Clean up partially created profile directory
            if 'pdir' in locals() and pdir.exists():
                shutil.rmtree(pdir, ignore_errors=True)
            raise ProfileIOError(f"System error creating profile '{name}': {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating profile '{name}': {e}")
            # Clean up partially created profile directory
            if 'pdir' in locals() and pdir.exists():
                shutil.rmtree(pdir, ignore_errors=True)
            raise ProfileError(f"Failed to create profile '{name}': {str(e)}") from e
    # В profile_manager.py добавить метод:
    def create_profile_with_fingerprint(
            self,
            name: str,
            os_type: str = 'windows',
            custom_user_agent: Optional[str] = None,
            fingerprint: Optional[BrowserFingerprint] = None,
            proxy: Optional[ProxyConfig] = None,
            notes: str = "",
            engine: str = "chromedriver"
        ) -> bool:
        """Create new profile with direct fingerprint"""
        try:
            pdir = self.profile_dir(name)
            if pdir.exists():
                logger.warning(f"Profile directory already exists: {pdir}")
                raise ProfileAlreadyExistsError(f"Profile '{name}' already exists")

            # Create directory
            pdir.mkdir(parents=True)

            # Generate or use provided fingerprint
            if not fingerprint:
                fingerprint = FingerprintGenerator.generate(os_type, custom_user_agent)

            # Create notes file
            notes_content = f"Profile created: {datetime.utcnow().isoformat()}\n"
            if notes:
                notes_content += f"\nNotes:\n{notes}\n"
            (pdir / "notes.txt").write_text(notes_content, encoding='utf-8')

            # Save fingerprint to profile directory
            (pdir / "fingerprint.json").write_text(
                json.dumps(fingerprint.to_dict(), indent=2),
                encoding='utf-8'
            )

            # Save proxy config if provided
            if proxy:
                (pdir / "proxy.json").write_text(
                    json.dumps(proxy.to_dict(), indent=2),
                    encoding='utf-8'
                )

            # Update metadata
            metadata = self._load_metadata()
            metadata[name] = ProfileMetadata(
                name=name,
                created=datetime.utcnow().isoformat(),
                path=str(pdir),
                fingerprint=fingerprint.to_dict(),
                proxy=proxy.to_dict() if proxy else None,
                notes=notes,
                engine=engine
            )
            self._save_metadata(metadata)
            
            logger.info(f"Successfully created profile with fingerprint: {name}")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied creating profile '{name}': {e}")
            # Clean up partially created profile directory
            if 'pdir' in locals() and pdir.exists():
                shutil.rmtree(pdir, ignore_errors=True)
            raise ProfileIOError(f"Permission denied creating profile '{name}': {str(e)}") from e
        except OSError as e:
            logger.error(f"OS error creating profile '{name}': {e}")
            # Clean up partially created profile directory
            if 'pdir' in locals() and pdir.exists():
                shutil.rmtree(pdir, ignore_errors=True)
            raise ProfileIOError(f"System error creating profile '{name}': {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating profile '{name}': {e}")
            # Clean up partially created profile directory
            if 'pdir' in locals() and pdir.exists():
                shutil.rmtree(pdir, ignore_errors=True)
            raise ProfileError(f"Failed to create profile '{name}': {str(e)}") from e
            
    def update_profile(
            self,
            name: str,
            fingerprint: Optional[BrowserFingerprint] = None,
            proxy: Optional[ProxyConfig] = None,
            notes: Optional[str] = None,
            engine: Optional[str] = None
    ) -> bool:
        """Update profile settings"""
        try:
            metadata = self._load_metadata()
            if name not in metadata:
                logger.warning(f"Profile '{name}' not found for update")
                raise ProfileNotFoundError(f"Profile '{name}' not found")

            pdir = self.profile_dir(name)
            profile = metadata[name]

            # Update fingerprint
            if fingerprint:
                profile.fingerprint = fingerprint.to_dict()
                (pdir / "fingerprint.json").write_text(
                    json.dumps(fingerprint.to_dict(), indent=2),
                    encoding='utf-8'
                )

            # Update proxy
            if proxy is not None:
                profile.proxy = proxy.to_dict()
                (pdir / "proxy.json").write_text(
                    json.dumps(proxy.to_dict(), indent=2),
                    encoding='utf-8'
                )

            # Update notes
            if notes is not None:
                profile.notes = notes
                (pdir / "notes.txt").write_text(notes, encoding='utf-8')

            # Update engine
            if engine is not None:
                profile.engine = engine

            self._save_metadata(metadata)
            logger.info(f"Successfully updated profile: {name}")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied updating profile '{name}': {e}")
            raise ProfileIOError(f"Permission denied updating profile '{name}': {str(e)}") from e
        except OSError as e:
            logger.error(f"OS error updating profile '{name}': {e}")
            raise ProfileIOError(f"System error updating profile '{name}': {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error updating profile '{name}': {e}")
            raise ProfileError(f"Failed to update profile '{name}': {str(e)}") from e

    def delete_profile(self, name: str) -> bool:
        """Delete profile and all its data"""
        try:
            pdir = self.profile_dir(name)
            if not pdir.exists():
                logger.warning(f"Profile directory does not exist: {pdir}")
                raise ProfileNotFoundError(f"Profile '{name}' not found")

            metadata = self._load_metadata()
            if name in metadata:
                del metadata[name]
                self._save_metadata(metadata)

            shutil.rmtree(pdir, ignore_errors=True)
            logger.info(f"Successfully deleted profile: {name}")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied deleting profile '{name}': {e}")
            raise ProfileIOError(f"Permission denied deleting profile '{name}': {str(e)}") from e
        except OSError as e:
            logger.error(f"OS error deleting profile '{name}': {e}")
            raise ProfileIOError(f"System error deleting profile '{name}': {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting profile '{name}': {e}")
            raise ProfileError(f"Failed to delete profile '{name}': {str(e)}") from e

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """Rename profile"""
        try:
            old_dir = self.profile_dir(old_name)
            new_dir = self.profile_dir(new_name)

            if not old_dir.exists():
                logger.warning(f"Source profile directory does not exist: {old_dir}")
                raise ProfileNotFoundError(f"Source profile '{old_name}' not found")
                
            if new_dir.exists():
                logger.warning(f"Target profile directory already exists: {new_dir}")
                raise ProfileAlreadyExistsError(f"Target profile '{new_name}' already exists")

            old_dir.rename(new_dir)

            metadata = self._load_metadata()
            if old_name in metadata:
                profile = metadata.pop(old_name)
                profile.name = new_name
                profile.path = str(new_dir)
                metadata[new_name] = profile
                self._save_metadata(metadata)

            logger.info(f"Successfully renamed profile from '{old_name}' to '{new_name}'")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied renaming profile '{old_name}' to '{new_name}': {e}")
            raise ProfileIOError(f"Permission denied renaming profile: {str(e)}") from e
        except OSError as e:
            logger.error(f"OS error renaming profile '{old_name}' to '{new_name}': {e}")
            raise ProfileIOError(f"System error renaming profile: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error renaming profile '{old_name}' to '{new_name}': {e}")
            raise ProfileError(f"Failed to rename profile: {str(e)}") from e

    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """Duplicate existing profile with new fingerprint"""
        try:
            source_dir = self.profile_dir(source_name)
            new_dir = self.profile_dir(new_name)

            if not source_dir.exists():
                logger.warning(f"Source profile directory does not exist: {source_dir}")
                raise ProfileNotFoundError(f"Source profile '{source_name}' not found")
                
            if new_dir.exists():
                logger.warning(f"Target profile directory already exists: {new_dir}")
                raise ProfileAlreadyExistsError(f"Target profile '{new_name}' already exists")

            # Copy directory
            shutil.copytree(source_dir, new_dir)

            # Load source metadata
            metadata = self._load_metadata()
            source_profile = metadata.get(source_name)

            if source_profile:
                # Generate new fingerprint for duplicate
                os_type = 'windows'  # Default, could be detected from source
                new_fingerprint = FingerprintGenerator.generate(os_type)

                # Save new fingerprint
                (new_dir / "fingerprint.json").write_text(
                    json.dumps(new_fingerprint.to_dict(), indent=2),
                    encoding='utf-8'
                )

                # Create new profile metadata
                metadata[new_name] = ProfileMetadata(
                    name=new_name,
                    created=datetime.utcnow().isoformat(),
                    path=str(new_dir),
                    fingerprint=new_fingerprint.to_dict(),
                    proxy=source_profile.proxy,  # Keep same proxy
                    notes=f"Duplicated from: {source_name}\n{source_profile.notes}"
                )
                self._save_metadata(metadata)
                
            logger.info(f"Successfully duplicated profile from '{source_name}' to '{new_name}'")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied duplicating profile '{source_name}' to '{new_name}': {e}")
            # Clean up partially created profile directory
            if 'new_dir' in locals() and new_dir.exists():
                shutil.rmtree(new_dir, ignore_errors=True)
            raise ProfileIOError(f"Permission denied duplicating profile: {str(e)}") from e
        except OSError as e:
            logger.error(f"OS error duplicating profile '{source_name}' to '{new_name}': {e}")
            # Clean up partially created profile directory
            if 'new_dir' in locals() and new_dir.exists():
                shutil.rmtree(new_dir, ignore_errors=True)
            raise ProfileIOError(f"System error duplicating profile: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error duplicating profile '{source_name}' to '{new_name}': {e}")
            # Clean up partially created profile directory
            if 'new_dir' in locals() and new_dir.exists():
                shutil.rmtree(new_dir, ignore_errors=True)
            raise ProfileError(f"Failed to duplicate profile: {str(e)}") from e

    def get_profile_size(self, name: str) -> int:
        """Get profile directory size in bytes"""
        try:
            pdir = self.profile_dir(name)
            if not pdir.exists():
                logger.warning(f"Profile directory does not exist when getting size: {pdir}")
                raise ProfileNotFoundError(f"Profile '{name}' not found")

            total = 0
            for f in pdir.rglob('*'):
                if f.is_file():
                    total += f.stat().st_size
            return total
        except PermissionError as e:
            logger.error(f"Permission denied accessing profile '{name}' directory: {e}")
            raise ProfileIOError(f"Permission denied accessing profile '{name}': {str(e)}") from e
        except OSError as e:
            logger.error(f"OS error calculating profile '{name}' size: {e}")
            raise ProfileIOError(f"System error calculating profile size: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error calculating profile '{name}' size: {e}")
            raise ProfileError(f"Failed to calculate profile size: {str(e)}") from e