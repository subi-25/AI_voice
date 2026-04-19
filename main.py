"""
Anya AI Desktop Assistant
Main entry point — Powered by Google Gemini
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.interface import AnyaUI
from brain.ai_engine import AIEngine
from voice.listen import VoiceListener
from voice.speak import Speaker
from system.control import SystemControl
from system.files import FileManager
from notification.notifier import NotificationMonitor


def main():
    print("╔══════════════════════════════════════╗")
    print("║   🧠 Anya AI Desktop Assistant        ║")
    print("║   Powered by Google Gemini            ║")
    print("╚══════════════════════════════════════╝")

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if not gemini_key:
        print("\n⚠️  No GEMINI_API_KEY found.")
        print("   Set it via: GEMINI_API_KEY=your-key python main.py")
        print("   Or enter it in ⚙️ Settings after launch.\n")

    print("🔧 Initializing components…")

    speaker     = Speaker()
    ai_engine   = AIEngine(api_key=gemini_key)
    system_ctrl = SystemControl(speaker)
    file_mgr    = FileManager(speaker)
    notifier    = NotificationMonitor(speaker)
    listener    = VoiceListener()

    print("🚀 Launching Anya UI…\n")

    app = AnyaUI(
        ai_engine=ai_engine,
        speaker=speaker,
        listener=listener,
        system_ctrl=system_ctrl,
        file_mgr=file_mgr,
        notifier=notifier,
    )
    app.run()


if __name__ == "__main__":
    main()