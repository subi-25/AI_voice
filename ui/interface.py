"""
Anya AI Desktop Assistant — Premium UI
Voice input fully integrated into chat.
All responses (AI + system actions) show in chat.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import threading
import datetime
import os
import sys
import platform

try:
    import pytesseract
    from PIL import Image, ImageGrab
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
#  Premium color palette — Deep navy × electric cyan × soft gold
# ──────────────────────────────────────────────────────────────────────────────
C = {
    "bg":           "#080c14",
    "surface":      "#0d1220",
    "surface2":     "#111827",
    "surface3":     "#1a2235",
    "accent":       "#00d4ff",
    "accent_dim":   "#0099bb",
    "accent2":      "#7dd3fc",
    "gold":         "#fbbf24",
    "gold_dim":     "#d97706",
    "green":        "#34d399",
    "red":          "#f87171",
    "yellow":       "#fde68a",
    "purple":       "#a78bfa",
    "text":         "#f1f5f9",
    "text_dim":     "#94a3b8",
    "text_muted":   "#475569",
    "border":       "#1e293b",
    "border2":      "#2d3f55",
    "input_bg":     "#0a1020",
    "hover":        "#1e2d45",
    "msg_user_bg":  "#0f1e35",
    "msg_bot_bg":   "#090f1c",
    "scrollbar":    "#1e293b",
    "tag_user":     "#38bdf8",
    "tag_anya":     "#00d4ff",
    "mic_active":   "#f87171",
    "mic_idle":     "#475569",
}

FONT_TITLE  = ("Segoe UI", 20, "bold")
FONT_HDR    = ("Segoe UI", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_BODY_B = ("Segoe UI", 10, "bold")
FONT_SMALL  = ("Segoe UI", 8)
FONT_MONO   = ("Consolas", 9)
FONT_CHAT   = ("Segoe UI", 10)
FONT_CHAT_B = ("Segoe UI", 10, "bold")


class AnyaUI:
    def __init__(self, ai_engine, speaker, listener, system_ctrl, file_mgr, notifier):
        self.ai = ai_engine
        self.speaker = speaker
        self.listener = listener
        self.sys_ctrl = system_ctrl
        self.file_mgr = file_mgr
        self.notifier = notifier

        self._voice_active = False        # continuous listening mode
        self._mic_listening = False       # one-shot mic button press
        self._pending_confirm = None
        self._input_history = []
        self._history_idx = -1
        self._settings_entries = {}

        self._build_window()
        self._apply_theme()
        self._build_layout()
        self._wire_callbacks()
        self._start_background_tasks()

    # ══════════════════════════════════════════════════════════════════
    #  Window
    # ══════════════════════════════════════════════════════════════════

    def _build_window(self):
        self.root = tk.Tk()
        self.root.title("Anya  ·  AI Desktop Assistant")
        self.root.geometry("1200x750")
        self.root.minsize(960, 620)
        self.root.configure(bg=C["bg"])
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = 1200, 750
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_theme(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("TNotebook",
                    background=C["surface"], borderwidth=0, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=C["surface2"], foreground=C["text_dim"],
                    padding=[16, 8], font=FONT_BODY, borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", C["surface3"])],
              foreground=[("selected", C["accent"])])
        s.configure("TScrollbar",
                    background=C["scrollbar"], troughcolor=C["bg"],
                    borderwidth=0, relief="flat", arrowsize=0)
        s.configure("TFrame", background=C["bg"])

    # ══════════════════════════════════════════════════════════════════
    #  Layout
    # ══════════════════════════════════════════════════════════════════

    def _build_layout(self):
        self._build_header()

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True)

        self._build_sidebar(body)

        nb_frame = tk.Frame(body, bg=C["bg"])
        nb_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT,
                      padx=(0, 10), pady=(0, 10))

        self.notebook = ttk.Notebook(nb_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self._tab_chat     = self._make_tab("💬  Chat")
        self._tab_files    = self._make_tab("📂  Files")
        self._tab_system   = self._make_tab("🖥️  System")
        self._tab_notifs   = self._make_tab("🔔  Alerts")
        self._tab_text     = self._make_tab("📖  Text Reader")
        self._tab_settings = self._make_tab("⚙️  Settings")

        self._build_chat_tab()
        self._build_files_tab()
        self._build_system_tab()
        self._build_notifs_tab()
        self._build_text_tab()
        self._build_settings_tab()

        self._build_statusbar()

    def _make_tab(self, title):
        f = tk.Frame(self.notebook, bg=C["surface2"])
        self.notebook.add(f, text=title)
        return f

    # ──────────────────────────── Header ──────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["surface"], height=64)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        logo_f = tk.Frame(hdr, bg=C["surface"])
        logo_f.pack(side=tk.LEFT, padx=(20, 0), pady=12)

        self._glow = tk.Label(logo_f, text="●", font=("Segoe UI", 14),
                              bg=C["surface"], fg=C["accent"])
        self._glow.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(logo_f, text="ANYA",
                 font=("Segoe UI", 16, "bold"),
                 bg=C["surface"], fg=C["text"]).pack(side=tk.LEFT)

        tk.Label(logo_f, text="  AI Desktop Assistant",
                 font=("Segoe UI", 10),
                 bg=C["surface"], fg=C["text_dim"]).pack(side=tk.LEFT)

        right_f = tk.Frame(hdr, bg=C["surface"])
        right_f.pack(side=tk.RIGHT, padx=20, pady=8)

        # Continuous voice toggle button (header)
        self._voice_txt = tk.StringVar(value="  🎙  Voice: OFF  ")
        self._voice_btn = tk.Button(
            right_f, textvariable=self._voice_txt,
            font=FONT_SMALL, bg=C["surface3"], fg=C["text_dim"],
            activebackground=C["hover"], relief="flat", bd=0,
            cursor="hand2", command=self._toggle_voice, padx=4,
        )
        self._voice_btn.pack(side=tk.RIGHT, padx=(8, 0), ipady=5)

        self._clock_var = tk.StringVar()
        tk.Label(right_f, textvariable=self._clock_var,
                 font=("Consolas", 11), bg=C["surface"],
                 fg=C["green"]).pack(side=tk.RIGHT, padx=12)

        self._ai_pill_var = tk.StringVar(value="  Built-in  ")
        self._ai_pill = tk.Label(right_f, textvariable=self._ai_pill_var,
                                 font=FONT_SMALL, bg=C["surface3"],
                                 fg=C["text_muted"], padx=6, pady=3)
        self._ai_pill.pack(side=tk.RIGHT, padx=4)

        self._update_ai_pill()

    def _update_ai_pill(self):
        if self.ai.use_gemini:
            self._ai_pill_var.set("  ✦ Gemini AI  ")
            self._ai_pill.config(bg=C["accent_dim"], fg="#ffffff")
        else:
            self._ai_pill_var.set("  Built-in  ")
            self._ai_pill.config(bg=C["surface3"], fg=C["text_muted"])

    # ──────────────────────────── Sidebar ─────────────────────────────

    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=C["surface"], width=210)
        sb.pack(fill=tk.Y, side=tk.LEFT, padx=(10, 6), pady=(0, 10))
        sb.pack_propagate(False)

        card = tk.Frame(sb, bg=C["surface3"])
        card.pack(fill=tk.X, padx=8, pady=(12, 4))

        avatar = tk.Label(card, text="👩‍💼", font=("Segoe UI", 22),
                          bg=C["surface3"], fg=C["text"])
        avatar.pack(padx=12, pady=(10, 2))
        self._user_label = tk.Label(card, text=self.ai.user_name,
                                    font=FONT_BODY_B, bg=C["surface3"],
                                    fg=C["text"], wraplength=160)
        self._user_label.pack(pady=(0, 8))

        tk.Frame(sb, bg=C["border"], height=1).pack(fill=tk.X, padx=8, pady=6)
        self._sb_label("QUICK ACTIONS", sb)

        actions = [
            ("📂", "File Manager",    "open file manager"),
            ("📸", "Screenshot",      "take screenshot"),
            ("🔔", "Notifications",   "show notifications"),
            ("📖", "Read Screen",     "read this text"),
            ("🧮", "Calculator",      "open calculator"),
            ("🌐", "Browser",         "open chrome"),
            ("📝", "Notepad",         "open notepad"),
            ("⏰", "Time",            "what time is it"),
            ("😄", "Joke",            "tell me a joke"),
            ("❓", "Help",            "help"),
        ]

        for icon, label, cmd in actions:
            self._sidebar_btn(sb, icon, label, lambda c=cmd: self._quick_cmd(c))

        tk.Frame(sb, bg=C["border"], height=1).pack(fill=tk.X, padx=8, pady=8)
        self._sb_label("STATUS", sb)

        self._voice_status_var = tk.StringVar(value="🔇  Voice: Off")
        tk.Label(sb, textvariable=self._voice_status_var,
                 font=FONT_SMALL, bg=C["surface"],
                 fg=C["text_muted"], anchor="w").pack(fill=tk.X, padx=16, pady=1)

        self._notif_count_var = tk.StringVar(value="🔔  Notifications: 1")
        tk.Label(sb, textvariable=self._notif_count_var,
                 font=FONT_SMALL, bg=C["surface"],
                 fg=C["text_muted"], anchor="w").pack(fill=tk.X, padx=16, pady=1)

    def _sb_label(self, text, parent):
        tk.Label(parent, text=text, font=("Segoe UI", 7, "bold"),
                 bg=C["surface"], fg=C["text_muted"],
                 anchor="w").pack(fill=tk.X, padx=16, pady=(6, 2))

    def _sidebar_btn(self, parent, icon, label, cmd):
        row = tk.Frame(parent, bg=C["surface"], cursor="hand2")
        row.pack(fill=tk.X, padx=8, pady=1)

        def on_enter(e):
            row.config(bg=C["hover"])
            icon_lbl.config(bg=C["hover"])
            txt_lbl.config(bg=C["hover"])

        def on_leave(e):
            row.config(bg=C["surface"])
            icon_lbl.config(bg=C["surface"])
            txt_lbl.config(bg=C["surface"])

        icon_lbl = tk.Label(row, text=icon, font=("Segoe UI", 11),
                            bg=C["surface"], fg=C["accent"], width=3)
        icon_lbl.pack(side=tk.LEFT, padx=(6, 0), pady=4)

        txt_lbl = tk.Label(row, text=label, font=FONT_BODY,
                           bg=C["surface"], fg=C["text"], anchor="w")
        txt_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=4)

        for w in (row, icon_lbl, txt_lbl):
            w.bind("<Button-1>", lambda e, c=cmd: c())
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    # ──────────────────────────── Chat Tab ────────────────────────────

    def _build_chat_tab(self):
        tab = self._tab_chat

        # ── Voice indicator bar (hidden by default) ──
        self._voice_bar = tk.Frame(tab, bg=C["surface3"], height=34)
        # not packed initially; shown when mic is active

        self._voice_bar_label = tk.Label(
            self._voice_bar, text="🎙️  Listening… speak now",
            font=("Segoe UI", 9, "bold"),
            bg=C["surface3"], fg=C["mic_active"]
        )
        self._voice_bar_label.pack(side=tk.LEFT, padx=14, pady=6)

        self._voice_bar_cancel = tk.Button(
            self._voice_bar, text="✕ Cancel",
            font=FONT_SMALL, bg=C["surface3"], fg=C["text_muted"],
            relief="flat", cursor="hand2",
            command=self._cancel_voice_listen
        )
        self._voice_bar_cancel.pack(side=tk.RIGHT, padx=10)

        # ── Chat display ──
        self.chat_display = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD,
            font=FONT_CHAT, bg=C["bg"], fg=C["text"],
            insertbackground=C["accent2"],
            selectbackground=C["accent_dim"],
            relief="flat", bd=0, state=tk.DISABLED,
            padx=16, pady=12,
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Text tags
        cd = self.chat_display
        cd.tag_configure("user_lbl",  foreground=C["tag_user"],  font=FONT_CHAT_B)
        cd.tag_configure("anya_lbl",  foreground=C["tag_anya"],  font=FONT_CHAT_B)
        cd.tag_configure("msg",       foreground=C["text"])
        cd.tag_configure("sys",       foreground=C["text_muted"], font=("Segoe UI", 9, "italic"))
        cd.tag_configure("success",   foreground=C["green"])
        cd.tag_configure("error",     foreground=C["red"])
        cd.tag_configure("warn",      foreground=C["yellow"])
        cd.tag_configure("dim",       foreground=C["text_dim"])
        cd.tag_configure("gold",      foreground=C["gold"])
        cd.tag_configure("voice_in",  foreground=C["purple"],   font=("Segoe UI", 9, "italic"))

        # ── Input area ──
        inp_wrap = tk.Frame(tab, bg=C["surface"])
        inp_wrap.pack(fill=tk.X)

        inp_inner = tk.Frame(inp_wrap, bg=C["surface"])
        inp_inner.pack(fill=tk.X, padx=12, pady=10)

        # Input field
        inp_frame = tk.Frame(inp_inner, bg=C["input_bg"], highlightthickness=1,
                             highlightbackground=C["border2"])
        inp_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self.chat_input = tk.Entry(
            inp_frame, font=("Segoe UI", 11),
            bg=C["input_bg"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", bd=0,
        )
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True,
                             ipady=9, padx=12)
        self.chat_input.bind("<Return>", self._on_send)
        self.chat_input.bind("<Up>", self._history_prev)
        self.chat_input.bind("<Down>", self._history_next)

        def focus_in(e):
            inp_frame.config(highlightbackground=C["accent_dim"])
        def focus_out(e):
            inp_frame.config(highlightbackground=C["border2"])
        self.chat_input.bind("<FocusIn>", focus_in)
        self.chat_input.bind("<FocusOut>", focus_out)

        # ── Mic button (one-shot voice input) ──
        self._mic_btn = tk.Button(
            inp_frame, text="🎙",
            font=("Segoe UI", 13),
            bg=C["input_bg"], fg=C["mic_idle"],
            activebackground=C["input_bg"], activeforeground=C["mic_active"],
            relief="flat", bd=0, cursor="hand2",
            command=self._listen_once,
        )
        self._mic_btn.pack(side=tk.RIGHT, padx=8, pady=4)
        self._add_tooltip(self._mic_btn, "Click to speak (one-shot)")

        # Send button
        send_btn = tk.Button(
            inp_inner, text="Send",
            font=FONT_BODY_B, bg=C["accent"], fg=C["bg"],
            activebackground=C["accent2"], activeforeground=C["bg"],
            relief="flat", bd=0, cursor="hand2",
            command=lambda: self._on_send(None), padx=20,
        )
        send_btn.pack(side=tk.LEFT, ipady=8)

        # Welcome message
        self._anya_message(
            f"Hello, {self.ai.user_name}! 🌟\n"
            "I'm Anya, your AI desktop assistant.\n"
            "Type or click 🎙 to speak — I'll answer right here in chat.\n"
            "Try saying: 'What time is it?' or 'Tell me a joke' or 'Help'."
        )
        self.chat_input.focus_set()

    def _add_tooltip(self, widget, text):
        """Simple tooltip on hover."""
        tip = None
        def show(e):
            nonlocal tip
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() - 28
            tip = tk.Toplevel(widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}")
            tk.Label(tip, text=text, font=FONT_SMALL,
                     bg=C["surface3"], fg=C["text_dim"],
                     relief="flat", padx=6, pady=3).pack()
        def hide(e):
            nonlocal tip
            if tip:
                tip.destroy()
                tip = None
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    # ──────────────────────────── Files Tab ───────────────────────────

    def _build_files_tab(self):
        tab = self._tab_files
        home = os.path.expanduser("~")
        self._current_path = tk.StringVar(value=home)

        pb = tk.Frame(tab, bg=C["surface3"])
        pb.pack(fill=tk.X)
        inner_pb = tk.Frame(pb, bg=C["surface3"])
        inner_pb.pack(fill=tk.X, padx=10, pady=8)

        tk.Label(inner_pb, text="📂", font=("Segoe UI", 11),
                 bg=C["surface3"], fg=C["accent"]).pack(side=tk.LEFT, padx=(0, 4))

        path_entry = tk.Entry(inner_pb, textvariable=self._current_path,
                              font=FONT_MONO, bg=C["input_bg"], fg=C["accent2"],
                              relief="flat", insertbackground=C["accent"])
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=4)
        path_entry.bind("<Return>", lambda e: self._file_browse(self._current_path.get()))

        for text, cmd, color in [
            ("Go",      lambda: self._file_browse(self._current_path.get()), C["accent"]),
            ("Home",    lambda: self._file_browse(home),                     C["surface3"]),
            ("↑ Up",    self._file_go_up,                                    C["surface3"]),
            ("Explorer",lambda: self._file_output(self.file_mgr.open_file_manager()), C["gold"]),
        ]:
            fg = C["bg"] if color == C["accent"] else C["text"]
            tk.Button(inner_pb, text=text, font=FONT_SMALL,
                      bg=color, fg=fg, relief="flat", cursor="hand2",
                      command=cmd, padx=8).pack(side=tk.LEFT, padx=2, ipady=4)

        main_f = tk.Frame(tab, bg=C["surface2"])
        main_f.pack(fill=tk.BOTH, expand=True)

        list_wrap = tk.Frame(main_f, bg=C["surface2"])
        list_wrap.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 4))

        sb = ttk.Scrollbar(list_wrap)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        self.file_list = tk.Listbox(
            list_wrap, font=FONT_MONO,
            bg=C["surface"], fg=C["text"],
            selectbackground=C["accent_dim"], selectforeground=C["bg"],
            relief="flat", bd=0, yscrollcommand=sb.set, activestyle="none",
        )
        self.file_list.pack(fill=tk.BOTH, expand=True)
        sb.config(command=self.file_list.yview)
        self.file_list.bind("<Double-Button-1>", self._file_double_click)

        act = tk.Frame(tab, bg=C["surface"])
        act.pack(fill=tk.X, padx=10, pady=4)

        for text, cmd in [
            ("Open",        self._file_open_selected),
            ("New File",    self._file_create_dialog),
            ("New Folder",  self._file_create_folder_dialog),
            ("Delete",      self._file_delete_selected),
            ("Info",        self._file_info_selected),
        ]:
            is_del = text == "Delete"
            tk.Button(act, text=text, font=FONT_SMALL,
                      bg=C["red"] if is_del else C["surface3"],
                      fg=C["text"], relief="flat", cursor="hand2",
                      command=cmd, padx=10).pack(side=tk.LEFT, padx=3, ipady=4)

        sf = tk.Frame(tab, bg=C["surface2"])
        sf.pack(fill=tk.X, padx=10, pady=(0, 6))

        self._search_var = tk.StringVar()
        se = tk.Entry(sf, textvariable=self._search_var,
                      font=FONT_BODY, bg=C["input_bg"], fg=C["text"],
                      relief="flat", insertbackground=C["accent"])
        se.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 6))
        se.bind("<Return>", lambda e: self._file_search())

        tk.Button(sf, text="🔍 Search", font=FONT_SMALL,
                  bg=C["accent"], fg=C["bg"], relief="flat",
                  cursor="hand2", command=self._file_search,
                  padx=12).pack(side=tk.LEFT, ipady=5)

        self.file_output = scrolledtext.ScrolledText(
            tab, height=5, font=FONT_MONO,
            bg=C["surface"], fg=C["green"],
            relief="flat", bd=0, state=tk.DISABLED,
        )
        self.file_output.pack(fill=tk.X)

        self._file_browse(home)

    # ──────────────────────────── System Tab ──────────────────────────

    def _build_system_tab(self):
        tab = self._tab_system
        canvas = tk.Frame(tab, bg=C["surface2"])
        canvas.pack(fill=tk.BOTH, expand=True)

        tk.Label(canvas, text="System Control",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["surface2"], fg=C["text"]).pack(pady=(20, 4))
        tk.Label(canvas, text="Manage your system with one click",
                 font=FONT_SMALL, bg=C["surface2"], fg=C["text_muted"]).pack(pady=(0, 16))

        grid = tk.Frame(canvas, bg=C["surface2"])
        grid.pack()

        btns = [
            ("🔊 Volume Up",    lambda: self._sys(self.sys_ctrl.volume_up),    C["accent_dim"], 0, 0),
            ("🔉 Volume Down",  lambda: self._sys(self.sys_ctrl.volume_down),  C["surface3"],  0, 1),
            ("🔇 Mute",        lambda: self._sys(self.sys_ctrl.mute),          C["surface3"],  0, 2),
            ("💡 Brighter",    lambda: self._sys(self.sys_ctrl.brightness_up), C["gold_dim"],  1, 0),
            ("🌙 Dimmer",      lambda: self._sys(self.sys_ctrl.brightness_down),C["surface3"], 1, 1),
            ("📸 Screenshot",  lambda: self._sys(self.sys_ctrl.take_screenshot),C["purple"],   1, 2),
            ("⏻ Shutdown",    self._confirm_shutdown,                          C["red"],       2, 0),
            ("🔄 Restart",     self._confirm_restart,                          "#7f1d1d",      2, 1),
            ("✕ Cancel Timer", lambda: self._sys(self.sys_ctrl.cancel_shutdown), C["surface3"],2, 2),
        ]

        for text, cmd, color, row, col in btns:
            tk.Button(grid, text=text, font=FONT_BODY,
                      bg=color, fg=C["text"],
                      activebackground=C["hover"], relief="flat",
                      cursor="hand2", command=cmd,
                      width=16, height=2).grid(row=row, column=col, padx=8, pady=6)

        tk.Frame(canvas, bg=C["border"], height=1).pack(fill=tk.X, padx=24, pady=12)
        tk.Label(canvas, text="Launch Application",
                 font=FONT_HDR, bg=C["surface2"], fg=C["text_dim"]).pack()

        lf = tk.Frame(canvas, bg=C["surface2"])
        lf.pack(pady=8)

        self._app_entry = tk.Entry(lf, font=FONT_BODY, bg=C["input_bg"], fg=C["text"],
                                   relief="flat", insertbackground=C["accent"], width=28)
        self._app_entry.pack(side=tk.LEFT, ipady=7, padx=(0, 8))
        self._app_entry.bind("<Return>", lambda e: self._launch_app())

        tk.Button(lf, text="Launch 🚀", font=FONT_BODY_B,
                  bg=C["accent"], fg=C["bg"], relief="flat",
                  cursor="hand2", command=self._launch_app,
                  padx=16).pack(side=tk.LEFT, ipady=6)

        chip_f = tk.Frame(canvas, bg=C["surface2"])
        chip_f.pack(pady=4)

        for app in ["Chrome", "Firefox", "Notepad", "Calculator", "VS Code", "Terminal", "Spotify"]:
            tk.Button(chip_f, text=app, font=FONT_SMALL,
                      bg=C["surface3"], fg=C["text_dim"],
                      activebackground=C["hover"], activeforeground=C["accent"],
                      relief="flat", cursor="hand2",
                      command=lambda a=app.lower(): self._sys(lambda: self.sys_ctrl.open_app(a)),
                      padx=10).pack(side=tk.LEFT, padx=3, ipady=4)

        self.sys_output = scrolledtext.ScrolledText(
            canvas, height=8, font=FONT_MONO,
            bg=C["surface"], fg=C["green"],
            relief="flat", bd=0, state=tk.DISABLED,
        )
        self.sys_output.pack(fill=tk.X, padx=24, pady=(12, 8))

    # ──────────────────────────── Notifications Tab ───────────────────

    def _build_notifs_tab(self):
        tab = self._tab_notifs

        tb = tk.Frame(tab, bg=C["surface3"])
        tb.pack(fill=tk.X)
        inner_tb = tk.Frame(tb, bg=C["surface3"])
        inner_tb.pack(fill=tk.X, padx=12, pady=8)

        tk.Label(inner_tb, text="Notification Center",
                 font=FONT_HDR, bg=C["surface3"], fg=C["text"]).pack(side=tk.LEFT)

        for text, cmd, color in [
            ("Refresh",       self._notif_refresh, C["accent"]),
            ("Mark All Read", self._notif_mark_read, C["surface"]),
        ]:
            tk.Button(inner_tb, text=text, font=FONT_SMALL,
                      bg=color, fg=C["bg"] if color == C["accent"] else C["text"],
                      relief="flat", cursor="hand2", command=cmd,
                      padx=12).pack(side=tk.RIGHT, padx=4, ipady=4)

        self.notif_display = scrolledtext.ScrolledText(
            tab, font=FONT_CHAT, bg=C["surface2"], fg=C["text"],
            relief="flat", bd=0, state=tk.DISABLED, padx=12, pady=8,
        )
        self.notif_display.pack(fill=tk.BOTH, expand=True)
        self.notif_display.tag_configure("title",  foreground=C["accent2"], font=FONT_BODY_B)
        self.notif_display.tag_configure("body",   foreground=C["text"])
        self.notif_display.tag_configure("meta",   foreground=C["text_muted"], font=FONT_SMALL)
        self.notif_display.tag_configure("unread", foreground=C["gold"])

        pf = tk.Frame(tab, bg=C["surface"])
        pf.pack(fill=tk.X)
        inner_pf = tk.Frame(pf, bg=C["surface"])
        inner_pf.pack(fill=tk.X, padx=10, pady=8)

        self._notif_msg = tk.Entry(inner_pf, font=FONT_BODY,
                                   bg=C["input_bg"], fg=C["text"],
                                   relief="flat", insertbackground=C["accent"])
        self._notif_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self._notif_msg.insert(0, "Custom notification message…")

        tk.Button(inner_pf, text="📢 Push",
                  font=FONT_BODY_B, bg=C["accent"], fg=C["bg"],
                  relief="flat", cursor="hand2",
                  command=self._push_custom_notif,
                  padx=12).pack(side=tk.LEFT, ipady=5)

        self._notif_refresh()

    # ──────────────────────────── Text Reader ─────────────────────────

    def _build_text_tab(self):
        tab = self._tab_text

        hdr = tk.Frame(tab, bg=C["surface3"])
        hdr.pack(fill=tk.X)
        inner = tk.Frame(hdr, bg=C["surface3"])
        inner.pack(fill=tk.X, padx=12, pady=10)

        tk.Label(inner, text="Text Reader & OCR",
                 font=FONT_HDR, bg=C["surface3"], fg=C["text"]).pack(side=tk.LEFT)

        for text, cmd in [
            ("📋 Clipboard",   self._read_clipboard),
            ("🖥️ Capture OCR", self._ocr_screen),
            ("📄 Open File",   self._read_file),
            ("🔊 Speak",       self._speak_text_area),
            ("🗑️ Clear",       self._clear_text_area),
        ]:
            tk.Button(inner, text=text, font=FONT_SMALL,
                      bg=C["surface"], fg=C["text"],
                      activebackground=C["hover"], relief="flat",
                      cursor="hand2", command=cmd, padx=10).pack(side=tk.RIGHT, padx=3, ipady=4)

        self.text_area = scrolledtext.ScrolledText(
            tab, font=FONT_MONO, bg=C["surface2"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", bd=0,
            padx=12, pady=12,
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        if not OCR_AVAILABLE:
            self.text_area.insert(tk.END,
                "ℹ️  OCR requires:\n"
                "  pip install pytesseract pillow\n\n"
                "Also install Tesseract OCR:\n"
                "  https://github.com/UB-Mannheim/tesseract/wiki\n\n"
                "Clipboard & file reading work without OCR.")

    # ──────────────────────────── Settings ────────────────────────────

    def _build_settings_tab(self):
        tab = self._tab_settings

        canvas = tk.Frame(tab, bg=C["surface2"])
        canvas.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        tk.Label(canvas, text="Settings",
                 font=("Segoe UI", 14, "bold"),
                 bg=C["surface2"], fg=C["text"]).pack(anchor="w", pady=(0, 4))
        tk.Label(canvas, text="Configure Anya's AI backend and preferences",
                 font=FONT_SMALL, bg=C["surface2"], fg=C["text_muted"]).pack(anchor="w", pady=(0, 20))

        self._section_label(canvas, "🤖 GEMINI AI")
        self._row(canvas, "Gemini API Key:", "gemini_key", show="*",
                  hint="Get your key at: aistudio.google.com")
        self._row(canvas, "Your Name:",      "user_name", default=self.ai.user_name)
        self._row(canvas, "Speech Rate (wpm):", "tts_rate", default="175")

        tk.Button(canvas, text="  💾  Save & Apply  ",
                  font=FONT_BODY_B, bg=C["accent"], fg=C["bg"],
                  relief="flat", cursor="hand2",
                  command=self._save_settings,
                  padx=4).pack(anchor="w", pady=16, ipady=6)

        self._section_label(canvas, "📦 DEPENDENCIES")
        info = (
            "pip install google-generativeai SpeechRecognition pyttsx3 pyaudio\n"
            "pip install pyautogui pytesseract pillow psutil requests\n\n"
            "Tesseract OCR (for screen reading):\n"
            "  → https://github.com/UB-Mannheim/tesseract/wiki\n\n"
            "Environment variable alternative:\n"
            "  GEMINI_API_KEY=your-key-here python main.py"
        )
        info_box = tk.Text(canvas, font=FONT_MONO, bg=C["surface"],
                           fg=C["text_dim"], relief="flat", bd=0,
                           height=7, state=tk.NORMAL)
        info_box.insert(tk.END, info)
        info_box.config(state=tk.DISABLED)
        info_box.pack(fill=tk.X, pady=(4, 0))

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 7, "bold"),
                 bg=C["surface2"], fg=C["text_muted"],
                 anchor="w").pack(fill=tk.X, pady=(8, 4))

    def _row(self, parent, label, key, default="", show="", hint=""):
        row = tk.Frame(parent, bg=C["surface2"])
        row.pack(fill=tk.X, pady=4)

        tk.Label(row, text=label, font=FONT_BODY,
                 bg=C["surface2"], fg=C["text_dim"],
                 width=22, anchor="w").pack(side=tk.LEFT)

        entry = tk.Entry(row, font=FONT_BODY, bg=C["input_bg"],
                         fg=C["text"], relief="flat",
                         insertbackground=C["accent"], show=show, width=36)
        if default:
            entry.insert(0, default)
        entry.pack(side=tk.LEFT, ipady=6, padx=8)

        if hint:
            tk.Label(row, text=hint, font=("Segoe UI", 7),
                     bg=C["surface2"], fg=C["text_muted"]).pack(side=tk.LEFT)

        self._settings_entries[key] = entry

    # ──────────────────────────── Status bar ──────────────────────────

    def _build_statusbar(self):
        sb = tk.Frame(self.root, bg=C["surface"], height=26)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        sb.pack_propagate(False)

        self._status_var = tk.StringVar(value="✅  Anya is ready")
        tk.Label(sb, textvariable=self._status_var,
                 font=FONT_SMALL, bg=C["surface"],
                 fg=C["text_dim"], anchor="w").pack(side=tk.LEFT, padx=14)

        self._listen_dot = tk.Label(sb, text="⚫",
                                    font=("Segoe UI", 10),
                                    bg=C["surface"], fg=C["text_muted"])
        self._listen_dot.pack(side=tk.RIGHT, padx=12)

        tk.Label(sb, text=f"Python {sys.version.split()[0]}  ·  {platform.system()}",
                 font=FONT_SMALL, bg=C["surface"],
                 fg=C["text_muted"]).pack(side=tk.RIGHT, padx=12)

    # ══════════════════════════════════════════════════════════════════
    #  Callbacks
    # ══════════════════════════════════════════════════════════════════

    def _wire_callbacks(self):
        self.listener.set_callbacks(
            on_text=self._on_voice_text,
            on_status=self._on_voice_status,
        )
        self.notifier.add_callback(self._on_new_notification)

    # ══════════════════════════════════════════════════════════════════
    #  Background tasks
    # ══════════════════════════════════════════════════════════════════

    def _start_background_tasks(self):
        self._update_clock()
        self.notifier.start_monitoring()
        self._pulse_glow()

    def _update_clock(self):
        now = datetime.datetime.now()
        self._clock_var.set(now.strftime("%I:%M:%S %p  ·  %a %b %d"))
        self.root.after(1000, self._update_clock)

    def _pulse_glow(self):
        colors = [C["accent"], C["accent_dim"], C["accent2"]]
        self._pulse_idx = (getattr(self, "_pulse_idx", 0) + 1) % len(colors)
        self._glow.config(fg=colors[self._pulse_idx])
        self.root.after(1200, self._pulse_glow)

    # ══════════════════════════════════════════════════════════════════
    #  Core input processing
    # ══════════════════════════════════════════════════════════════════

    def _on_send(self, event):
        text = self.chat_input.get().strip()
        if not text:
            return
        self.chat_input.delete(0, tk.END)
        self._input_history.append(text)
        self._history_idx = len(self._input_history)
        self._process_input(text, source="text")

    def _on_voice_text(self, text: str):
        """Called from continuous voice listener thread."""
        if text == "__wake_word__":
            self.root.after(0, lambda: self._anya_message(
                "🌟 Yes? I'm listening! What would you like me to do?"))
            self.speaker.speak("Yes? How can I help you?", priority=True)
            return
        # Voice input — show in chat and process
        self.root.after(0, lambda: self._process_input(text, source="voice"))

    def _on_voice_status(self, status: str):
        self.root.after(0, lambda: self._set_status(status))
        is_on = any(k in status for k in ["Listening", "active", "activated"])
        color = C["green"] if is_on else C["text_muted"]
        dot   = "🟢" if is_on else "⚫"
        self.root.after(0, lambda: self._listen_dot.config(fg=color, text=dot))

    def _on_new_notification(self, notif):
        self.root.after(0, self._notif_refresh)
        count = len(self.notifier.get_unread())
        self.root.after(0, lambda: self._notif_count_var.set(f"🔔  Unread: {count}"))

    def _history_prev(self, event):
        if self._input_history and self._history_idx > 0:
            self._history_idx -= 1
            self.chat_input.delete(0, tk.END)
            self.chat_input.insert(0, self._input_history[self._history_idx])

    def _history_next(self, event):
        if self._history_idx < len(self._input_history) - 1:
            self._history_idx += 1
            self.chat_input.delete(0, tk.END)
            self.chat_input.insert(0, self._input_history[self._history_idx])
        else:
            self._history_idx = len(self._input_history)
            self.chat_input.delete(0, tk.END)

    def _process_input(self, text: str, source: str = "text"):
        """
        Central dispatcher — shows user message in chat, runs AI, shows response.
        source: 'text' | 'voice'
        """
        # Always switch to chat tab so response is visible
        self.notebook.select(0)

        # Show user message with voice indicator if spoken
        if source == "voice":
            self._user_message(text, voice=True)
        else:
            self._user_message(text, voice=False)

        self._set_status(
            f"🧠  Processing: '{text[:40]}…'" if len(text) > 40
            else f"🧠  Processing: '{text}'"
        )

        # Confirmation flow
        if self._pending_confirm:
            low = text.lower()
            if any(w in low for w in ["yes", "confirm", "ok", "sure", "do it", "proceed"]):
                action, fn = self._pending_confirm
                self._pending_confirm = None
                result = fn()
                self._anya_message(result)
                self.speaker.speak(result)
            else:
                self._pending_confirm = None
                self._anya_message("❎ Action cancelled.")
            return

        threading.Thread(target=self._ai_worker, args=(text,), daemon=True).start()

    def _ai_worker(self, text: str):
        result = self.ai.process_command(text)
        resp   = result["response"]
        action = result["action"]
        params = result.get("params", {})
        extra  = self._execute_action(action, params)
        self.root.after(0, lambda: self._finalize(resp, extra, action))

    def _finalize(self, resp: str, extra: str, action: str):
        """Show AI response + any system action result in chat."""
        self._anya_message(resp)

        # Show system action result in chat too (if different from AI response)
        if extra and extra.strip() and extra.strip() != resp.strip():
            tag = "success" if any(s in extra for s in ["✅", "📸", "📂", "🔊", "🔉", "🔇", "💡"]) else \
                  "warn"    if "⚠️" in extra else \
                  "error"   if "❌" in extra else "sys"
            self._chat_sys(extra, tag)

        self.speaker.speak(resp)
        self._set_status("✅  Ready")

    # ══════════════════════════════════════════════════════════════════
    #  Action dispatcher
    # ══════════════════════════════════════════════════════════════════

    def _execute_action(self, action: str, params: dict) -> str:
        if not action:
            return ""
        if action == "exit":
            self.root.after(600, self._on_close); return ""
        if action == "get_time":
            t = self.sys_ctrl.get_time()
            return f"⏰ Current time: {t}"
        if action == "get_date":
            d = self.sys_ctrl.get_date()
            return f"📅 Today: {d}"
        if action == "open_app":
            return self.sys_ctrl.open_app(params.get("app", ""))
        if action == "close_app":
            return self.sys_ctrl.close_app(params.get("app", ""))
        if action == "volume_up":
            return self.sys_ctrl.volume_up()
        if action == "volume_down":
            return self.sys_ctrl.volume_down()
        if action == "mute":
            return self.sys_ctrl.mute()
        if action == "brightness_up":
            return self.sys_ctrl.brightness_up()
        if action == "brightness_down":
            return self.sys_ctrl.brightness_down()
        if action == "shutdown":
            self.root.after(0, self._confirm_shutdown); return ""
        if action == "restart":
            self.root.after(0, self._confirm_restart); return ""
        if action == "open_file_manager":
            self.root.after(200, lambda: self.notebook.select(1))
            return self.file_mgr.open_file_manager()
        if action == "open_file":
            return self.file_mgr.open_file(params.get("path", ""))
        if action == "create_file":
            return self.file_mgr.create_file(params.get("name", "new_file.txt"))
        if action == "delete_file":
            path = params.get("path", "")
            self._pending_confirm = ("delete_file", lambda: self.file_mgr.delete_file(path))
            return ""
        if action == "search_files":
            q = params.get("query", "")
            out = self.file_mgr.search_and_format(q)
            self.root.after(200, lambda: self._file_output(out))
            return out
        if action == "take_screenshot":
            return self.sys_ctrl.take_screenshot()
        if action == "show_notifications":
            self.root.after(200, lambda: self.notebook.select(3))
            self.root.after(300, self._notif_refresh)
            return "🔔 Switched to Notifications tab."
        if action == "read_screen":
            self.root.after(200, lambda: self.notebook.select(4))
            self.root.after(300, self._ocr_screen)
            return "📖 Opening Text Reader tab."
        if action == "calculate":
            import re
            expr = params.get("expr", "")
            if expr:
                try:
                    safe = re.sub(r"[^0-9\+\-\*/\(\)\.\s%]", "", expr)
                    result = eval(safe)
                    return f"🧮 {safe.strip()} = {result}"
                except Exception:
                    return ""
            return ""
        if action == "get_weather":
            return "🌤️ Connect a weather API in Settings for live weather."
        return ""

    # ══════════════════════════════════════════════════════════════════
    #  Chat helpers
    # ══════════════════════════════════════════════════════════════════

    def _user_message(self, text: str, voice: bool = False):
        """Show user message bubble. voice=True adds mic indicator."""
        prefix = "\n🎙  You (voice)   " if voice else "\n👤  You    "
        tag    = "voice_in"            if voice else "user_lbl"
        self._chat_append(prefix, tag)
        self._chat_append(f"{text}\n", "msg")

    def _anya_message(self, text: str):
        self._chat_append("\n✦  Anya   ", "anya_lbl")
        self._chat_append(f"{text}\n", "msg")
        self._scroll_chat()

    def _chat_sys(self, text: str, tag: str = "sys"):
        """Show a system/action result line in chat (indented)."""
        self._chat_append(f"     → {text}\n", tag)
        self._scroll_chat()

    def _chat_append(self, text: str, tag: str = ""):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text, tag)
        self.chat_display.config(state=tk.DISABLED)

    def _scroll_chat(self):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    # ══════════════════════════════════════════════════════════════════
    #  Voice controls
    # ══════════════════════════════════════════════════════════════════

    def _toggle_voice(self):
        """Toggle continuous 'Hey Anya' wake-word listening."""
        if self._voice_active:
            self.listener.stop_listening()
            self._voice_active = False
            self._voice_txt.set("  🎙  Voice: OFF  ")
            self._voice_btn.config(bg=C["surface3"], fg=C["text_dim"])
            self._voice_status_var.set("🔇  Voice: Off")
            self._chat_sys("🔇 Continuous voice listening stopped.", "dim")
        else:
            self.listener.start_continuous_listening()
            self._voice_active = True
            self._voice_txt.set("  🎙  Voice: ON  ")
            self._voice_btn.config(bg=C["green"], fg=C["bg"])
            self._voice_status_var.set("👂  Listening…")
            self._anya_message(
                "🎙️ Voice activated!\n"
                "Say 'Hey Anya' then speak your command.\n"
                "Everything you say (and my replies) will appear here in chat."
            )

    def _listen_once(self):
        """One-shot mic button: listen for one utterance, process it."""
        if self._mic_listening:
            return  # already listening
        self._mic_listening = True

        # Show voice indicator bar above chat
        self._voice_bar.pack(fill=tk.X, before=self.chat_display)
        self._mic_btn.config(fg=C["mic_active"], font=("Segoe UI", 13, "bold"))

        self._set_status("🎙️  Listening…")
        threading.Thread(target=self._do_listen_once, daemon=True).start()

    def _do_listen_once(self):
        text = self.listener.listen_once()

        def finish():
            self._mic_listening = False
            self._voice_bar.pack_forget()
            self._mic_btn.config(fg=C["mic_idle"], font=("Segoe UI", 13))

            if text:
                self._process_input(text, source="voice")
            else:
                self._set_status("❓  No speech detected")
                self._chat_sys("🎙️ No speech detected — try again.", "dim")

        self.root.after(0, finish)

    def _cancel_voice_listen(self):
        """Cancel the one-shot listen."""
        # We can't abort the blocking listen_once easily,
        # but we hide the bar and mark it done so the result is ignored.
        self._mic_listening = False
        self._voice_bar.pack_forget()
        self._mic_btn.config(fg=C["mic_idle"], font=("Segoe UI", 13))
        self._set_status("✅  Ready")

    # ══════════════════════════════════════════════════════════════════
    #  Quick command
    # ══════════════════════════════════════════════════════════════════

    def _quick_cmd(self, cmd: str):
        self.notebook.select(0)
        self._process_input(cmd, source="text")

    # ══════════════════════════════════════════════════════════════════
    #  File tab
    # ══════════════════════════════════════════════════════════════════

    def _file_browse(self, path: str):
        path = os.path.expanduser(path)
        if not os.path.isdir(path):
            return
        self._current_path.set(path)
        self.file_list.delete(0, tk.END)
        try:
            items = sorted(os.listdir(path))
            for item in items:
                full = os.path.join(path, item)
                pfx = "📁  " if os.path.isdir(full) else "📄  "
                self.file_list.insert(tk.END, pfx + item)
        except PermissionError:
            self.file_list.insert(tk.END, "❌  Permission denied")

    def _file_go_up(self):
        cur = self._current_path.get()
        par = os.path.dirname(cur)
        if par != cur:
            self._file_browse(par)

    def _file_double_click(self, e):
        sel = self.file_list.curselection()
        if not sel: return
        item = self.file_list.get(sel[0]).lstrip("📁📄 ").strip()
        full = os.path.join(self._current_path.get(), item)
        if os.path.isdir(full):
            self._file_browse(full)
        else:
            self._file_output(self.file_mgr.open_file(full))

    def _file_open_selected(self):
        sel = self.file_list.curselection()
        if not sel: return
        item = self.file_list.get(sel[0]).lstrip("📁📄 ").strip()
        full = os.path.join(self._current_path.get(), item)
        if os.path.isdir(full):
            self._file_browse(full)
        else:
            self._file_output(self.file_mgr.open_file(full))

    def _file_create_dialog(self):
        name = simpledialog.askstring("New File", "File name:", parent=self.root)
        if name:
            self._file_output(self.file_mgr.create_file(name, folder=self._current_path.get()))
            self._file_browse(self._current_path.get())

    def _file_create_folder_dialog(self):
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self.root)
        if name:
            self._file_output(self.file_mgr.create_folder(name, parent=self._current_path.get()))
            self._file_browse(self._current_path.get())

    def _file_delete_selected(self):
        sel = self.file_list.curselection()
        if not sel: return
        item = self.file_list.get(sel[0]).lstrip("📁📄 ").strip()
        full = os.path.join(self._current_path.get(), item)
        if messagebox.askyesno("Delete", f"Move '{item}' to Anya Trash?", parent=self.root):
            self._file_output(self.file_mgr.delete_file(full))
            self._file_browse(self._current_path.get())

    def _file_info_selected(self):
        sel = self.file_list.curselection()
        if not sel: return
        item = self.file_list.get(sel[0]).lstrip("📁📄 ").strip()
        full = os.path.join(self._current_path.get(), item)
        self._file_output(self.file_mgr.get_file_info(full))

    def _file_search(self):
        q = self._search_var.get().strip()
        if not q: return
        self._file_output("🔍  Searching…")
        threading.Thread(
            target=lambda: self.root.after(0,
                lambda: self._file_output(self.file_mgr.search_and_format(q))),
            daemon=True,
        ).start()

    def _file_output(self, text: str):
        self.file_output.config(state=tk.NORMAL)
        self.file_output.delete("1.0", tk.END)
        self.file_output.insert(tk.END, text)
        self.file_output.config(state=tk.DISABLED)

    # ══════════════════════════════════════════════════════════════════
    #  System tab
    # ══════════════════════════════════════════════════════════════════

    def _sys(self, fn):
        threading.Thread(
            target=lambda: self.root.after(0, lambda: self._sys_out(fn())),
            daemon=True
        ).start()

    def _sys_out(self, text: str):
        self.sys_output.config(state=tk.NORMAL)
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.sys_output.insert(tk.END, f"[{ts}]  {text}\n")
        self.sys_output.see(tk.END)
        self.sys_output.config(state=tk.DISABLED)

    def _launch_app(self):
        app = self._app_entry.get().strip()
        if app:
            self._sys(lambda: self.sys_ctrl.open_app(app))

    def _confirm_shutdown(self):
        if messagebox.askyesno("⚠️  Shutdown",
                               "Are you sure you want to shut down?",
                               parent=self.root):
            r = self.sys_ctrl.shutdown()
            self._sys_out(r); self._anya_message(r)

    def _confirm_restart(self):
        if messagebox.askyesno("⚠️  Restart",
                               "Are you sure you want to restart?",
                               parent=self.root):
            r = self.sys_ctrl.restart()
            self._sys_out(r); self._anya_message(r)

    # ══════════════════════════════════════════════════════════════════
    #  Notifications
    # ══════════════════════════════════════════════════════════════════

    def _notif_refresh(self):
        self.notif_display.config(state=tk.NORMAL)
        self.notif_display.delete("1.0", tk.END)
        items = self.notifier.get_history(30)
        if not items:
            self.notif_display.insert(tk.END, "No notifications yet.")
        for n in items:
            icon = "🔴  " if not n.read else "⚪  "
            self.notif_display.insert(tk.END, icon, "unread" if not n.read else "meta")
            self.notif_display.insert(tk.END,
                f"[{n.timestamp.strftime('%H:%M:%S')}]  {n.source}: ", "meta")
            self.notif_display.insert(tk.END, f"{n.title}\n", "title")
            if n.message:
                self.notif_display.insert(tk.END, f"    {n.message}\n", "body")
            self.notif_display.insert(tk.END, "\n")
        self.notif_display.see(tk.END)
        self.notif_display.config(state=tk.DISABLED)
        u = len(self.notifier.get_unread())
        self._notif_count_var.set(f"🔔  Unread: {u}")

    def _notif_mark_read(self):
        self.notifier.mark_all_read()
        self._notif_refresh()

    def _push_custom_notif(self):
        msg = self._notif_msg.get().strip()
        placeholder = "Custom notification message…"
        if msg and msg != placeholder:
            self.notifier.push("Custom Alert", msg, source="You")
            self.notifier.show_desktop_notification("Anya", msg)

    # ══════════════════════════════════════════════════════════════════
    #  Text Reader
    # ══════════════════════════════════════════════════════════════════

    def _read_clipboard(self):
        try:
            text = self.root.clipboard_get()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, text)
        except Exception:
            self.text_area.insert(tk.END, "❌  Nothing in clipboard.")

    def _ocr_screen(self):
        if not OCR_AVAILABLE:
            self.text_area.insert(tk.END,
                "\n❌  OCR not available.\n"
                "Install: pip install pytesseract pillow\n"
                "Also install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki")
            return
        try:
            img = ImageGrab.grab()
            text = pytesseract.image_to_string(img)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, text or "No text detected on screen.")
        except Exception as e:
            self.text_area.insert(tk.END, f"\n❌  OCR error: {e}")

    def _read_file(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="Open Text File",
            filetypes=[("Text files", "*.txt *.md *.py *.json *.csv *.log"),
                       ("All files", "*.*")],
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    self.text_area.delete("1.0", tk.END)
                    self.text_area.insert(tk.END, f.read())
            except Exception as e:
                self.text_area.insert(tk.END, f"\n❌  Error: {e}")

    def _speak_text_area(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if text:
            self.speaker.speak(text)

    def _clear_text_area(self):
        self.text_area.delete("1.0", tk.END)

    # ══════════════════════════════════════════════════════════════════
    #  Settings
    # ══════════════════════════════════════════════════════════════════

    def _save_settings(self):
        e = self._settings_entries

        key_entry = e.get("gemini_key")
        if key_entry and key_entry.get().strip():
            self.ai.set_api_key(key_entry.get().strip())
            self._update_ai_pill()

        name_entry = e.get("user_name")
        if name_entry and name_entry.get().strip():
            name = name_entry.get().strip()
            self.ai.set_user_name(name)
            self._user_label.config(text=name)

        rate_entry = e.get("tts_rate")
        if rate_entry:
            try:
                self.speaker.set_rate(int(rate_entry.get()))
            except ValueError:
                pass

        messagebox.showinfo("Settings", "✅  Settings saved and applied!", parent=self.root)
        self._update_ai_pill()

    # ══════════════════════════════════════════════════════════════════
    #  Misc
    # ══════════════════════════════════════════════════════════════════

    def _set_status(self, text: str):
        self._status_var.set(text)

    def _on_close(self):
        self.listener.stop_listening()
        self.notifier.stop_monitoring()
        self.speaker.shutdown()
        self.root.destroy()

    def run(self):
        self.root.mainloop()