import ctypes
import time
import random
import threading
import sys
import os
import logging
import json
import tkinter as tk
from tkinter import messagebox
from tkinter import Menu
from ctypes import wintypes
from win32api import GetModuleHandle
import win32con
import win32gui_struct
import win32gui

# Constants to prevent sleep mode
ES_CONTINUOUS       = 0x80000000
ES_SYSTEM_REQUIRED  = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

# Load Windows libraries
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Constants for keyboard input
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_LSHIFT = 0xA0  # Virtual-Key code for the left Shift key

# Define structures for keyboard input
wintypes.ULONG_PTR = wintypes.WPARAM

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk',         wintypes.WORD),
        ('wScan',       wintypes.WORD),
        ('dwFlags',     wintypes.DWORD),
        ('time',        wintypes.DWORD),
        ('dwExtraInfo', wintypes.ULONG_PTR),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [('ki', KEYBDINPUT)]
    _anonymous_ = ('_input',)
    _fields_ = [
        ('type',   wintypes.DWORD),
        ('_input', _INPUT),
    ]

# Exception handling and logging setup
LOG_FILENAME = 'keep_awake.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
CONFIG_FILE = 'keep_awake_config.json'

default_config = {
    "min_interval": 60,
    "max_interval": 360,
    "key_code": VK_LSHIFT
}

def load_config():
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            logging.info("Configuration loaded successfully.")
            return config
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            return default_config
    else:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f)
        logging.info("Default configuration file created.")
        return default_config

config = load_config()

# Singleton enforcement
def check_single_instance():
    from tendo import singleton
    try:
        me = singleton.SingleInstance()
        logging.info("No other instances detected.")
    except singleton.SingleInstanceException:
        logging.error("Another instance is already running.")
        sys.exit()

check_single_instance()

# Function to simulate key press
def PressKey(hexKeyCode):
    x = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=hexKeyCode,
            dwFlags=0,
        )
    )
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    logging.debug(f"Key {hexKeyCode} pressed.")

# Function to simulate key release
def ReleaseKey(hexKeyCode):
    x = INPUT(
        type=INPUT_KEYBOARD,
        ki=KEYBDINPUT(
            wVk=hexKeyCode,
            dwFlags=KEYEVENTF_KEYUP,
        )
    )
    user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    logging.debug(f"Key {hexKeyCode} released.")

# Function to prevent the system from going into sleep mode
def keep_system_awake():
    kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
    logging.debug("System sleep prevented.")

# Monitor detection
def monitors_connected():
    return user32.GetSystemMetrics(80)  # SM_CMONITORS

# System Tray Icon Setup
class SysTrayApp:
    def __init__(self, root):
        self.root = root
        self.setup_tray_icon()

    def setup_tray_icon(self):
        # Hide the main window
        self.root.withdraw()

        # Message map for the system tray icon
        message_map = {
            win32con.WM_DESTROY: self.on_destroy,
            win32con.WM_COMMAND: self.on_command,
            win32con.WM_USER+20 : self.on_notify,
        }

        # Register the window class
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = GetModuleHandle(None)
        wc.lpszClassName = "SysTrayIconPy"
        wc.lpfnWndProc = message_map
        classAtom = win32gui.RegisterClass(wc)

        # Create the window
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(wc.lpszClassName, "KeepAwake", style,
                                          0, 0, win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT, 0, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)

        # Icon and tooltip
        icon_path = os.path.abspath(os.path.join(sys.path[0], "icon.ico"))
        if not os.path.isfile(icon_path):
            icon_path = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        else:
            icon_path = win32gui.LoadImage(hinst, icon_path,
                                           win32con.IMAGE_ICON, 0, 0,
                                           win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE)

        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, icon_path, "KeepAwake is running")
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

        # Create a menu
        self.menu = Menu(self.root, tearoff=0)
        self.menu.add_command(label="Exit", command=self.exit_app)

        # Start the main loop in a separate thread
        threading.Thread(target=win32gui.PumpMessages).start()

    def on_destroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)

    def on_command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        if id == 1:
            self.exit_app()

    def on_notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_RBUTTONUP:
            # Display the menu
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            self.menu.tk_popup(pos[0], pos[1])
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return True

    def exit_app(self):
        logging.info("Exiting application.")
        self.root.destroy()
        os._exit(0)
  
# Automatic restart
def restart_script():
    logging.info("Restarting script.")
    python = sys.executable
    os.execl(python, python, * sys.argv)

# Main function
def main():
    try:
        next_press_time = time.time() + random.randint(config["min_interval"], config["max_interval"])
        while True:
            keep_system_awake()  # Prevent sleep mode
            current_time = time.time()
            if current_time >= next_press_time:
                PressKey(config["key_code"])     # Press key
                time.sleep(0.05)                 # Short delay
                ReleaseKey(config["key_code"])   # Release key
                logging.info(f"Key {config['key_code']} pressed and released.")
                next_press_time = current_time + random.randint(config["min_interval"], config["max_interval"])
            if monitors_connected() == 0:
                logging.warning("No monitors detected. Ensuring system stays awake.")
                # Additional actions can be added here
            time.sleep(5)  # Wait before next iteration
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        # Optionally restart the script
        restart_script()

if __name__ == "__main__":
    root = tk.Tk()
    app = SysTrayApp(root)
    threading.Thread(target=main, daemon=True).start()
    root.mainloop()
