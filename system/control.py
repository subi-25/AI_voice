"""
Anya System Control — OS-level operations.
"""

import os
import subprocess
import platform
import datetime
from typing import Optional

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

SYSTEM = platform.system()

APP_MAP = {
    "chrome":        {"Windows": "chrome",    "Darwin": "open -a 'Google Chrome'", "Linux": "google-chrome"},
    "firefox":       {"Windows": "firefox",   "Darwin": "open -a Firefox",         "Linux": "firefox"},
    "notepad":       {"Windows": "notepad",   "Darwin": "open -a TextEdit",        "Linux": "gedit"},
    "calculator":    {"Windows": "calc",      "Darwin": "open -a Calculator",      "Linux": "gnome-calculator"},
    "explorer":      {"Windows": "explorer",  "Darwin": "open ~",                  "Linux": "nautilus"},
    "task manager":  {"Windows": "taskmgr",   "Darwin": "open -a 'Activity Monitor'", "Linux": "gnome-system-monitor"},
    "word":          {"Windows": "winword",   "Darwin": "open -a 'Microsoft Word'", "Linux": "libreoffice --writer"},
    "excel":         {"Windows": "excel",     "Darwin": "open -a 'Microsoft Excel'", "Linux": "libreoffice --calc"},
    "vs code":       {"Windows": "code",      "Darwin": "code",                    "Linux": "code"},
    "code":          {"Windows": "code",      "Darwin": "code",                    "Linux": "code"},
    "terminal":      {"Windows": "cmd",       "Darwin": "open -a Terminal",        "Linux": "gnome-terminal"},
    "cmd":           {"Windows": "cmd",       "Darwin": "open -a Terminal",        "Linux": "gnome-terminal"},
    "spotify":       {"Windows": "spotify",   "Darwin": "open -a Spotify",         "Linux": "spotify"},
    "vlc":           {"Windows": "vlc",       "Darwin": "open -a VLC",             "Linux": "vlc"},
    "paint":         {"Windows": "mspaint",   "Darwin": "open -a Preview",         "Linux": "gimp"},
    "powerpoint":    {"Windows": "powerpnt",  "Darwin": "open -a 'Microsoft PowerPoint'", "Linux": "libreoffice --impress"},
}


class SystemControl:
    def __init__(self, speaker=None):
        self.speaker = speaker
        self._screenshot_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Anya_Screenshots")
        os.makedirs(self._screenshot_dir, exist_ok=True)

    def open_app(self, app_name: str) -> str:
        key = app_name.lower().strip()
        cmd = None
        for known, cmds in APP_MAP.items():
            if known in key:
                cmd = cmds.get(SYSTEM, cmds.get("Linux", ""))
                break
        cmd = cmd or app_name
        try:
            if cmd == app_name:
                import webbrowser
                if SYSTEM == "Windows":
                    os.system(f'start "" "{app_name}"')
                elif SYSTEM == "Darwin":
                    os.system(f'open "{app_name}"')
                else:
                    os.system(f'xdg-open "{app_name}"')
            else:
                if SYSTEM == "Windows":
                    subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen(cmd, shell=True)
            return f"✅ Opened {app_name}!"
        except Exception as e:
            return f"❌ Could not open {app_name}: {e}"

    def close_app(self, app_name: str) -> str:
        try:
            if SYSTEM == "Windows":
                os.system(f"taskkill /f /im {app_name}.exe 2>nul")
            else:
                os.system(f"pkill -f '{app_name}'")
            return f"✅ Closed {app_name}."
        except Exception as e:
            return f"❌ Error: {e}"

    def shutdown(self, delay: int = 10) -> str:
        if SYSTEM == "Windows":
            os.system(f"shutdown /s /t {delay}")
        elif SYSTEM == "Darwin":
            os.system(f"sudo shutdown -h +{max(delay//60, 1)}")
        else:
            os.system(f"shutdown -h +{max(delay//60, 1)}")
        return f"⚠️ Shutting down in {delay} seconds."

    def restart(self, delay: int = 10) -> str:
        if SYSTEM == "Windows":
            os.system(f"shutdown /r /t {delay}")
        elif SYSTEM == "Darwin":
            os.system(f"sudo shutdown -r +{max(delay//60, 1)}")
        else:
            os.system(f"shutdown -r +{max(delay//60, 1)}")
        return f"⚠️ Restarting in {delay} seconds."

    def cancel_shutdown(self) -> str:
        if SYSTEM == "Windows":
            os.system("shutdown /a")
        else:
            os.system("sudo shutdown -c")
        return "✅ Shutdown cancelled."

    def volume_up(self, step: int = 10) -> str:
        if not PYAUTOGUI_AVAILABLE:
            return "❌ Install pyautogui for volume control."
        try:
            for _ in range(step // 2):
                pyautogui.press("volumeup")
            return "🔊 Volume increased."
        except Exception as e:
            return f"❌ Volume error: {e}"

    def volume_down(self, step: int = 10) -> str:
        if not PYAUTOGUI_AVAILABLE:
            return "❌ Install pyautogui for volume control."
        try:
            for _ in range(step // 2):
                pyautogui.press("volumedown")
            return "🔉 Volume decreased."
        except Exception as e:
            return f"❌ Volume error: {e}"

    def mute(self) -> str:
        if not PYAUTOGUI_AVAILABLE:
            return "❌ Install pyautogui."
        pyautogui.press("volumemute")
        return "🔇 Audio muted."

    def brightness_up(self) -> str:
        try:
            if SYSTEM == "Windows":
                import wmi
                c = wmi.WMI(namespace="wmi")
                m = c.WmiMonitorBrightnessMethods()[0]
                cur = c.WmiMonitorBrightness()[0].CurrentBrightness
                m.WmiSetBrightness(min(cur + 10, 100), 0)
                return "💡 Brightness increased."
            elif SYSTEM == "Linux":
                os.system("xrandr --output $(xrandr | grep ' connected' | head -1 | cut -d' ' -f1) --brightness 1.0")
                return "💡 Brightness at max."
            else:
                return "⚠️ Brightness not supported on this platform."
        except Exception as e:
            return f"❌ Brightness error: {e}"

    def brightness_down(self) -> str:
        try:
            if SYSTEM == "Windows":
                import wmi
                c = wmi.WMI(namespace="wmi")
                m = c.WmiMonitorBrightnessMethods()[0]
                cur = c.WmiMonitorBrightness()[0].CurrentBrightness
                m.WmiSetBrightness(max(cur - 10, 10), 0)
                return "💡 Brightness decreased."
            elif SYSTEM == "Linux":
                os.system("xrandr --output $(xrandr | grep ' connected' | head -1 | cut -d' ' -f1) --brightness 0.7")
                return "💡 Brightness reduced."
            else:
                return "⚠️ Brightness not supported on this platform."
        except Exception as e:
            return f"❌ Brightness error: {e}"

    def take_screenshot(self) -> str:
        try:
            if PYAUTOGUI_AVAILABLE:
                img = pyautogui.screenshot()
            elif PIL_AVAILABLE:
                img = ImageGrab.grab()
            else:
                return "❌ Install pyautogui or Pillow for screenshots."
            fname = f"anya_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            path = os.path.join(self._screenshot_dir, fname)
            img.save(path)

            if SYSTEM == "Windows":
                os.startfile(path)
            elif SYSTEM == "Darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')

            return f"📸 Screenshot saved:\n{path}"
        except Exception as e:
            return f"❌ Screenshot error: {e}"

    def get_time(self) -> str:
        return datetime.datetime.now().strftime("%I:%M %p")

    def get_date(self) -> str:
        return datetime.datetime.now().strftime("%A, %B %d, %Y")
