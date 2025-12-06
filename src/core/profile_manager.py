"""
Core profile management functionality
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

from src.config import PROFILES_DIR, METADATA_FILE
from src.utils.fingerprint_generator import BrowserFingerprint, FingerprintGenerator
from src.utils.proxy_manager import ProxyConfig
from src.utils.cache_cleaner import CacheCleaner


@dataclass
class ProfileMetadata:
    """Metadata for a browser profile"""
    name: str
    created: str
    path: str
    fingerprint: Optional[Dict] = None
    proxy: Optional[Dict] = None
    notes: str = ""
    engine: str = "chromedriver"
    last_launched: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

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


class ProfileManager:
    """Manages browser profiles with fingerprints and proxies"""

    def __init__(self):
        self.profiles_dir = PROFILES_DIR
        self.metadata_file = METADATA_FILE
        self._ensure_metadata()

    def _ensure_metadata(self):
        """Ensure metadata file exists"""
        if not self.metadata_file.exists():
            self._save_metadata({})

    def _load_metadata(self) -> Dict[str, ProfileMetadata]:
        """Load profiles metadata"""
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {name: ProfileMetadata.from_dict(meta) for name, meta in data.items()}
        except Exception:
            return {}

    def _save_metadata(self, metadata: Dict[str, ProfileMetadata]):
        """Save profiles metadata"""
        data = {name: meta.to_dict() for name, meta in metadata.items()}
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def profile_dir(self, name: str) -> Path:
        """Get profile directory path"""
        safe = "_".join(name.split())
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
        pdir = self.profile_dir(name)
        if pdir.exists():
            return False

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

        return True
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
        pdir = self.profile_dir(name)
        if pdir.exists():
            return False

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

        return True 
    def update_profile(
            self,
            name: str,
            fingerprint: Optional[BrowserFingerprint] = None,
            proxy: Optional[ProxyConfig] = None,
            notes: Optional[str] = None,
            engine: Optional[str] = None
    ) -> bool:
        """Update profile settings"""
        metadata = self._load_metadata()
        if name not in metadata:
            return False

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
        return True

    def delete_profile(self, name: str) -> bool:
        """Delete profile and all its data"""
        pdir = self.profile_dir(name)
        if not pdir.exists():
            return False

        metadata = self._load_metadata()
        if name in metadata:
            del metadata[name]
            self._save_metadata(metadata)

        shutil.rmtree(pdir, ignore_errors=True)
        return True

    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """Rename profile"""
        old_dir = self.profile_dir(old_name)
        new_dir = self.profile_dir(new_name)

        if not old_dir.exists() or new_dir.exists():
            return False

        old_dir.rename(new_dir)

        metadata = self._load_metadata()
        if old_name in metadata:
            profile = metadata.pop(old_name)
            profile.name = new_name
            profile.path = str(new_dir)
            metadata[new_name] = profile
            self._save_metadata(metadata)

        return True

    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """Duplicate existing profile with new fingerprint"""
        source_dir = self.profile_dir(source_name)
        new_dir = self.profile_dir(new_name)

        if not source_dir.exists() or new_dir.exists():
            return False

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

        return True

    def get_profile_size(self, name: str) -> int:
        """Get profile directory size in bytes"""
        pdir = self.profile_dir(name)
        if not pdir.exists():
            return 0

        total = 0
        try:
            for f in pdir.rglob('*'):
                if f.is_file():
                    total += f.stat().st_size
        except Exception:
            pass

        return total
    
    def clean_profile_cache(self, name: str, keep_cookies: bool = True, keep_history: bool = False) -> int:
        """Clean cache from profile directory
        
        Args:
            name: Profile name
            keep_cookies: If True, preserves cookies (default: True)
            keep_history: If True, preserves history (default: False)
            
        Returns:
            Number of bytes freed
        """
        pdir = self.profile_dir(name)
        if not pdir.exists():
            return 0
        
        return CacheCleaner.clean_profile_cache(
            pdir,
            keep_cookies=keep_cookies,
            keep_history=keep_history
        )
    
    def get_cleanable_cache_size(self, name: str, keep_cookies: bool = True, keep_history: bool = False) -> int:
        """Get size of cleanable cache without actually cleaning
        
        Args:
            name: Profile name
            keep_cookies: If True, excludes cookies from calculation
            keep_history: If True, excludes history from calculation
            
        Returns:
            Number of bytes that can be freed
        """
        pdir = self.profile_dir(name)
        if not pdir.exists():
            return 0
        
        return CacheCleaner.get_cleanable_size(
            pdir,
            keep_cookies=keep_cookies,
            keep_history=keep_history
        )