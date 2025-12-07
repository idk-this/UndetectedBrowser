# create_profile_dialog.py
"""
Create Profile Dialog - Enhanced with manual fingerprint editing
"""
import customtkinter as ctk
import threading
from typing import Optional, Callable

from src.utils.fingerprint_generator import FingerprintGenerator
from src.utils.proxy_manager import ProxyConfig, ProxyTester


class CreateProfileDialog(ctk.CTkToplevel):
    """Create profile dialog with manual fingerprint editing"""
    
    def __init__(self, parent, on_create: Callable):
        super().__init__(parent)
        
        self.on_create = on_create
        self.fingerprint = None
        
        self.title("Create New Profile")
        self.geometry("800x700")
        self.resizable(True, True)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            main_container,
            text="Create New Profile",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))
        
        # Profile name
        name_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        name_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            name_frame,
            text="Profile Name:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.name_entry = ctk.CTkEntry(name_frame)
        self.name_entry.pack(fill="x")
        
        # Tab view
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs
        self.tabview.add("General")
        self.tabview.add("Fingerprint")
        self.tabview.add("Proxy")
        
        # Configure tabs
        self._create_general_tab()
        self._create_fingerprint_tab()
        self._create_proxy_tab()
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(15, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="Create Profile",
            command=self._create_profile,
            height=40,
            fg_color="#1a73e8",
            hover_color="#0d62d9"
        ).pack(side="right", padx=(10, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            height=40
        ).pack(side="right")
    
    def _create_general_tab(self):
        """Create General tab"""
        tab = self.tabview.tab("General")
        
        # OS Type
        ctk.CTkLabel(
            tab,
            text="Operating System:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.os_var = ctk.StringVar(value="windows")
        
        os_frame = ctk.CTkFrame(tab, fg_color="transparent")
        os_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkRadioButton(os_frame, text="Windows", variable=self.os_var, value="windows").pack(side="left", padx=5)
        ctk.CTkRadioButton(os_frame, text="macOS", variable=self.os_var, value="macos").pack(side="left", padx=5)
        ctk.CTkRadioButton(os_frame, text="Linux", variable=self.os_var, value="linux").pack(side="left", padx=5)
        
        # Browser Engine
        ctk.CTkLabel(
            tab,
            text="Browser Engine:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.engine_var = ctk.StringVar(value="chromedriver")
        
        engine_frame = ctk.CTkFrame(tab, fg_color="transparent")
        engine_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkRadioButton(engine_frame, text="ChromeDriver", variable=self.engine_var, value="chromedriver").pack(side="left", padx=5)
        # Future engines can be added here when implemented
        
        # User Agent
        ctk.CTkLabel(
            tab,
            text="User Agent:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        ua_frame = ctk.CTkFrame(tab, fg_color="transparent")
        ua_frame.pack(fill="x", pady=(0, 15))
        
        self.ua_var = ctk.StringVar(value="auto")
        ctk.CTkRadioButton(ua_frame, text="Auto-generate", variable=self.ua_var, value="auto",
                          command=self._toggle_ua_fields).pack(anchor="w")
        ctk.CTkRadioButton(ua_frame, text="Custom", variable=self.ua_var, value="custom",
                          command=self._toggle_ua_fields).pack(anchor="w", pady=(5, 0))
        
        self.custom_ua_entry = ctk.CTkEntry(ua_frame, placeholder_text="Enter custom user agent")
        self.custom_ua_entry.pack(fill="x", pady=(5, 0))
        self.custom_ua_entry.configure(state="disabled")
        
        # Notes
        ctk.CTkLabel(
            tab,
            text="Notes:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.notes_text = ctk.CTkTextbox(tab, height=80)
        self.notes_text.pack(fill="x")
    
    def _create_fingerprint_tab(self):
        """Create Fingerprint tab with manual editing"""
        tab = self.tabview.tab("Fingerprint")
        
        # Generate button at top
        generate_btn = ctk.CTkButton(
            tab,
            text="🔄 Generate Random Fingerprint",
            command=self._generate_fingerprint,
            height=35
        )
        generate_btn.pack(pady=(0, 15))
        
        # Scrollable frame for fingerprint fields
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True)
        
        # Screen settings
        screen_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2d2e", corner_radius=6)
        screen_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            screen_frame,
            text="Screen Settings",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Screen width
        width_frame = ctk.CTkFrame(screen_frame, fg_color="transparent")
        width_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(width_frame, text="Width:", width=100).pack(side="left")
        self.screen_width = ctk.CTkEntry(width_frame, placeholder_text="1920")
        self.screen_width.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Screen height
        height_frame = ctk.CTkFrame(screen_frame, fg_color="transparent")
        height_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(height_frame, text="Height:", width=100).pack(side="left")
        self.screen_height = ctk.CTkEntry(height_frame, placeholder_text="1080")
        self.screen_height.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Hardware settings
        hardware_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2d2e", corner_radius=6)
        hardware_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            hardware_frame,
            text="Hardware Settings",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # CPU cores
        cores_frame = ctk.CTkFrame(hardware_frame, fg_color="transparent")
        cores_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(cores_frame, text="CPU Cores:", width=100).pack(side="left")
        self.cpu_cores = ctk.CTkOptionMenu(cores_frame, values=["2", "4", "8", "12", "16"])
        self.cpu_cores.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Memory
        memory_frame = ctk.CTkFrame(hardware_frame, fg_color="transparent")
        memory_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(memory_frame, text="Memory (GB):", width=100).pack(side="left")
        self.memory = ctk.CTkOptionMenu(memory_frame, values=["2", "4", "8", "16", "32"])
        self.memory.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Platform settings
        platform_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2d2e", corner_radius=6)
        platform_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            platform_frame,
            text="Platform Settings",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Platform
        platform_type_frame = ctk.CTkFrame(platform_frame, fg_color="transparent")
        platform_type_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(platform_type_frame, text="Platform:", width=100).pack(side="left")
        self.platform = ctk.CTkOptionMenu(platform_type_frame, 
                                         values=["Win32", "MacIntel", "Linux x86_64"])
        self.platform.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Language
        language_frame = ctk.CTkFrame(platform_frame, fg_color="transparent")
        language_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(language_frame, text="Language:", width=100).pack(side="left")
        self.language = ctk.CTkOptionMenu(language_frame, 
                                         values=["en-US", "ru-RU", "de-DE", "fr-FR", "es-ES"])
        self.language.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # WebGL settings
        webgl_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2d2e", corner_radius=6)
        webgl_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            webgl_frame,
            text="WebGL Settings",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # WebGL vendor
        vendor_frame = ctk.CTkFrame(webgl_frame, fg_color="transparent")
        vendor_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(vendor_frame, text="Vendor:", width=100).pack(side="left")
        self.webgl_vendor = ctk.CTkEntry(vendor_frame, placeholder_text="Google Inc. (NVIDIA)")
        self.webgl_vendor.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # WebGL renderer
        renderer_frame = ctk.CTkFrame(webgl_frame, fg_color="transparent")
        renderer_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(renderer_frame, text="Renderer:", width=100).pack(side="left")
        self.webgl_renderer = ctk.CTkEntry(renderer_frame, 
                                          placeholder_text="ANGLE (NVIDIA GeForce GTX 1660 Ti)")
        self.webgl_renderer.pack(side="left", fill="x", expand=True, padx=(10, 0))
    
    def _create_proxy_tab(self):
        """Create Proxy tab"""
        tab = self.tabview.tab("Proxy")
        
        # Server
        ctk.CTkLabel(
            tab,
            text="Proxy Server (optional):",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.proxy_server = ctk.CTkEntry(
            tab,
            placeholder_text="host:port or http://host:port"
        )
        self.proxy_server.pack(fill="x", pady=(0, 15))
        
        # Username
        ctk.CTkLabel(
            tab,
            text="Username (optional):",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.proxy_user = ctk.CTkEntry(tab)
        self.proxy_user.pack(fill="x", pady=(0, 15))
        
        # Password
        ctk.CTkLabel(
            tab,
            text="Password (optional):",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.proxy_pass = ctk.CTkEntry(tab, show="*")
        self.proxy_pass.pack(fill="x", pady=(0, 15))
        
        # Test button
        self.test_btn = ctk.CTkButton(
            tab,
            text="Test Proxy Connection",
            command=self._test_proxy
        )
        self.test_btn.pack(pady=(10, 0))
        
        self.test_status = ctk.CTkLabel(tab, text="")
        self.test_status.pack(pady=(5, 0))
    
    def _toggle_ua_fields(self):
        """Toggle user agent fields"""
        if self.ua_var.get() == "auto":
            self.custom_ua_entry.configure(state="disabled")
        else:
            self.custom_ua_entry.configure(state="normal")
    
    def _generate_fingerprint(self):
        """Generate random fingerprint and fill fields"""
        os_type = self.os_var.get()
        fp = FingerprintGenerator.generate(os_type)
        
        # Fill fields
        self.screen_width.delete(0, 'end')
        self.screen_width.insert(0, str(fp.screen_width))
        
        self.screen_height.delete(0, 'end')
        self.screen_height.insert(0, str(fp.screen_height))
        
        self.cpu_cores.set(str(fp.hardware_concurrency))
        self.memory.set(str(fp.device_memory))
        self.platform.set(fp.platform)
        self.language.set(fp.language)
        self.webgl_vendor.delete(0, 'end')
        self.webgl_vendor.insert(0, fp.webgl_vendor)
        self.webgl_renderer.delete(0, 'end')
        self.webgl_renderer.insert(0, fp.webgl_renderer)
        
        # Set user agent if auto
        if self.ua_var.get() == "auto":
            self.custom_ua_entry.delete(0, 'end')
            self.custom_ua_entry.insert(0, fp.user_agent)
    
    def _test_proxy(self):
        """Test proxy connection"""
        server = self.proxy_server.get().strip()
        if not server:
            self.test_status.configure(text="Enter proxy server", text_color="orange")
            return
        
        proxy = ProxyConfig(
            server=server,
            username=self.proxy_user.get().strip() or None,
            password=self.proxy_pass.get().strip() or None
        )
        
        self.test_btn.configure(state="disabled")
        self.test_status.configure(text="Testing...", text_color="gray")
        
        def test_thread():
            result = ProxyTester.test_proxy(proxy)
            
            def update_ui():
                if result["success"]:
                    self.test_status.configure(
                        text=f"✓ Connected ({result['latency']}ms)",
                        text_color="green"
                    )
                else:
                    self.test_status.configure(
                        text=f"✗ Failed: {result['error']}",
                        text_color="red"
                    )
                self.test_btn.configure(state="normal")
            
            self.after(0, update_ui)
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def _create_profile(self):
        """Create the profile"""
        name = self.name_entry.get().strip()
        if not name:
            self.test_status.configure(text="Enter profile name", text_color="orange")
            return
        
        # Get user agent
        custom_ua = None
        if self.ua_var.get() == "custom":
            custom_ua = self.custom_ua_entry.get().strip() or None
        
        # Create fingerprint from manual settings
        try:
            from src.utils.fingerprint_generator import BrowserFingerprint
            
            fingerprint = BrowserFingerprint(
                user_agent=custom_ua or FingerprintGenerator.generate_user_agent(self.os_var.get()),
                platform=self.platform.get(),
                vendor="Google Inc.",
                renderer="Google Inc. (NVIDIA)",
                language=self.language.get(),
                languages=[self.language.get(), self.language.get()[:2]],
                screen_width=int(self.screen_width.get() or 1920),
                screen_height=int(self.screen_height.get() or 1080),
                viewport_width=int(self.screen_width.get() or 1920) - 10,
                viewport_height=int(self.screen_height.get() or 1080) - 100,
                hardware_concurrency=int(self.cpu_cores.get()),
                device_memory=int(self.memory.get()),
                color_depth=24,
                timezone="Europe/Kiev",
                webgl_vendor=self.webgl_vendor.get() or "Google Inc. (NVIDIA)",
                webgl_renderer=self.webgl_renderer.get() or "ANGLE (NVIDIA GeForce GTX 1660 Ti)"
            )
        except ValueError as e:
            self.test_status.configure(text=f"Invalid fingerprint: {e}", text_color="red")
            return
        
        # Get proxy
        proxy = None
        server = self.proxy_server.get().strip()
        if server:
            proxy = ProxyConfig(
                server=server,
                username=self.proxy_user.get().strip() or None,
                password=self.proxy_pass.get().strip() or None
            )
        
        # Get notes
        notes = self.notes_text.get("1.0", "end-1c").strip()
        
        # We need to modify profile_manager to accept fingerprint directly
        # For now, we'll create a custom version
        result = {
            'name': name,
            'os_type': self.os_var.get(),
            'custom_user_agent': custom_ua,
            'fingerprint': fingerprint,
            'proxy': proxy,
            'notes': notes,
            'engine': self.engine_var.get()
        }
        
        # Call the modified create_profile function
        success = self.master.profile_manager.create_profile_with_fingerprint(**result)
        if success:
            self.on_create({'name': name})
            self.destroy()
        else:
            self.test_status.configure(text="Failed to create profile", text_color="red")