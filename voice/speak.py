"""
Anya Speaker — Thread-safe text-to-speech.
"""

import threading
import queue
import os
from typing import Optional

try:
    import asyncio
    import edge_tts
    from playsound import playsound
    EDGE_AVAILABLE = True
except ImportError:
    EDGE_AVAILABLE = False
    print("⚠️  edge-tts or playsound not installed. Run: pip install edge-tts playsound==1.2.2")

class Speaker:
    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._speaking = False
        self._muted = False
        self._thread: Optional[threading.Thread] = None
        self._voice = "en-US-AnaNeural"  # Default Edge Neural Child Voice
        self._rate_shift = "+10%"

        if EDGE_AVAILABLE:
            self._thread = threading.Thread(target=self._worker, daemon=True)
            self._thread.start()

    def speak(self, text: str, priority: bool = False):
        if self._muted or not EDGE_AVAILABLE:
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
        # We can implement dynamic rate shifting, but keeping it fixed for Neural voice
        pass

    def set_volume(self, volume: float):
        pass

    @property
    def is_speaking(self):
        return self._speaking

    def _worker(self):
        # Create an async event loop for edge-tts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
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
                        temp_file = os.path.join(os.path.expanduser("~"), "anya_temp_tts.mp3")
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                            except:
                                pass
                        
                        # Generate the neural speech!
                        communicate = edge_tts.Communicate(text, self._voice, rate=self._rate_shift)
                        loop.run_until_complete(communicate.save(temp_file))
                        
                        # Play the speech natively
                        playsound(temp_file)
                    except Exception as e:
                        print(f"[Speaker] TTS error: {e}")
                    finally:
                        self._speaking = False
            self._queue.task_done()

    def shutdown(self):
        self._queue.put(None)

