# UndetectedBrowser

A stealth browser automation tool with advanced profile management and fingerprint spoofing capabilities. Built with Python and CustomTkinter, UndetectedBrowser provides a user-friendly GUI for managing multiple browser profiles with persistent sessions and undetectable browser fingerprints.

## Features

- 🎭 **Advanced Fingerprint Spoofing** - Randomized browser fingerprints to avoid detection
- 👤 **Multi-Profile Management** - Create and manage multiple isolated browser profiles
- 🔄 **Session Persistence** - Automatically saves and restores tabs across browser sessions
- 🔌 **Proxy Support** - Configure proxies for each profile individually
- 🎨 **Modern GUI** - Clean and intuitive interface with dark theme
- 🔒 **Isolated Environments** - Each profile runs in a completely isolated environment
- 💾 **Persistent Storage** - Browser data, cookies, and extensions persist across sessions
- 🖥️ **Process Monitoring** - Real-time monitoring of running browser instances

## Architecture

### Project Structure

```
UndetectedBrowser/
├── src/
│   ├── core/              # Core business logic
│   │   ├── engines/       # Browser engine implementations
│   │   │   ├── engine_base.py
│   │   │   └── chromedriver_engine.py
│   │   ├── browser_launcher.py
│   │   └── profile_manager.py
│   ├── gui/               # User interface components
│   │   ├── main_window.py
│   │   ├── create_profile_dialog.py
│   │   ├── edit_profile_dialog.py
│   │   ├── process_monitor.py
│   │   └── process_monitor_service.py
│   ├── utils/             # Utility modules
│   │   ├── fingerprint_generator.py
│   │   └── proxy_manager.py
│   ├── config.py
│   ├── config_manager.py
│   └── __init__.py
├── profiles/              # Profile data (not tracked in git)
├── main.py               # Application entry point
└── requirements.txt
```

### Key Components

- **Browser Launcher** - Manages browser process lifecycle and session restoration
- **Profile Manager** - Handles CRUD operations for browser profiles
- **Fingerprint Generator** - Creates randomized browser fingerprints
- **Process Monitor** - Tracks and manages running browser instances
- **Process Monitor Service** - Background service for monitoring browser processes
- **Engine System** - Pluggable architecture for different browser automation libraries
- **Configuration Manager** - Centralized configuration management system


## Installation

### Prerequisites

- Python 3.8 or higher
- Google Chrome or Chromium browser installed

### Setup

1. Clone the repository:
```bash
git clone https://github.com/idk-this/UndetectedBrowser.git
cd UndetectedBrowser
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Usage

### Creating a Profile

1. Click the **"Create Profile"** button
2. Enter a profile name
3. (Optional) Configure proxy settings
4. (Optional) Customize fingerprint parameters
5. Click **"Create"**

### Starting a Browser Session

1. Select a profile from the list
2. Click the **"Start"** button
3. The browser will launch with your saved session
4. All tabs and cookies are automatically restored

### Managing Profiles

- **Edit Profile** - Click the profile card to view details, then use the edit button
- **Delete Profile** - Select a profile and click the delete button
- **View Running Status** - Active browsers are highlighted in the interface

### Session Management

- **Auto-Save** - Sessions are automatically saved when you close the browser
- **Tab Restoration** - All open tabs are restored when you start the profile again
- **Persistent Data** - Cookies, local storage, and extensions persist across sessions

## Configuration

### Fingerprint Settings

The fingerprint generator randomizes:
- User-Agent strings
- WebGL renderer information
- Canvas fingerprints
- Screen resolution and color depth
- Timezone and language settings
- Hardware concurrency
- Device memory

### Proxy Configuration

Supported proxy types:
- HTTP/HTTPS proxies
- SOCKS4/SOCKS5 proxies
- Authentication support

## Technical Details

### Browser Engine

Currently supports:
- **ChromeDriver Engine** - Uses undetected-chromedriver for stealth automation

The architecture allows for easy integration of additional engines in the future.

### Session Persistence

Sessions are saved using Chrome DevTools Protocol (CDP):
- `Target.getTargets` - Lists all open tabs without switching focus
- Preserves tab order and state
- Saves URLs and navigation history

### Fingerprint Evasion

Implements multiple techniques to avoid detection:
- JavaScript property override injection
- WebDriver flag concealment
- Chrome automation detection bypass
- Navigator property randomization

## Troubleshooting

### Browser doesn't start
- Ensure Chrome/Chromium is installed
- Check that the ChromeDriver version matches your Chrome version
- Verify proxy settings if configured

### Tabs not restoring
- Check that `last_session.json` exists in the profile directory
- Ensure the browser was properly closed (not force-killed)

### Fingerprint detection
- Try generating a new profile with fresh fingerprint
- Ensure all stealth plugins are loaded

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Development

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is provided as-is for educational purposes. Please use responsibly and in accordance with applicable laws and website terms of service.

## Disclaimer

This tool is intended for legitimate browser automation tasks, testing, and privacy protection. Users are responsible for ensuring their use complies with all applicable laws and regulations. The authors are not responsible for any misuse of this software.

## Acknowledgments

- Built with [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- Modern CustomTkinter user interface
- PyQt5 for the graphical interface

## Roadmap

- [ ] Support for Firefox engine
- [ ] Extension management interface
- [ ] Profile import/export functionality
- [ ] Advanced fingerprint customization
- [ ] Cloud profile synchronization
- [ ] Automated testing framework

---

**Note**: The `profiles/` directory is automatically created when you create your first profile. This directory is excluded from version control to protect your privacy and browser data.
