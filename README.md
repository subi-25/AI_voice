# 🧠 Anya AI Desktop Assistant
### Powered by Google Gemini · Built for Subi

---

## ✦ What's New in This Version

| Feature | Status |
|---|---|
| 🤖 **Gemini AI Backend** | Replace built-in NLP with Google's Gemini 1.5 Flash |
| 🎙️ **Voice I/O** | Wake word detection + TTS responses |
| 🎨 **Premium UI** | Redesigned deep-navy × cyan aesthetic |
| 📡 **Real AI Chat** | Full conversational memory via Gemini |
| ⚙️ **Live Settings** | Enter Gemini key in-app, no restart needed | 

---

## 🚀 Quick Start

### 1. Install Python 3.9+
https://www.python.org/downloads/

### 2. Install dependencies
```bash
cd anya_assistant
pip install -r requirements.txt
```

### 3. Get your Gemini API Key (FREE)
👉 https://aistudio.google.com/app/apikey

### 4. Set your key (choose one method)

**Method A — Environment variable (recommended):**
```bash
# Windows
set GEMINI_API_KEY=your-key-here
python main.py

# macOS / Linux
GEMINI_API_KEY=your-key-here python main.py
```

**Method B — In-app Settings tab:**
Launch Anya → click ⚙️ Settings → paste key → Save & Apply

### 5. Launch!
```bash
python main.py
```

---

## 🎙️ Voice Setup (Optional)

```bash
# Windows
pip install pyaudio

# Linux
sudo apt install python3-pyaudio

# macOS
brew install portaudio && pip install pyaudio
```

**Wake word:** Say **"Hey Anya"** → then speak your command.

---

## 📖 OCR Setup (Optional)

```bash
pip install pytesseract pillow
```

Download Tesseract OCR:
- **Windows:** https://github.com/UB-Mannheim/tesseract/wiki
- **Linux:** `sudo apt install tesseract-ocr`
- **macOS:** `brew install tesseract`

---

## 🗣️ Commands

```
"Hey Anya"              Wake word (voice mode)
"What time is it?"      Current time
"What's today's date?"  Today's date
"Open Chrome"           Launch browser
"Open VS Code"          Launch editor
"Volume up / down"      Audio control
"Mute"                  Mute audio
"Brightness up / down"  Screen brightness
"Take screenshot"       Capture screen
"Open file manager"     Browse files
"Create file notes.txt" New file
"Search files report"   Find files
"Read this text"        OCR screen
"Show notifications"    Alerts panel
"Calculate 15 * 7 + 3"  Math
"Tell me a joke"        Fun!
"Help"                  Full command list
"Goodbye"               Close Anya
```

---

## 📁 Project Structure

```
anya_assistant/
├── main.py                  ← Entry point
├── requirements.txt
├── brain/
│   └── ai_engine.py        ← Gemini AI + intent detection
├── voice/
│   ├── listen.py           ← Speech recognition + wake word
│   └── speak.py            ← Text-to-speech
├── system/
│   ├── control.py          ← OS control (apps, volume, etc.)
│   └── files.py            ← File management
├── notification/
│   └── notifier.py         ← Notification center
└── ui/
    └── interface.py        ← Premium Tkinter UI
```

---

## 🔐 Safety

- ✅ Confirmation dialogs for shutdown/restart/delete
- ✅ Files moved to `~/.anya_trash` (recoverable)
- ✅ Thread-safe voice & UI operations
- ✅ Graceful degradation if optional libraries missing

---

Made with 💜 for Subi
