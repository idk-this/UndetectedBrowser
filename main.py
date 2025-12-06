# main.py (обновленный для запуска)
"""
Main entry point
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.profile_manager import ProfileManager
from src.gui.main_window import ProfileManagerGUI

def main():
    """Main entry point"""
    try:
        profile_manager = ProfileManager()
        app = ProfileManagerGUI(profile_manager)
        app.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()