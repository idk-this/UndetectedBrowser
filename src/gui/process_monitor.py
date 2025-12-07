# process_monitor.py
"""
Process Monitor for tracking browser instances
"""
import customtkinter as ctk
import tkinter.messagebox as mb
from typing import Callable

from src.core.browser_launcher import BrowserLauncher
from src.core.profile_manager import ProfileManager, ProfileError

class ProcessMonitorWindow(ctk.CTkToplevel):
    """Process monitor window"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parent = parent
        
        self.title("Process Monitor")
        self.geometry("900x500")
        
        # Make modal
        self.transient(parent)
        
        self._create_widgets()
        self._refresh()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create UI widgets"""
        # Header
        header_frame = ctk.CTkFrame(self, height=50)
        header_frame.pack(fill="x", padx=20, pady=20)
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="Running Processes",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            header_frame,
            text="Refresh",
            width=80,
            command=self._refresh
        )
        self.refresh_btn.pack(side="right")
        
        # Process list
        self.process_list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=300
        )
        self.process_list.pack(fill="both", expand=True, pady=(1, 0))
    
    def _refresh(self):
        """Refresh process list"""
        # Clear current list
        for widget in self.process_list.winfo_children():
            widget.destroy()
        
        # Get all instances from BrowserLauncher
        instances = BrowserLauncher.get_active_processes()
        running_instances = {name: process for name, process in instances.items() if process.is_alive()}
        
        if not running_instances:
            ctk.CTkLabel(
                self.process_list,
                text="No running processes",
                text_color="gray"
            ).pack(pady=50)
            return
        
        # Add each process
        for profile_name, process in running_instances.items():
            # Create process item frame
            item_frame = ctk.CTkFrame(self.process_list, height=60)
            item_frame.pack(fill="x", pady=2)
            item_frame.pack_propagate(False)
            
            # Profile name
            ctk.CTkLabel(
                item_frame,
                text=profile_name,
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            ).place(x=15, y=10)
            
            # PID
            ctk.CTkLabel(
                item_frame,
                text=f"PID: {process.pid}",
                text_color="gray",
                anchor="w"
            ).place(x=15, y=35)
            
            # Uptime
            ctk.CTkLabel(
                item_frame,
                text=process.get_uptime(),
                text_color="gray",
                anchor="w"
            ).place(x=120, y=35)
            
            # Kill button
            kill_btn = ctk.CTkButton(
                item_frame,
                text="Kill",
                width=60,
                height=25,
                fg_color="#ea4335",
                hover_color="#d33d2d",
                command=lambda name=profile_name: self._kill_process(name)
            )
            kill_btn.place(relx=1.0, x=-15, y=17, anchor="e")
    
    def _kill_process(self, profile_name: str):
        """Kill a running process"""
        if mb.askyesno("Confirm Kill", f"Kill process for profile '{profile_name}'?"):
            try:
                success = BrowserLauncher.kill_process(profile_name)
                if success:
                    mb.showinfo("Success", f"Process for profile '{profile_name}' killed")
                else:
                    mb.showerror("Error", f"Failed to kill process for profile '{profile_name}'")
                self._refresh()
            except ProfileError as e:
                mb.showerror("Error", f"Failed to kill process: {str(e)}")
            except Exception as e:
                mb.showerror("Error", f"Unexpected error: {str(e)}")