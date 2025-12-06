"""
Analyze what takes up space in browser profiles
"""
from pathlib import Path
from src.core.profile_manager import ProfileManager


def get_dir_size(path: Path) -> int:
    """Calculate directory size"""
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


def analyze_profile(profile_dir: Path):
    """Analyze profile directory breakdown"""
    if not profile_dir.exists():
        print(f"Profile directory not found: {profile_dir}")
        return
    
    print(f"\n{'='*70}")
    print(f"Analyzing: {profile_dir.name}")
    print(f"{'='*70}")
    
    # Get all subdirectories and files
    items = {}
    
    # Check immediate children
    for item in profile_dir.iterdir():
        if item.is_dir():
            size = get_dir_size(item)
            items[item.name] = size
        elif item.is_file():
            try:
                items[item.name] = item.stat().st_size
            except Exception:
                pass
    
    # Sort by size
    sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)
    
    total_size = sum(items.values())
    
    print(f"\nTotal size: {total_size / (1024*1024):.2f} MB\n")
    print(f"{'Item':<40} {'Size (MB)':<15} {'%':<10}")
    print("-" * 70)
    
    for name, size in sorted_items:
        if size > 0:  # Only show non-empty items
            size_mb = size / (1024 * 1024)
            percent = (size / total_size * 100) if total_size > 0 else 0
            print(f"{name:<40} {size_mb:>10.2f} MB   {percent:>6.1f}%")


def main():
    pm = ProfileManager()
    profiles = pm.list_profiles()
    
    if not profiles:
        print("No profiles found!")
        return
    
    print("\nAvailable profiles:")
    for i, name in enumerate(profiles.keys(), 1):
        total_size = pm.get_profile_size(name)
        print(f"{i}. {name} ({total_size / (1024*1024):.2f} MB)")
    
    # Analyze all profiles
    for name in profiles.keys():
        profile_dir = pm.profile_dir(name)
        analyze_profile(profile_dir)
    
    print("\n" + "="*70)
    print("Analysis complete!")
    print("="*70)


if __name__ == "__main__":
    main()
