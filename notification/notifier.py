"""
Anya Notification Monitor
"""

import platform
import threading
import time
import datetime
from typing import List, Dict, Optional, Callable

SYSTEM = platform.system()

try:
    from win10toast import ToastNotifier
    WIN_TOAST = True
except ImportError:
    WIN_TOAST = False


class Notification:
    def __init__(self, title: str, message: str, source: str = "System", urgency: str = "normal"):
        self.title = title
        self.message = message
        self.source = source
        self.urgency = urgency
        self.timestamp = datetime.datetime.now()
        self.read = False

    def __str__(self):
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.source}: {self.title}"


class NotificationMonitor:
    def __init__(self, speaker=None):
        self.speaker = speaker
        self.history: List[Notification] = []
        self._max = 100
        self._callbacks: List[Callable] = []
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._toaster = ToastNotifier() if WIN_TOAST else None
        self._add_startup()

    def _add_startup(self):
        n = Notification("Anya is ready! 🌟",
                         "Your AI assistant is active. Say 'Hey Anya' to begin.",
                         source="Anya")
        self.history.append(n)

    def add_callback(self, cb: Callable):
        self._callbacks.append(cb)

    def push(self, title: str, message: str, source: str = "Anya",
             urgency: str = "normal", speak: bool = False):
        n = Notification(title, message, source, urgency)
        self._store(n)
        self._dispatch(n)
        if speak and self.speaker:
            self.speaker.speak(f"New notification: {title}. {message}")

    def show_desktop_notification(self, title: str, message: str):
        try:
            if SYSTEM == "Windows" and self._toaster:
                threading.Thread(
                    target=self._toaster.show_toast,
                    args=(title, message),
                    kwargs={"duration": 5, "threaded": True},
                    daemon=True,
                ).start()
            elif SYSTEM == "Darwin":
                import subprocess
                script = f'display notification "{message}" with title "{title}"'
                subprocess.Popen(["osascript", "-e", script])
            elif SYSTEM == "Linux":
                import subprocess
                subprocess.Popen(["notify-send", title, message])
        except Exception as e:
            print(f"[Notifier] {e}")

    def get_unread(self) -> List[Notification]:
        return [n for n in self.history if not n.read]

    def mark_all_read(self):
        for n in self.history:
            n.read = True

    def get_history(self, limit: int = 20) -> List[Notification]:
        return list(reversed(self.history[-limit:]))

    def start_monitoring(self):
        if self._monitoring:
            return
        self._monitoring = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        self._monitoring = False

    def _store(self, n: Notification):
        self.history.append(n)
        if len(self.history) > self._max:
            self.history = self.history[-self._max:]

    def _dispatch(self, n: Notification):
        for cb in self._callbacks:
            try:
                cb(n)
            except Exception:
                pass

    def _loop(self):
        last_hour = -1
        while self._monitoring:
            now = datetime.datetime.now()
            if now.hour != last_hour and now.minute == 0:
                last_hour = now.hour
                self.push("⏰ Time Update",
                          f"It's {now.strftime('%I:%M %p')}",
                          source="Anya Clock")
            time.sleep(60)
