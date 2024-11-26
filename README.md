# KeepAwake

KeepAwake is a lightweight Python-based utility designed to prevent your computer from going into sleep mode or locking the screen due to inactivity. It achieves this by periodically simulating a key press and ensuring system awake states. Additionally, it runs unobtrusively in the system tray with an easy-to-use context menu for basic control.

---

## Features
- **Prevent Sleep**: Uses system calls to prevent the system from sleeping or the display from turning off.
- **Simulated Key Presses**: Periodically presses a configurable key to maintain activity.
- **System Tray Integration**: Runs in the system tray for seamless interaction.
- **Customizable Configuration**: Allows users to configure key press intervals and the key to simulate.
- **Monitor Detection**: Detects connected monitors and ensures the system remains active when monitors are disconnected.

---

## Installation
1. **Dependencies**: Ensure the following Python libraries are installed:
   ```
   pip install pywin32 tendo
   ```
2. **Run the Script**: Execute the script using Python:
   ```
   python keep_awake.py
   ```
3. **System Tray**: The application will minimize to the system tray upon running.

---

## Configuration
The configuration file (`keep_awake_config.json`) is generated automatically in the script's directory if it does not already exist. Edit the file to customize the following settings:
- `min_interval`: Minimum interval (in seconds) between simulated key presses.
- `max_interval`: Maximum interval (in seconds) between simulated key presses.
- `key_code`: Virtual-Key code of the key to simulate (default: Left Shift).

Example:
```json
{
    "min_interval": 60,
    "max_interval": 360,
    "key_code": 160
}
```

---

## How to Use
1. **Start the Application**: Run the script. It will minimize to the system tray.
2. **Context Menu**: Right-click the system tray icon for options.
3. **Exit**: Select "Exit" from the context menu to close the application.

---

## Logging
The application logs activity and errors to `keep_awake.log` in the script's directory. Use this log to monitor the application's behavior or debug issues.

Enjoy a worry-free active system experience!
