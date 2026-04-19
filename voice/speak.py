"""
Anya Speaker — Thread-safe text-to-speech.
"""

import threading
import queue
from typing import Optional

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("⚠️  pyttsx3 not installed. Run: pip install pyttsx3")


class Speaker:
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._speaking = False
        self._muted = False
        self._engine = None
        self._current_rate = 175
        self._current_volume = 1.0
        self._thread: Optional[threading.Thread] = None

        if PYTTSX3_AVAILABLE:
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def _init_engine(self):
        try:
            if getattr(self, "_engine", None) is not None:
                del self._engine
            
            self._engine = pyttsx3.init()
            voices = self._engine.getProperty("voices")
            for v in voices:
                name = v.name.lower()
                if any(k in name for k in ["female", "zira", "samantha", "hazel", "susan"]):
                    self._engine.setProperty("voice", v.id)
                    break
            self._engine.setProperty("rate", self._current_rate)
            self._engine.setProperty("volume", self._current_volume)
        except Exception as e:
            print(f"[Speaker] Engine init error: {e}")
            self._engine = None

    def speak(self, text: str, priority: bool = False):
        if self._muted or not PYTTSX3_AVAILABLE:
            print(f"[Anya] {text}")
            return
        if priority:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
        self._queue.put({"cmd": "speak", "text": text})

    def stop(self):
        self._queue.put({"cmd": "stop"})

    def set_muted(self, muted: bool):
        self._muted = muted

    def set_rate(self, rate: int):
        self._queue.put({"cmd": "set_rate", "rate": rate})

    def set_volume(self, volume: float):
        self._queue.put({"cmd": "set_volume", "volume": max(0.0, min(1.0, volume))})

    @property
    def is_speaking(self):
        return self._speaking

    def _worker(self):
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        self._init_engine()

        while True:
            msg = self._queue.get()
            if msg is None:
                break
                
            if isinstance(msg, dict):
                cmd = msg.get("cmd")
                if cmd == "speak":
                    text = msg.get("text")
                    self._speaking = True
                    try:
                        self._init_engine()
                        if self._engine:
                            self._engine.say(text)
                            self._engine.runAndWait()
                    except Exception as e:
                        print(f"[Speaker] TTS error: {e}")
                        self._init_engine()
                    finally:
                        self._speaking = False
                elif cmd == "stop":
                    if self._engine:
                        try:
                            self._engine.stop()
                        except Exception:
                            pass
                elif cmd == "set_rate":
                    self._current_rate = msg.get("rate")
                    if self._engine:
                        self._engine.setProperty("rate", self._current_rate)
                elif cmd == "set_volume":
                    self._current_volume = msg.get("volume")
                    if self._engine:
                        self._engine.setProperty("volume", self._current_volume)
            else:
                self._speaking = True
                try:
                    if self._engine:
                        self._engine.say(msg)
                        self._engine.runAndWait()
                except Exception as e:
                    print(f"[Speaker] TTS error: {e}")
                    self._init_engine()
                finally:
                    self._speaking = False
                    
            self._queue.task_done()

    def shutdown(self):
        self._queue.put(None)
