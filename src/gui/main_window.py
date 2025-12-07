# main_window.py
"""
Main GUI window with modern interface
"""
import sys
import os
import subprocess
import threading
import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, List
from datetime import datetime

from src.core.profile_manager import ProfileManager, ProfileError, ProfileAlreadyExistsError, ProfileNotFoundError
from src.core.browser_launcher import BrowserLauncher
from src.gui.create_profile_dialog import CreateProfileDialog
from src.gui.edit_profile_dialog import EditProfileDialog
from src.gui.process_monitor import ProcessMonitorWindow
from src.gui.process_monitor_service import ProcessMonitorService

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ProfileManagerGUI(ctk.CTk):
    """Main application window - Fixed layout"""
    
    def __init__(self, profile_manager: ProfileManager):
        super().__init__()
        
        self.profile_manager = profile_manager
        self.selected_profile = None
        self.profile_buttons = {}
        self.current_tab = "profiles"  # profiles, settings
        self.process_monitor_service = ProcessMonitorService()
        
        # Window setup
        self.title("Stealth Browser Manager")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        
        # Configure grid: 10% left buttons, 70% main, 20% right details
        self.grid_columnconfigure(0, weight=1)   # 10% - left buttons
        self.grid_columnconfigure(1, weight=7)   # 70% - main content
        self.grid_columnconfigure(2, weight=2)   # 20% - right details
        self.grid_rowconfigure(0, weight=1)
        
        self._create_widgets()
        self._refresh_profile_list()
        
    def _is_ui_valid(self):
        """Check if the UI is still valid for updates"""
        try:
            return (self.winfo_exists() and 
                   hasattr(self, 'profile_list_container') and 
                   hasattr(self, 'right_container') and
                   self.profile_list_container.winfo_exists() and
                   self.right_container.winfo_exists())
        except Exception:
            return False
            
    def _safe_destroy_children(self, parent_widget):
        """Safely destroy all children of a widget, handling pending events"""
        try:
            # Get all children first to avoid modification during iteration
            children = list(parent_widget.winfo_children())
            for widget in children:
                try:
                    # Unbind all events to prevent callbacks after destruction
                    widget.unbind("<Button-1>")
                    widget.unbind("<Button-3>")
                    
                    # Schedule destruction after all pending events are processed
                    self.after_idle(widget.destroy)
                except Exception:
                    # Widget may have already been destroyed
                    pass
        except Exception:
            # Parent widget may have been destroyed
            pass
        
    def _create_widgets(self):
        """Create all UI widgets"""
        # Left sidebar buttons (10%)
        self._create_left_sidebar()
        
        # Main content area (70%)
        self._create_main_content()
        
        # Right details area (20%)
        self._create_right_details()
        # Expand main area until a profile is selected
        self.main_container.grid_configure(columnspan=2)
    
    def _create_left_sidebar(self):
        """Create left sidebar with buttons"""
        sidebar = ctk.CTkFrame(self, width=120, corner_radius=0, fg_color="#1a1a1a")
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 1))
        sidebar.grid_propagate(False)
        
        # Logo/Title
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=80)
        title_frame.pack(fill="x", pady=(10, 20))
        
        ctk.CTkLabel(
            title_frame, 
            text="🦊", 
            font=ctk.CTkFont(size=28)
        ).pack(pady=(5, 0))
        
        ctk.CTkLabel(
            title_frame, 
            text="Browser", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack()
        
        # Navigation buttons
        self.profiles_btn = ctk.CTkButton(
            sidebar,
            text="Profiles",
            height=40,
            fg_color="#1a73e8" if self.current_tab == "profiles" else "transparent",
            hover_color="#0d62d9" if self.current_tab == "profiles" else "#2a2d2e",
            command=lambda: self.switch_tab("profiles")
        )
        self.profiles_btn.pack(fill="x", padx=10, pady=5)
        
        self.settings_btn = ctk.CTkButton(
            sidebar,
            text="Settings",
            height=40,
            fg_color="#1a73e8" if self.current_tab == "settings" else "transparent",
            hover_color="#0d62d9" if self.current_tab == "settings" else "#2a2d2e",
            command=lambda: self.switch_tab("settings")
        )
        self.settings_btn.pack(fill="x", padx=10, pady=5)
        
        # Spacer
        ctk.CTkFrame(sidebar, fg_color="transparent", height=20).pack()
        
        # Process monitor button at bottom
        monitor_btn = ctk.CTkButton(
            sidebar,
            text="🖥️ Monitor",
            height=35,
            fg_color="transparent",
            hover_color="#2a2d2e",
            command=self.open_process_monitor
        )
        monitor_btn.pack(side="bottom", fill="x", padx=10, pady=10)
    
    def _create_main_content(self):
        """Create main content area (70%)"""
        self.main_container = ctk.CTkFrame(self, fg_color="#1e1e1e")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=1)
        
        # Profiles tab content (default)
        self.profiles_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._create_profiles_tab()
        
        # Settings tab content (hidden initially)
        self.settings_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self._create_settings_tab()
        self.settings_frame.grid_forget()
        
        # Show profiles tab by default
        self.profiles_frame.pack(fill="both", expand=True)
    
    def _create_profiles_tab(self):
        """Create profiles tab content"""
        # Search bar at top
        search_frame = ctk.CTkFrame(self.profiles_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=20)
        
        # Search entry
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Search profiles by name or notes...",
            textvariable=self.search_var
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_var.trace_add("write", lambda *args: self._refresh_profile_list())
        
        # Create profile button
        create_btn = ctk.CTkButton(
            search_frame, 
            text="+ New Profile", 
            width=100,
            height=35,
            command=self.create_profile_dialog
        )
        create_btn.pack(side="right")
        
        # Profile list
        self.profile_list_container = ctk.CTkScrollableFrame(
            self.profiles_frame, 
            fg_color="transparent"
        )
        self.profile_list_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    def _create_settings_tab(self):
        """Create settings tab content"""
        # Simple placeholder for now
        settings_label = ctk.CTkLabel(
            self.settings_frame,
            text="Application Settings",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        settings_label.pack(pady=50)
        
        ctk.CTkLabel(
            self.settings_frame,
            text="Settings will be available in a future update",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack()
    
    def _create_right_details(self):
        """Create right details area (20%) - hidden initially"""
        self.right_container = ctk.CTkFrame(self, fg_color="#1a1a1a", width=240)
        self.right_container.grid(row=0, column=2, sticky="nsew", padx=(1, 0))
        self.right_container.grid_propagate(False)
        
        # Hide initially since no profile is selected
        self.right_container.grid_remove()
    
    def switch_tab(self, tab_name: str):
        """Switch between tabs"""
        self.current_tab = tab_name
        
        # Update button colors
        self.profiles_btn.configure(
            fg_color="#1a73e8" if tab_name == "profiles" else "transparent",
            hover_color="#0d62d9" if tab_name == "profiles" else "#2a2d2e"
        )
        self.settings_btn.configure(
            fg_color="#1a73e8" if tab_name == "settings" else "transparent",
            hover_color="#0d62d9" if tab_name == "settings" else "#2a2d2e"
        )
        
        # Switch content
        if tab_name == "profiles":
            self.settings_frame.pack_forget()
            self.profiles_frame.pack(fill="both", expand=True)
            # Show right details if profile is selected
            if self.selected_profile:
                self._show_right_details()
            else:
                self.right_container.grid_remove()
                # Expand main content when no profile selected
                self.main_container.grid_configure(columnspan=2)
        else:
            self.profiles_frame.pack_forget()
            self.settings_frame.pack(fill="both", expand=True)
            # Hide right details in settings tab
            self.right_container.grid_remove()
            # Expand main content when in settings
            self.main_container.grid_configure(columnspan=2)
    
    def _create_profile_row(self, profile_name: str, profile_data):
        """Create a profile row in the list"""
        row = ctk.CTkFrame(
            self.profile_list_container,
            fg_color="#2a2d2e",
            corner_radius=6
        )
        row.pack(fill="x", pady=6)
        
        # ВАЖНО: Фиксируем высоту строки
        row.grid_propagate(False)
        row.configure(height=60)
        
        # Store reference
        self.profile_buttons[profile_name] = row
        
        # Используем grid для точного контроля
        row.grid_columnconfigure(0, weight=1)  # левая часть (информация)
        row.grid_columnconfigure(1, weight=0)  # правая часть (кнопка)
        row.grid_rowconfigure(0, weight=1)
        
        # Left side: Profile info
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=0, sticky="nsew", padx=8, pady=2)
        info_frame.grid_propagate(False)
        info_frame.configure(height=26)  # чуть меньше чем родительская строка
        
        # Внутри info_frame тоже используем grid
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_rowconfigure(0, weight=1)
        info_frame.grid_rowconfigure(1, weight=1)
        
        # Profile name
        name_label = ctk.CTkLabel(
            info_frame,
            text=profile_name,
            font=ctk.CTkFont(size=18, weight="bold"),  # еще уменьшили
            anchor="w",
            height=12  # задаем высоту
        )
        name_label.grid(row=0, column=0, sticky="w", padx=0, pady=(1, 0))
        
        # Engine and last launch time
        engine = getattr(profile_data, 'engine', 'chromedriver')
        last_launched = getattr(profile_data, 'last_launched', '')
        last_time = last_launched[:10] if last_launched else 'Never'  # показываем только дату
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=f"{engine} • {last_time}",
            font=ctk.CTkFont(size=9),  # еще уменьшили
            text_color="gray",
            anchor="w",
            height=10  # задаем высоту
        )
        details_label.grid(row=1, column=0, sticky="w", padx=0, pady=(0, 1))
        
        # Right side: Start/Stop button
        is_running = BrowserLauncher.is_running(profile_name)
        
        if is_running:
            # Stop button (red)
            action_btn = ctk.CTkButton(
                row,
                text="⏹️ Stop",
                width=100,
                height=35,
                fg_color="#dc3545",
                hover_color="#c82333",
                command=lambda n=profile_name: self.stop_profile(n)
            )
        else:
            # Start button (green)
            action_btn = ctk.CTkButton(
                row,
                text="▶ Start",
                width=100,
                height=35,
                fg_color="#28a745",
                hover_color="#218838",
                command=lambda n=profile_name: self.start_profile(n)
            )
        
        action_btn.grid(row=0, column=1, sticky="ns", padx=(0, 8), pady=17)
        
        # Bind click to select profile (ignore clicks originating from action button)
        row.bind("<Button-1>", lambda e, n=profile_name: self._on_profile_row_click(e, n))
        info_frame.bind("<Button-1>", lambda e, n=profile_name: self._on_profile_row_click(e, n))
        name_label.bind("<Button-1>", lambda e, n=profile_name: self._on_profile_row_click(e, n))
        details_label.bind("<Button-1>", lambda e, n=profile_name: self._on_profile_row_click(e, n))
        
        # Context menu
        row.bind("<Button-3>", lambda e, n=profile_name: self._show_context_menu(e, n))
    
    def _refresh_profile_list(self):
        """Refresh the profile list with search filtering"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        # Clear current list with proper cleanup
        self._safe_destroy_children(self.profile_list_container)
        
        # Get all profiles
        try:
            profiles = self.profile_manager.list_profiles()
        except Exception:
            # Handle case where profile manager is not available
            return
        
        # Apply search filter
        try:
            search_term = self.search_var.get().strip().lower()
        except Exception:
            search_term = ""
            
        filtered_profiles = []
        
        for name, profile in profiles.items():
            if not search_term:
                filtered_profiles.append((name, profile))
            else:
                # Search in name
                if search_term in name.lower():
                    filtered_profiles.append((name, profile))
                # Search in notes
                elif profile.notes and search_term in profile.notes.lower():
                    filtered_profiles.append((name, profile))
        
        # Sort by name
        filtered_profiles.sort(key=lambda x: x[0])
        
        # Create profile rows
        for name, profile in filtered_profiles:
            # Check if UI is still valid before creating widgets
            if not self._is_ui_valid():
                return
            try:
                self._create_profile_row(name, profile)
            except Exception:
                # Skip profile if we can't create its row
                pass
    
    def select_profile(self, profile_name: str):
        """Select a profile"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
        self.selected_profile = profile_name
        self._show_right_details()
    
    def _show_right_details(self):
        """Show profile details in right panel"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        if not self.selected_profile or self.current_tab != "profiles":
            try:
                self.right_container.grid_remove()
                # Expand main content across columns 1-2 when no selection
                self.main_container.grid_configure(columnspan=2)
            except Exception:
                # Container may have been destroyed
                pass
            return
        
        # Clear right container with proper cleanup
        try:
            self._safe_destroy_children(self.right_container)
        except Exception:
            # Right container may have been destroyed
            return
        
        # Show container
        try:
            self.right_container.grid()
            # Shrink main content to make space for right panel
            self.main_container.grid_configure(columnspan=1)
        except Exception:
            # Container may have been destroyed
            return
        
        # Get profile data
        try:
            profile = self.profile_manager.get_profile(self.selected_profile)
            if not profile:
                return
        except Exception:
            # Profile manager may not be available
            return
        
        try:
            # Header with close button
            header_frame = ctk.CTkFrame(self.right_container, fg_color="transparent")
            header_frame.pack(fill="x", padx=10, pady=(10, 0))
            ctk.CTkButton(
                header_frame,
                text="✖",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color="#2a2d2e",
                command=self._close_right_details
            ).pack(side="right")
            
            # Scrollable container for details
            details_scroll = ctk.CTkScrollableFrame(self.right_container, fg_color="transparent")
            details_scroll.pack(fill="both", expand=True, padx=15, pady=15)
            
            # Header title
            ctk.CTkLabel(
                header_frame,
                text=profile.name,
                font=ctk.CTkFont(size=18, weight="bold")
            ).pack(side="left", padx=10)
            
            # Status
            is_running = BrowserLauncher.is_running(self.selected_profile)
            status_text = "🟢 Running" if is_running else "⚫ Stopped"
            status_color = "green" if is_running else "gray"
            
            ctk.CTkLabel(
                details_scroll,
                text=status_text,
                font=ctk.CTkFont(size=12),
                text_color=status_color
            ).pack(anchor="w", pady=(0, 20))
            
            # Info sections
            self._create_detail_section(details_scroll, "BASIC INFO", [
                ("Engine", getattr(profile, 'engine', 'chromedriver')),
                ("Created", profile.created[:10] if profile.created else "Unknown"),
                ("Size", f"{self.profile_manager.get_profile_size(self.selected_profile) / 1024:.1f} KB"),
            ])
            
            if profile.fingerprint:
                self._create_detail_section(details_scroll, "FINGERPRINT", [
                    ("Platform", profile.fingerprint.get('platform', 'N/A')),
                    ("Screen", f"{profile.fingerprint.get('screen_width', 'N/A')}×{profile.fingerprint.get('screen_height', 'N/A')}"),
                    ("Cores", str(profile.fingerprint.get('hardware_concurrency', 'N/A'))),
                    ("Memory", f"{profile.fingerprint.get('device_memory', 'N/A')} GB"),
                ])
            
            if profile.proxy:
                proxy_text = profile.proxy.get('server', 'N/A')
                if profile.proxy.get('username'):
                    proxy_text = f"{profile.proxy['username']}@{proxy_text}"
                
                self._create_detail_section(details_scroll, "PROXY", [
                    ("Server", proxy_text),
                ])
            
            # Notes section
            notes_frame = ctk.CTkFrame(details_scroll, fg_color="#2a2d2e", corner_radius=6)
            notes_frame.pack(fill="x", pady=(15, 0))
            
            ctk.CTkLabel(
                notes_frame,
                text="NOTES",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray"
            ).pack(anchor="w", padx=10, pady=(10, 5))
            
            notes_text = ctk.CTkTextbox(notes_frame, height=100, fg_color="transparent", border_width=0)
            notes_text.pack(fill="x", padx=10, pady=(0, 10))
            
            if profile.notes:
                notes_text.insert("1.0", profile.notes)
            # Enable inline editing and save on every change (supports Enter/newlines)
            notes_text.configure(state="normal")
            notes_text.bind("<KeyRelease>", lambda e: self._save_notes_live(e.widget))
            
            # Action buttons at bottom
            actions_frame = ctk.CTkFrame(details_scroll, fg_color="transparent")
            actions_frame.pack(fill="x", pady=(20, 10))
            
            if is_running:
                stop_btn = ctk.CTkButton(
                    actions_frame,
                    text="⏹️ Stop Browser",
                    fg_color="#dc3545",
                    hover_color="#c82333",
                    command=lambda: self.stop_profile(self.selected_profile)
                )
                stop_btn.pack(fill="x", pady=5)
            else:
                start_btn = ctk.CTkButton(
                    actions_frame,
                    text="▶ Start Browser",
                    fg_color="#28a745",
                    hover_color="#218838",
                    command=lambda: self.start_profile(self.selected_profile)
                )
                start_btn.pack(fill="x", pady=5)
            
            edit_btn = ctk.CTkButton(
                actions_frame,
                text="✏️ Edit Profile",
                command=lambda: self.edit_profile_dialog(self.selected_profile)
            )
            edit_btn.pack(fill="x", pady=5)
            
            folder_btn = ctk.CTkButton(
                actions_frame,
                text="📁 Open Folder",
                command=lambda: self._open_profile_folder(self.selected_profile)
            )
            folder_btn.pack(fill="x", pady=5)
        except Exception:
            # Details may not be creatable if UI elements were destroyed
            pass
    
    def _close_right_details(self):
        """Close the right details panel"""
        self.selected_profile = None
        self.right_container.grid_remove()
        # Expand main content when details are closed
        self.main_container.grid_configure(columnspan=2)
    
    def _save_notes_live(self, widget):
        """Save notes inline as the user types"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        if not self.selected_profile:
            return
        try:
            text = widget.get("1.0", "end-1c")
            self.profile_manager.update_profile(self.selected_profile, notes=text)
        except ProfileError as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Failed to save notes: {str(e)}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Unexpected error saving notes: {str(e)}")
    
    def _on_profile_row_click(self, event, profile_name: str):
        if isinstance(event.widget, ctk.CTkButton):
            return
        self.select_profile(profile_name)
    
    def _create_detail_section(self, parent, title: str, items: List[tuple]):
        """Create a detail section"""
        section_frame = ctk.CTkFrame(parent, fg_color="#2a2d2e", corner_radius=6)
        section_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        for label, value in items:
            item_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            item_frame.pack(fill="x", padx=10, pady=2)
            
            ctk.CTkLabel(
                item_frame,
                text=label,
                width=80,
                anchor="w",
                font=ctk.CTkFont(size=11)
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=str(value),
                text_color="lightgray",
                anchor="w"
            ).pack(side="left", fill="x", expand=True, padx=(10, 0))
    
    def _show_context_menu(self, event, profile_name: str):
        """Show context menu for profile"""
        menu = tk.Menu(self, tearoff=0)
        menu.configure(
            bg="#2b2b2b",
            fg="white",
            activebackground="#3d3d3d",
            activeforeground="white",
            bd=0,
            font=("Segoe UI", 10)
        )
        
        menu.add_command(
            label="Start Browser", 
            command=lambda: self.start_profile(profile_name)
        )
        menu.add_separator()
        menu.add_command(
            label="Edit", 
            command=lambda: self._edit_profile(profile_name)
        )
        menu.add_command(
            label="Duplicate", 
            command=lambda: self._duplicate_profile(profile_name)
        )
        menu.add_command(
            label="Rename", 
            command=lambda: self._rename_profile(profile_name)
        )
        menu.add_separator()
        menu.add_command(
            label="Open Folder", 
            command=lambda: self._open_profile_folder(profile_name)
        )
        menu.add_command(
            label="Delete", 
            command=lambda: self._delete_profile(profile_name)
        )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def start_profile(self, profile_name: str):
        """Start a browser profile"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        import tkinter.messagebox as mb
        
        try:
            profile = self.profile_manager.get_profile(profile_name)
            if not profile:
                mb.showerror("Error", f"Profile '{profile_name}' not found.")
                return
            
            state = profile.get_instance_state()
            if state['is_running']:
                mb.showinfo("Info", f"Profile '{profile_name}' is already running.")
                return
            
            try:
                profile.start_instance(
                    self.profile_manager,
                    headless=False,
                    restore_session=True
                )
                # Refresh once the process is registered (limited retries, no constant polling)
                try:
                    self.after(400, lambda n=profile_name: self._post_launch_refresh(n, retries=4))
                except Exception:
                    # Window may have been destroyed
                    pass
                self.process_monitor_service.start_monitor(
                    profile_name, 
                    self._refresh_profile_list, 
                    self._show_right_details, 
                    self.selected_profile
                )
            except Exception as e:
                mb.showerror("Error", str(e))
        except ProfileNotFoundError:
            mb.showerror("Error", f"Profile '{profile_name}' not found.")
        except ProfileError as e:
            mb.showerror("Error", f"Failed to start profile: {str(e)}")
        except Exception as e:
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _post_launch_refresh(self, profile_name: str, retries: int = 4):
        """Refresh list and details after launch with limited retries"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        if BrowserLauncher.is_running(profile_name):
            try:
                self._refresh_profile_list()
                if self.selected_profile == profile_name:
                    self._show_right_details()
            except Exception:
                # UI may have been destroyed
                pass
        elif retries > 0:
            try:
                self.after(400, lambda n=profile_name, r=retries-1: self._post_launch_refresh(n, r))
            except Exception:
                # Window may have been destroyed
                pass
    
    def stop_profile(self, profile_name: str):
        """Stop a browser profile"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        import tkinter.messagebox as mb
        
        try:
            profile = self.profile_manager.get_profile(profile_name)
            if not profile:
                mb.showerror("Error", f"Profile '{profile_name}' not found.")
                return
            
            state = profile.get_instance_state()
            if not state['is_running']:
                mb.showinfo("Info", f"Profile '{profile_name}' is not running.")
                return
            
            if mb.askyesno("Confirm", f"Stop browser for profile '{profile_name}'?"):
                success = profile.stop_instance()
                if success:
                    try:
                        self._refresh_profile_list()
                        if self.selected_profile == profile_name:
                            self._show_right_details()
                    except Exception:
                        # UI may have been destroyed
                        pass
                else:
                    mb.showerror("Error", "Failed to stop browser")
        except ProfileNotFoundError:
            mb.showerror("Error", f"Profile '{profile_name}' not found.")
        except ProfileError as e:
            mb.showerror("Error", f"Failed to stop profile: {str(e)}")
        except Exception as e:
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def create_profile_dialog(self):
        """Open create profile dialog"""
        CreateProfileDialog(self, self._on_profile_created)
    
    def _on_profile_created(self, result):
        """Handle profile creation"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        # Profile is already created by dialog; just refresh and select it
        try:
            self._refresh_profile_list()
            self.select_profile(result['name'])
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Failed to refresh profile list: {str(e)}")
    
    def edit_profile_dialog(self, profile_name: str = None):
        """Open edit profile dialog"""
        if not profile_name and self.selected_profile:
            profile_name = self.selected_profile
        
        if not profile_name:
            return
        
        try:
            profile = self.profile_manager.get_profile(profile_name)
            if not profile:
                import tkinter.messagebox as mb
                mb.showerror("Error", f"Profile '{profile_name}' not found.")
                return
            
            EditProfileDialog(self, profile, self._on_profile_updated)
        except ProfileNotFoundError:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Profile '{profile_name}' not found.")
        except ProfileError as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Failed to load profile: {str(e)}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _on_profile_updated(self, fingerprint, proxy, notes):
        """Handle profile update"""
        # Check if UI is still valid
        if not self._is_ui_valid():
            return
            
        if not self.selected_profile:
            return
        
        try:
            success = self.profile_manager.update_profile(
                self.selected_profile,
                fingerprint=fingerprint,
                proxy=proxy,
                notes=notes
            )
            
            if success:
                self._refresh_profile_list()
                self._show_right_details()
        except ProfileNotFoundError:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Profile '{self.selected_profile}' not found.")
        except ProfileError as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Failed to update profile: {str(e)}")
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _edit_profile(self, profile_name: str):
        """Edit profile from context menu"""
        self.select_profile(profile_name)
        self.edit_profile_dialog(profile_name)
    
    def _duplicate_profile(self, profile_name: str):
        """Duplicate profile from context menu"""
        import tkinter.messagebox as mb
        
        try:
            dialog = ctk.CTkInputDialog(
                text=f"Duplicate '{profile_name}' as:",
                title="Duplicate Profile"
            )
            new_name = dialog.get_input()
            
            if new_name:
                success = self.profile_manager.duplicate_profile(profile_name, new_name)
                if success:
                    self._refresh_profile_list()
                    self.select_profile(new_name)
        except ProfileNotFoundError:
            mb.showerror("Error", f"Profile '{profile_name}' not found.")
        except ProfileAlreadyExistsError:
            mb.showerror("Error", f"Profile '{new_name}' already exists.")
        except ProfileError as e:
            mb.showerror("Error", f"Failed to duplicate profile: {str(e)}")
        except Exception as e:
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _rename_profile(self, profile_name: str):
        """Rename profile from context menu"""
        import tkinter.messagebox as mb
        
        try:
            dialog = ctk.CTkInputDialog(
                text=f"Rename '{profile_name}' to:",
                title="Rename Profile"
            )
            new_name = dialog.get_input()
            
            if new_name:
                success = self.profile_manager.rename_profile(profile_name, new_name)
                if success:
                    self.selected_profile = new_name
                    self._refresh_profile_list()
                    self._show_right_details()
        except ProfileNotFoundError:
            mb.showerror("Error", f"Profile '{profile_name}' not found.")
        except ProfileAlreadyExistsError:
            mb.showerror("Error", f"Profile '{new_name}' already exists.")
        except ProfileError as e:
            mb.showerror("Error", f"Failed to rename profile: {str(e)}")
        except Exception as e:
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _open_profile_folder(self, profile_name: str):
        """Open profile folder from context menu"""
        import tkinter.messagebox as mb
        
        try:
            pdir = self.profile_manager.profile_dir(profile_name)
            if not pdir.exists():
                mb.showwarning("Warning", "Profile folder not found")
                return
            
            try:
                if sys.platform.startswith("win"):
                    os.startfile(str(pdir))
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(pdir)])
                else:
                    subprocess.Popen(["xdg-open", str(pdir)])
            except Exception as e:
                mb.showerror("Error", f"Failed to open folder: {e}")
        except ProfileNotFoundError:
            mb.showerror("Error", f"Profile '{profile_name}' not found.")
        except ProfileError as e:
            mb.showerror("Error", f"Failed to locate profile: {str(e)}")
        except Exception as e:
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def _delete_profile(self, profile_name: str):
        """Delete profile from context menu"""
        import tkinter.messagebox as mb
        
        try:
            if not mb.askyesno("Confirm Delete",
                              f"Delete profile '{profile_name}' and all its data?\n\nThis cannot be undone."):
                return
            
            success = self.profile_manager.delete_profile(profile_name)
            if success:
                if self.selected_profile == profile_name:
                    self.selected_profile = None
                    self.right_container.grid_remove()
                    # Expand main content when nothing is selected
                    self.main_container.grid_configure(columnspan=2)
                self._refresh_profile_list()
        except ProfileNotFoundError:
            mb.showerror("Error", f"Profile '{profile_name}' not found.")
        except ProfileError as e:
            mb.showerror("Error", f"Failed to delete profile: {str(e)}")
        except Exception as e:
            mb.showerror("Error", f"Unexpected error: {str(e)}")
    
    def open_process_monitor(self):
        """Open process monitor window"""
        ProcessMonitorWindow(self)