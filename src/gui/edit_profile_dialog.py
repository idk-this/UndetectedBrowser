# edit_profile_dialog.py (обновленный для ручного редактирования)
"""
Edit Profile Dialog - Enhanced with manual editing
"""
import customtkinter as ctk
import threading
from typing import Optional, Callable

from src.utils.fingerprint_generator import FingerprintGenerator, BrowserFingerprint
from src.utils.proxy_manager import ProxyConfig, ProxyTester


class EditProfileDialog(ctk.CTkToplevel):
    """Edit profile dialog with manual fingerprint editing"""
    
    def __init__(self, parent, profile, on_save: Callable):
        super().__init__(parent)
        
        self.profile = profile
        self.on_save = on_save
        
        self.title(f"Edit Profile: {profile.name}")
        self.geometry("800x700")
        self.resizable(True, True)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self._load_current_settings()
        
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
            text=f"Edit Profile: {self.profile.name}",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 20))
        
        # Tab view
        self.tabview = ctk.CTkTabview(main_container)
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs
        self.tabview.add("Fingerprint")
        self.tabview.add("Proxy")
        self.tabview.add("Engine")
        self.tabview.add("Notes")
        
        # Configure tabs
        self._create_fingerprint_tab()
        self._create_proxy_tab()
        self._create_engine_tab()
        self._create_notes_tab()
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(15, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="Save Changes",
            command=self._save,
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
    
    def _create_fingerprint_tab(self):
        """Create Fingerprint tab with manual editing"""
        tab = self.tabview.tab("Fingerprint")
        
        # Generate button at top
        generate_btn = ctk.CTkButton(
            tab,
            text="🔄 Generate New Fingerprint",
            command=self._generate_fingerprint,
            height=35
        )
        generate_btn.pack(pady=(0, 15))
        
        # Scrollable frame for fingerprint fields
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True)
        
        # User Agent
        ua_frame = ctk.CTkFrame(scroll_frame, fg_color="#2a2d2e", corner_radius=6)
        ua_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            ua_frame,
            text="User Agent",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.ua_entry = ctk.CTkEntry(ua_frame)
        self.ua_entry.pack(fill="x", padx=10, pady=(0, 10))
        
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
        self.screen_width = ctk.CTkEntry(width_frame)
        self.screen_width.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # Screen height
        height_frame = ctk.CTkFrame(screen_frame, fg_color="transparent")
        height_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(height_frame, text="Height:", width=100).pack(side="left")
        self.screen_height = ctk.CTkEntry(height_frame)
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
        self.webgl_vendor = ctk.CTkEntry(vendor_frame)
        self.webgl_vendor.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        # WebGL renderer
        renderer_frame = ctk.CTkFrame(webgl_frame, fg_color="transparent")
        renderer_frame.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(renderer_frame, text="Renderer:", width=100).pack(side="left")
        self.webgl_renderer = ctk.CTkEntry(renderer_frame)
        self.webgl_renderer.pack(side="left", fill="x", expand=True, padx=(10, 0))
    
    def _create_proxy_tab(self):
        """Create Proxy tab"""
        tab = self.tabview.tab("Proxy")
        
        # Server
        ctk.CTkLabel(
            tab,
            text="Proxy Server:",
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
        
        # Test and clear buttons
        btn_frame = ctk.CTkFrame(tab, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        self.test_btn = ctk.CTkButton(
            btn_frame,
            text="Test Proxy",
            command=self._test_proxy,
            width=100
        )
        self.test_btn.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            btn_frame,
            text="Clear Proxy",
            command=self._clear_proxy,
            width=100
        ).pack(side="left")
        
        self.test_status = ctk.CTkLabel(tab, text="")
        self.test_status.pack(anchor="w", pady=(10, 0))
    
    def _create_engine_tab(self):
        """Create Engine tab"""
        tab = self.tabview.tab("Engine")
        
        # Current engine display
        ctk.CTkLabel(
            tab,
            text="Current Engine:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        current_engine = getattr(self.profile, 'engine', 'chromedriver')
        ctk.CTkLabel(
            tab,
            text=current_engine,
            font=ctk.CTkFont(size=14)
        ).pack(anchor="w", padx=10, pady=(0, 15))
        
        # Engine selection
        ctk.CTkLabel(
            tab,
            text="Select Engine:",
            font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        self.engine_var = ctk.StringVar(value=current_engine)
        
        engine_frame = ctk.CTkFrame(tab, fg_color="transparent")
        engine_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkRadioButton(engine_frame, text="ChromeDriver", variable=self.engine_var, value="chromedriver").pack(side="left", padx=5)
        # Future engines can be added here when implemented
        
        # Warning
        ctk.CTkLabel(
            tab,
            text="Note: Changing engine may affect profile compatibility",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(anchor="w", pady=(20, 0))
    
    def _create_notes_tab(self):
        """Create Notes tab"""
        tab = self.tabview.tab("Notes")
        
        self.notes_text = ctk.CTkTextbox(tab, height=400)
        self.notes_text.pack(fill="both", expand=True, pady=10)
    
    def _load_current_settings(self):
        """Load current profile settings"""
        if self.profile.fingerprint:
            fp = self.profile.fingerprint
            
            # User Agent
            self.ua_entry.insert(0, fp.get('user_agent', ''))
            
            # Screen
            self.screen_width.insert(0, str(fp.get('screen_width', '1920')))
            self.screen_height.insert(0, str(fp.get('screen_height', '1080')))
            
            # Hardware
            self.cpu_cores.set(str(fp.get('hardware_concurrency', '8')))
            self.memory.set(str(fp.get('device_memory', '8')))
            
            # Platform
            self.platform.set(fp.get('platform', 'Win32'))
            self.language.set(fp.get('language', 'en-US'))
            
            # WebGL
            self.webgl_vendor.insert(0, fp.get('webgl_vendor', 'Google Inc. (NVIDIA)'))
            self.webgl_renderer.insert(0, fp.get('webgl_renderer', 'ANGLE (NVIDIA GeForce GTX 1660 Ti)'))
        
        # Proxy
        if self.profile.proxy:
            proxy = self.profile.proxy
            self.proxy_server.insert(0, proxy.get('server', ''))
            self.proxy_user.insert(0, proxy.get('username', ''))
            self.proxy_pass.insert(0, proxy.get('password', ''))
        
        # Notes
        if self.profile.notes:
            self.notes_text.insert("1.0", self.profile.notes)
    
    def _generate_fingerprint(self):
        """Generate new fingerprint"""
        # Detect OS from platform
        platform = self.platform.get().lower()
        if 'win' in platform:
            os_type = 'windows'
        elif 'mac' in platform:
            os_type = 'macos'
        else:
            os_type = 'linux'
        
        # Generate with current user agent or new one
        current_ua = self.ua_entry.get().strip()
        fp = FingerprintGenerator.generate(os_type, current_ua)
        
        # Update fields
        self.ua_entry.delete(0, 'end')
        self.ua_entry.insert(0, fp.user_agent)
        
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
    
    def _clear_proxy(self):
        """Clear proxy settings"""
        self.proxy_server.delete(0, 'end')
        self.proxy_user.delete(0, 'end')
        self.proxy_pass.delete(0, 'end')
        self.test_status.configure(text="")
    
    def _save(self):
        """Save changes"""
        try:
            # Build fingerprint from manual settings
            fingerprint = BrowserFingerprint(
                user_agent=self.ua_entry.get().strip(),
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
                webgl_vendor=self.webgl_vendor.get(),
                webgl_renderer=self.webgl_renderer.get()
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
        
        # Get engine
        engine = self.engine_var.get()
        
        # Save
        # We need to modify profile_manager to accept engine parameter
        success = self.master.profile_manager.update_profile(
            self.profile.name,
            fingerprint=fingerprint,
            proxy=proxy,
            notes=notes,
            engine=engine
        )
        
        if success:
            self.on_save(fingerprint, proxy, notes)
            self.destroy()
        else:
            self.test_status.configure(text="Failed to save profile", text_color="red")
