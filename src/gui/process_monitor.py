# process_monitor.py
"""
Process Monitor for tracking browser instances
"""
import customtkinter as ctk
import tkinter.messagebox as mb
from typing import Callable

from src.core.browser_launcher import BrowserLauncher


class ProcessMonitorWindow(ctk.CTkToplevel):
    """Process monitor window"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
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
        """Create monitor widgets"""
        main_frame = ctk.CTkFrame(self, fg_color="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="Process Monitor",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Refresh",
            width=100,
            command=self._refresh
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🗑️ Kill All",
            width=100,
            fg_color="#ea4335",
            hover_color="#d32f2f",
            command=self._kill_all
        ).pack(side="left", padx=5)
        
        # Table
        table_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True)
        
        # Table header
        header_frame = ctk.CTkFrame(table_frame, fg_color="#2a2d2e", height=40)
        header_frame.pack(fill="x")
        
        headers = [
            ("Profile", 200),
            ("PID", 100),
            ("Status", 100),
            ("Uptime", 100),
            ("CPU %", 80),
            ("Memory", 100),
            ("Actions", 100)
        ]
        
        for text, width in headers:
            lbl = ctk.CTkLabel(
                header_frame,
                text=text,
                font=ctk.CTkFont(weight="bold"),
                width=width
            )
            lbl.pack(side="left", padx=10, pady=10)
        
        # Process list
        self.process_list = ctk.CTkScrollableFrame(
            table_frame, 
            fg_color="transparent",
            height=300
        )
        self.process_list.pack(fill="both", expand=True, pady=(1, 0))
    
    def _refresh(self):
        """Refresh process list"""
        # Clear current list
        for widget in self.process_list.winfo_children():
            widget.destroy()
        
        # Get active processes
        processes = BrowserLauncher.get_active_processes()
        
        if not processes:
            ctk.CTkLabel(
                self.process_list,
                text="No running processes",
                text_color="gray"
            ).pack(pady=50)
            return
        
        # Add each process
        for profile_name, process in processes.items():
            self._add_process_row(profile_name, process)
    
    def _add_process_row(self, profile_name: str, process):
        """Add process row"""
        row = ctk.CTkFrame(self.process_list, height=50, fg_color="#2a2d2e")
        row.pack(fill="x", pady=1)
        
        # Profile name
        ctk.CTkLabel(
            row,
            text=profile_name,
            width=200
        ).place(x=10, y=15)
        
        # PID
        ctk.CTkLabel(
            row,
            text=str(process.pid),
            width=100
        ).place(x=210, y=15)
        
        # Status
        status = "Running" if process.is_alive() else "Stopped"
        status_color = "green" if status == "Running" else "red"
        ctk.CTkLabel(
            row,
            text=status,
            text_color=status_color,
            width=100
        ).place(x=310, y=15)
        
        # Uptime
        ctk.CTkLabel(
            row,
            text=process.get_uptime(),
            width=100
        ).place(x=410, y=15)
        
        # CPU
        cpu = process.get_cpu_percent()
        ctk.CTkLabel(
            row,
            text=f"{cpu:.1f}%",
            text_color="red" if cpu > 50 else "white",
            width=80
        ).place(x=510, y=15)
        
        # Memory
        mem = process.get_memory_usage()
        ctk.CTkLabel(
            row,
            text=f"{mem:.0f} MB",
            text_color="red" if mem > 1000 else "white",
            width=100
        ).place(x=590, y=15)
        
        # Kill button
        kill_btn = ctk.CTkButton(
            row,
            text="Kill",
            width=80,
            height=30,
            fg_color="#ea4335",
            hover_color="#d32f2f",
            command=lambda p=profile_name: self._kill_process(p)
        )
        kill_btn.place(x=690, y=10)
    
    def _kill_process(self, profile_name: str):
        """Kill specific process"""
        if mb.askyesno("Confirm", f"Kill process for '{profile_name}'?"):
            success = BrowserLauncher.kill_process(profile_name)
            if success:
                self._refresh()
    
    def _kill_all(self):
        """Kill all processes"""
        processes = BrowserLauncher.get_active_processes()
        if not processes:
            return
        
        if mb.askyesno("Confirm", f"Kill all {len(processes)} processes?"):
            for profile_name in list(processes.keys()):
                BrowserLauncher.kill_process(profile_name)
            self._refresh()