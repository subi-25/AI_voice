"""
Anya Voice Listener — Speech-to-text with wake word detection.
"""

import threading
import time
from typing import Callable, Optional

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("⚠️  speech_recognition not installed. Run: pip install SpeechRecognition sounddevice")

WAKE_WORDS = ["hey anya", "anya", "hi anya", "okay anya", "ok anya"]

class SoundDeviceMicrophone(sr.AudioSource):
    """
    Drop-in replacement for sr.Microphone that uses sounddevice instead of PyAudio.
    """
    def __init__(self, sample_rate=16000, chunk_size=1024):
        self.SAMPLE_RATE = sample_rate
        self.CHUNK = chunk_size
        self.SAMPLE_WIDTH = 2
        self.stream = None
        self._q = None
        self._sd_stream = None

    def __enter__(self):
        import sounddevice as sd
        import queue
        self._q = queue.Queue()
        
        def callback(indata, frames, time, status):
            if status:
                pass
            self._q.put(bytes(indata))
            
        self._sd_stream = sd.RawInputStream(
            samplerate=self.SAMPLE_RATE,
            blocksize=self.CHUNK,
            channels=1,
            dtype='int16',
            callback=callback
        )
        self._sd_stream.start()
        
        class _Stream:
            def __init__(self, q):
                self.q = q
            def read(self, size):
                return self.q.get()
                
        self.stream = _Stream(self._q)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._sd_stream:
            self._sd_stream.stop()
            self._sd_stream.close()
            self._sd_stream = None
        self.stream = None



class VoiceListener:
    def __init__(self):
        self.is_listening = False
        self.is_active = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.on_text_callback: Optional[Callable[[str], None]] = None
        self.on_status_callback: Optional[Callable[[str], None]] = None

        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.pause_threshold = 0.8
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
        else:
            self.recognizer = None

    def set_callbacks(self, on_text: Callable, on_status: Callable):
        self.on_text_callback = on_text
        self.on_status_callback = on_status

    def start_continuous_listening(self):
        if not SR_AVAILABLE:
            self._notify_status("❌ Microphone unavailable — install SpeechRecognition + sounddevice")
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop_listening(self):
        self._stop_event.set()
        self.is_listening = False
        self.is_active = False
        self._notify_status("🔇 Listening stopped")

    def listen_once(self) -> Optional[str]:
        if not SR_AVAILABLE:
            return None
        try:
            with SoundDeviceMicrophone() as source:
                self._notify_status("🎙️ Listening…")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=7, phrase_time_limit=12)
            text = self.recognizer.recognize_google(audio).lower()
            self._notify_status(f"✅ Heard: '{text}'")
            return text
        except sr.WaitTimeoutError:
            self._notify_status("⏱️ No speech detected")
        except sr.UnknownValueError:
            self._notify_status("🤔 Could not understand")
        except sr.RequestError as e:
            self._notify_status(f"❌ Recognition error: {e}")
        except Exception as e:
            self._notify_status(f"❌ Mic error: {e}")
        return None

    def _listen_loop(self):
        self._notify_status("👂 Continuous listening active — say 'Hey Anya'")
        while not self._stop_event.is_set():
            try:
                with SoundDeviceMicrophone() as source:
                    self.is_listening = True
                    if not self.is_active:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=10)
                text = self.recognizer.recognize_google(audio).lower()
                if not self.is_active:
                    if any(w in text for w in WAKE_WORDS):
                        self.is_active = True
                        self._notify_status("🌟 Anya activated! Speak your command…")
                        if self.on_text_callback:
                            self.on_text_callback("__wake_word__")
                else:
                    self._notify_status(f"🗣️ You said: '{text}'")
                    if self.on_text_callback:
                        self.on_text_callback(text)
                    self.is_active = False
            except sr.WaitTimeoutError:
                pass
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                self._notify_status(f"❌ Speech service: {e}")
                time.sleep(2)
            except Exception as e:
                self._notify_status(f"❌ Error: {e}")
                time.sleep(1)
        self.is_listening = False
        self._notify_status("🔇 Listener stopped")

    def _notify_status(self, msg: str):
        if self.on_status_callback:
            self.on_status_callback(msg)
        else:
            print(f"[Voice] {msg}")