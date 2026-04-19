"""
Anya AI Engine — Powered by Google Gemini
"""

import os
import re
import datetime
import random
from typing import Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Run: pip install google-generativeai")

SYSTEM_PROMPT = """You are Anya, an elite AI desktop assistant.
You are intelligent, warm, and highly capable.

Personality:
- Warm, professional, and slightly playful
- Address the user respectfully
- Use emojis occasionally (not excessively)
- Be concise — 1-3 sentences unless giving instructions
- Anticipate needs and offer follow-up suggestions

When the user asks you to perform system actions (open apps,
screenshots, volume, etc.), acknowledge and confirm briefly.
Anya handles execution automatically — you don't explain how.

Always respond in the language the user is using.
"""


class AIEngine:
    AFFIRMATIONS = [
        "On it! ✨", "Right away! ✅", "Consider it done! 🚀",
        "Absolutely! Taking care of that now.",
        "Sure thing! Let me handle that.",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.user_name = "Subi"
        self.conversation_history = []
        self.model = None
        self.chat = None
        self.use_gemini = False

        if GEMINI_AVAILABLE and self.api_key:
            self._init_gemini()
        else:
            print("ℹ️  Built-in engine active. Set GEMINI_API_KEY for AI.")

    def _init_gemini(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name="gemini-3-flash-preview",
                system_instruction=SYSTEM_PROMPT +
                    f"\nThe user's name is {self.user_name}.",
            )
            self.chat = self.model.start_chat(history=[])
            self.use_gemini = True
            print("✅ Gemini AI engine initialized.")
        except Exception as e:
            print(f"❌ Gemini init failed: {e}")
            self.use_gemini = False

    def set_api_key(self, key: str):
        self.api_key = key.strip()
        if GEMINI_AVAILABLE and self.api_key:
            self._init_gemini()

    def set_user_name(self, name: str):
        self.user_name = name
        if self.use_gemini:
            self._init_gemini()

    def process_command(self, user_input: str) -> dict:
        text = user_input.strip().lower()
        intent, action, params = self._detect_intent(text)

        if self.use_gemini:
            response = self._gemini_response(user_input, intent, action, params)
        else:
            response = self._rule_response(user_input, intent, params)

        return {"intent": intent, "response": response,
                "action": action, "params": params}

    def _detect_intent(self, text: str):
        patterns = [
            (r"\b(bye|goodbye|exit|quit|close anya|farewell)\b",
             "farewell", "exit", {}),
            (r"\b(time|clock|what time)\b", "time_query", "get_time", {}),
            (r"\b(date|today|what day)\b",  "date_query", "get_date", {}),
            (r"volume\s+up|increase\s+volume|louder|turn up",
             "volume_up",   "volume_up",   {}),
            (r"volume\s+down|decrease\s+volume|quieter|lower volume",
             "volume_down", "volume_down", {}),
            (r"\bmute\b",                   "mute",          "mute",          {}),
            (r"brightness\s+up|brighter",   "brightness_up", "brightness_up", {}),
            (r"brightness\s+down|dimmer",   "brightness_down","brightness_down",{}),
            (r"screenshot|capture screen",  "screenshot",  "take_screenshot",  {}),
            (r"open file manager|file manager|browse files",
             "file_manager", "open_file_manager", {}),
            (r"notification|show alerts",   "notifications","show_notifications",{}),
            (r"read\s+(this|screen|text)|ocr",
             "read_text", "read_screen", {}),
            (r"\bshutdown\b|\bshut down\b|\bpower off\b",
             "shutdown", "shutdown", {}),
            (r"\brestart\b|\breboot\b",     "restart",  "restart",  {}),
            (r"\bhelp\b|\bcommands\b",      "help",     "show_help",{}),
            (r"\bjoke\b|\bfunny\b",         "joke",     None,       {}),
            (r"\bweather\b",                "weather",  "get_weather",{}),
        ]
        for pat, intent, action, params in patterns:
            if re.search(pat, text):
                return intent, action, params

        m = re.search(r"(?:open|launch|start)\s+(.+)", text)
        if m:
            return "open_app", "open_app", {"app": m.group(1).strip()}

        m = re.search(r"(?:close|kill|quit)\s+(.+)", text)
        if m:
            return "close_app", "close_app", {"app": m.group(1).strip()}

        m = re.search(r"create\s+(?:a\s+)?(?:new\s+)?file\s+(.+)", text)
        if m:
            return "create_file", "create_file", {"name": m.group(1).strip()}

        m = re.search(r"delete\s+(?:file\s+)?(.+)", text)
        if m:
            return "delete_file", "delete_file", {"path": m.group(1).strip()}

        m = re.search(r"search\s+(?:for\s+)?(?:files?\s+)?(.+)", text)
        if m:
            return "search_files", "search_files", {"query": m.group(1).strip()}

        m = re.search(r"(?:calculate|compute|what is)\s+([\d\s\+\-\*/\(\)\.%]+)", text)
        if m:
            return "calculate", "calculate", {"expr": m.group(1).strip()}

        if re.search(r"\b(hello|hi|hey|good morning|howdy)\b", text):
            return "greeting", None, {}

        return "conversation", None, {}

    def _gemini_response(self, user_input, intent, action, params) -> str:
        try:
            action_ctx = {
                "get_time":          "Tell the user the current time.",
                "get_date":          "Tell the user today's date.",
                "open_app":          f"Confirm opening {params.get('app','it')}.",
                "close_app":         f"Confirm closing {params.get('app','it')}.",
                "volume_up":         "Confirm volume increased.",
                "volume_down":       "Confirm volume decreased.",
                "mute":              "Confirm audio muted.",
                "brightness_up":     "Confirm brightness increased.",
                "brightness_down":   "Confirm brightness decreased.",
                "take_screenshot":   "Confirm taking a screenshot.",
                "open_file_manager": "Confirm opening file manager.",
                "show_notifications":"Confirm showing notifications.",
                "read_screen":       "Confirm activating OCR text reader.",
                "shutdown":          "Ask user to confirm shutdown.",
                "restart":           "Ask user to confirm restart.",
                "create_file":       f"Confirm creating '{params.get('name','')}'.",
                "delete_file":       f"Ask to confirm deleting '{params.get('path','')}'.",
                "search_files":      f"Confirm searching for '{params.get('query','')}'.",
                "show_help":         "Give a friendly overview of your capabilities.",
                "get_weather":       "Say you'll check and note a live API is needed.",
            }
            ctx = ""
            if action in action_ctx:
                ctx = f"\n[System note: {action_ctx[action]}]"
            resp = self.chat.send_message(user_input + ctx)
            return resp.text.strip()
        except Exception as e:
            print(f"[Gemini] {e}")
            return self._rule_response(user_input, intent, params)

    def _rule_response(self, original, intent, params) -> str:
        now = datetime.datetime.now()
        h = now.hour
        period = "morning" if h < 12 else "afternoon" if h < 17 else "evening"

        responses = {
            "greeting":      f"Good {period}, {self.user_name}! 🌟 How can I help?",
            "farewell":      f"Goodbye, {self.user_name}! 👋 Have a wonderful day!",
            "time_query":    f"It's {now.strftime('%I:%M %p')}. ⏰",
            "date_query":    f"Today is {now.strftime('%A, %B %d, %Y')}. 📅",
            "open_app":      f"{random.choice(self.AFFIRMATIONS)} Opening {params.get('app','it')}...",
            "close_app":     f"Closing {params.get('app','it')} now.",
            "volume_up":     "Volume turned up. 🔊",
            "volume_down":   "Volume turned down. 🔉",
            "mute":          "Audio muted. 🔇",
            "brightness_up": "Brightness increased. 💡",
            "brightness_down":"Brightness decreased. 🌙",
            "shutdown":      f"⚠️ Confirm shutdown, {self.user_name}?",
            "restart":       f"⚠️ Confirm restart, {self.user_name}?",
            "screenshot":    "📸 Taking a screenshot!",
            "file_manager":  "📂 Opening File Manager!",
            "notifications": "🔔 Showing notifications!",
            "read_text":     "📖 Activating OCR text reader…",
            "create_file":   f"✅ Creating '{params.get('name','file')}'…",
            "delete_file":   f"⚠️ Move '{params.get('path','')}' to Anya Trash?",
            "search_files":  f"🔍 Searching for '{params.get('query','')}'…",
            "weather":       "🌤️ Connect a weather API in Settings for live data.",
            "help":          self._help_text(),
        }

        if intent == "joke":
            jokes = [
                "Why do programmers prefer dark mode? Light attracts bugs! 🐛",
                "Why did the AI go to therapy? Too many deep issues! 🤖",
                "What's a computer's favorite snack? Microchips! 🍟",
            ]
            return random.choice(jokes)

        if intent == "calculate":
            expr = params.get("expr", "")
            try:
                safe = re.sub(r"[^0-9\+\-\*/\(\)\.\s%]", "", expr)
                return f"🧮 {safe.strip()} = {eval(safe)}"
            except Exception:
                return "Try: 'calculate 15 * 7 + 3'"

        return responses.get(intent,
            f"I'm here for you, {self.user_name}! Could you tell me more?")

    def _help_text(self) -> str:
        return (
            f"Here's what I can do, {self.user_name}! 🌟\n\n"
            "🗣️  Voice  — Click 🎙 or say 'Hey Anya' to speak\n"
            "📂  Files  — 'Open file manager', 'Create file x.txt'\n"
            "🖥️  Apps   — 'Open Chrome', 'Close Spotify'\n"
            "🔊  Audio  — 'Volume up/down', 'Mute'\n"
            "💡  Screen — 'Brightness up/down'\n"
            "📸  Snap   — 'Take screenshot'\n"
            "📖  OCR    — 'Read this text'\n"
            "🔔  Alerts — 'Show notifications'\n"
            "🧮  Math   — 'Calculate 15 * 7'\n"
            "😄  Fun    — 'Tell me a joke'\n"
            "⏰  Time   — 'What time is it?'\n"
            "❌  Exit   — 'Goodbye'"
        )