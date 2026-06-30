#!/usr/bin/env python
"""
UE Texture Tools — Modern tkinter GUI with drag-and-drop
PS5/PS4/Switch texture swizzler + UE asset extract/inject
"""
import sys, os, threading, subprocess, glob, tempfile, shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR / 'src'
sys.path.insert(0, str(SRC_DIR))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD

# ═══════════════════════════════════════
#  DESIGN SYSTEM — Catppuccin Mocha
# ═══════════════════════════════════════
class C:
    BASE     = "#1e1e2e"
    MANTLE   = "#181825"
    CRUST    = "#11111b"
    SURFACE0 = "#313244"
    SURFACE1 = "#45475a"
    SURFACE2 = "#585b70"
    OVERLAY0 = "#6c7086"
    OVERLAY1 = "#7f849c"
    TEXT     = "#cdd6f4"
    SUBTEXT0 = "#a6adc8"
    SUBTEXT1 = "#bac2de"
    BLUE     = "#89b4fa"
    LAVENDER = "#b4befe"
    TEAL     = "#94e2d5"
    GREEN    = "#a6e3a1"
    RED      = "#f38ba8"
    YELLOW   = "#f9e2af"
    PEACH    = "#fab387"
    MAUVE    = "#cba6f7"
    PINK     = "#f5c2e7"
    SKY      = "#89dceb"

FONT      = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_MONO  = ("Cascadia Code", 9)
FONT_BTN   = ("Segoe UI", 10, "bold")
FONT_TAB   = ("Segoe UI", 10, "bold")
FONT_BADGE = ("Segoe UI", 7, "bold")


# ═══════════════════════════════════════
#  STYLES
# ═══════════════════════════════════════
def apply_theme(root):
    s = ttk.Style()
    s.theme_use("clam")
    # Base
    s.configure(".", background=C.BASE, foreground=C.TEXT, font=FONT)
    # Notebook
    s.configure("TNotebook", background=C.BASE, borderwidth=0)
    s.configure("TNotebook.Tab", background=C.SURFACE0, foreground=C.SUBTEXT0,
                padding=[20, 8], font=FONT_TAB, borderwidth=0)
    s.map("TNotebook.Tab", background=[("selected", C.BASE)],
          foreground=[("selected", C.LAVENDER)])
    # Frame / LabelFrame
    s.configure("TFrame", background=C.BASE)
    s.configure("Card.TFrame", background=C.SURFACE0, relief="solid", borderwidth=0)
    s.configure("TLabelframe", background=C.BASE, foreground=C.TEXT, borderwidth=1, relief="solid")
    s.configure("TLabelframe.Label", background=C.BASE, foreground=C.LAVENDER, font=FONT_BTN)
    # Label
    s.configure("TLabel", background=C.BASE, foreground=C.TEXT)
    s.configure("Title.TLabel", background=C.BASE, foreground=C.LAVENDER, font=FONT_TITLE)
    s.configure("Sub.TLabel", background=C.BASE, foreground=C.SUBTEXT0, font=FONT_SM)
    s.configure("Card.TLabel", background=C.SURFACE0, foreground=C.TEXT)
    # Entry
    s.configure("TEntry", fieldbackground=C.SURFACE1, foreground=C.TEXT, borderwidth=0,
                padding=[10, 6])
    s.map("TEntry", fieldbackground=[("focus", C.SURFACE2)], bordercolor=[("focus", C.LAVENDER)])
    # Combobox
    s.configure("TCombobox", fieldbackground=C.SURFACE1, foreground=C.TEXT,
                arrowcolor=C.TEXT, borderwidth=0, padding=[8, 6])
    s.map("TCombobox", fieldbackground=[("focus", C.SURFACE2)], bordercolor=[("focus", C.LAVENDER)])
    s.map("TCombobox", selectbackground=[("readonly", C.SURFACE1)], selectforeground=[("readonly", C.TEXT)])
    root.option_add("*TCombobox*Listbox.background", C.SURFACE1)
    root.option_add("*TCombobox*Listbox.foreground", C.TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", C.BLUE)
    root.option_add("*TCombobox*Listbox.selectForeground", C.BASE)
    # Button
    s.configure("TButton", background=C.BLUE, foreground=C.BASE, font=FONT_BTN,
                borderwidth=0, padding=[14, 6])
    s.map("TButton", background=[("active", C.LAVENDER), ("disabled", C.SURFACE1)],
          foreground=[("disabled", C.OVERLAY0)])
    s.configure("Accent.TButton", background=C.TEAL, foreground=C.BASE, font=FONT_BTN,
                borderwidth=0, padding=[20, 8])
    s.map("Accent.TButton", background=[("active", C.GREEN)])
    s.configure("Small.TButton", background=C.SURFACE1, foreground=C.TEXT, font=FONT_SM,
                borderwidth=0, padding=[6, 2])
    s.map("Small.TButton", background=[("active", C.SURFACE2)])
    # Checkbutton
    s.configure("TCheckbutton", background=C.BASE, foreground=C.TEXT)
    s.map("TCheckbutton", background=[("active", C.BASE)],
          indicatorcolor=[("selected", C.LAVENDER)])
    # Spinbox
    s.configure("TSpinbox", fieldbackground=C.SURFACE1, foreground=C.TEXT,
                borderwidth=0, padding=[8, 6])
    # Scrollbar
    s.configure("TScrollbar", background=C.SURFACE0, troughcolor=C.BASE,
                borderwidth=0, arrowcolor=C.TEXT)
    # Scale
    s.configure("TScale", background=C.BASE, troughcolor=C.SURFACE1, borderwidth=0)


# ═══════════════════════════════════════
#  HELPER: Drag-Drop Entry
# ═══════════════════════════════════════
class DropEntry(ttk.Frame):
    """Entry widget with drag-and-drop + browse button + visual drop zone"""
    def __init__(self, parent, placeholder="Drop file or folder here", browse_cmd=None, ext="*"):
        super().__init__(parent)
        self.placeholder = placeholder
        self.browse_cmd = browse_cmd
        self.ext = ext
        self.var = tk.StringVar()

        self.configure(style="Card.TFrame")
        self._build()

    def _build(self):
        # Drop indicator border
        inner = ttk.Frame(self, style="Card.TFrame")
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        row = ttk.Frame(inner, style="Card.TFrame")
        row.pack(fill="x", padx=5, pady=5)

        # Icon label
        icon = ttk.Label(row, text="📁", font=("Segoe UI", 14), background=C.SURFACE0)
        icon.pack(side="left", padx=(5, 8))

        self.entry = tk.Entry(row, textvariable=self.var, font=FONT,
                              bg=C.SURFACE0, fg=C.SUBTEXT0 if not self.var.get() else C.TEXT,
                              relief="flat", borderwidth=0, insertbackground=C.LAVENDER,
                              highlightthickness=0)
        self.entry.pack(side="left", fill="x", expand=True)
        self._update_placeholder()

        if self.browse_cmd:
            ttk.Button(row, text="📂", width=3, style="Small.TButton",
                      command=self.browse_cmd).pack(side="left", padx=(4, 2))

        # Drop target registration
        self.entry.drop_target_register(DND_FILES)
        self.entry.dnd_bind("<<Drop>>", self._on_drop)
        self.entry.dnd_bind("<<DropEnter>>", self._on_drop_enter)
        self.entry.dnd_bind("<<DropLeave>>", self._on_drop_leave)

        # Track focus
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _update_placeholder(self):
        val = self.var.get()
        if val:
            self.entry.configure(fg=C.TEXT)
        else:
            self.entry.delete(0, "end")
            self.entry.insert(0, self.placeholder)
            self.entry.configure(fg=C.OVERLAY0)

    def _on_focus_in(self, e):
        if not self.var.get():
            self.entry.delete(0, "end")

    def _on_focus_out(self, e):
        self._update_placeholder()

    def _on_drop_enter(self, e):
        self.entry.configure(bg=C.SURFACE2)
        return e.action

    def _on_drop_leave(self, e):
        self.entry.configure(bg=C.SURFACE0)
        return e.action

    def _on_drop(self, e):
        data = e.data.strip()
        # Handle multiple files (take first)
        if "{" in data:
            # tkinterdnd2 format: {path1} {path2}
            paths = data.strip("{}").split("} {")
            path = paths[0].strip()
        else:
            path = data.strip()
        self.var.set(path)
        self.entry.configure(fg=C.TEXT, bg=C.SURFACE0)

    def get(self):
        val = self.var.get()
        return "" if val == self.placeholder else val

    def set(self, val):
        self.var.set(val)
        self.entry.configure(fg=C.TEXT)
        self._update_placeholder()


# ═══════════════════════════════════════
#  OUTPUT REDIRECT
# ═══════════════════════════════════════
class OutputRedirector:
    def __init__(self, widget):
        self.widget = widget
        self.buffer = ""

    def write(self, text):
        self.buffer += text
        if "\n" in text:
            self.widget.after(0, self._flush)

    def _flush(self):
        self.widget.configure(state="normal")
        self.widget.insert("end", self.buffer)
        self.widget.see("end")
        self.widget.configure(state="disabled")
        self.buffer = ""

    def flush(self):
        if self.buffer:
            self._flush()


# ═══════════════════════════════════════
#  BASE TAB
# ═══════════════════════════════════════
class BaseTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self): pass

    def log(self, text, tag=None):
        self.app.log(text, tag)

    def run_cmd(self, args):
        self.app.run_cmd(args)


# ═══════════════════════════════════════
#  EXPORT TAB
# ═══════════════════════════════════════
class ExportTab(BaseTab):
    def _build(self):
        padx = 24

        # Header
        h = ttk.Frame(self)
        h.pack(fill="x", padx=padx, pady=(16, 0))
        ttk.Label(h, text="⬆ Export Texture", style="Title.TLabel").pack(side="left")
        ttk.Label(h, text=".uasset → .dds / .png / .tga", style="Sub.TLabel").pack(side="left", padx=12)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=(6, 12))

        # Card
        card = ttk.LabelFrame(self, text=" Input & Output ")
        card.pack(fill="x", padx=24)

        c = ttk.Frame(card)
        c.pack(fill="x", padx=16, pady=(12, 8))

        ttk.Label(c, text="Uasset file or folder", style="Card.TLabel").pack(anchor="w")
        self.input_w = DropEntry(c, "Drop .uasset file or folder here", self._browse, "uasset")
        self.input_w.pack(fill="x", pady=(3, 10))

        ttk.Label(c, text="Output folder", style="Card.TLabel").pack(anchor="w")
        out_row = ttk.Frame(c, style="Card.TFrame")
        out_row.pack(fill="x", pady=(3, 0))
        self.out_var = tk.StringVar(value="exported")
        oe = ttk.Entry(out_row, textvariable=self.out_var)
        oe.pack(side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse", style="Small.TButton", command=self._browse_out).pack(side="left", padx=4)

        # Options card
        opts = ttk.LabelFrame(self, text=" Options ")
        opts.pack(fill="x", padx=24, pady=(10, 0))
        o = ttk.Frame(opts)
        o.pack(fill="x", padx=16, pady=(10, 10))

        ttk.Label(o, text="UE Version", style="Card.TLabel").pack(anchor="w")
        self.ver_var = tk.StringVar(value="4.26")
        ver = ttk.Combobox(o, textvariable=self.ver_var, values=[
            "5.4","5.3","5.2","5.1","5.0","4.26","4.24","4.23","4.20","4.16",
            "4.14","4.12","4.10","4.9","4.8","4.7","4.4","ff7r","borderlands3"
        ], state="readonly", width=20)
        ver.pack(anchor="w", pady=3)

        ttk.Label(o, text="Export as", style="Card.TLabel").pack(anchor="w", pady=(10, 0))
        self.fmt_var = tk.StringVar(value="dds")
        fmt = ttk.Combobox(o, textvariable=self.fmt_var, values=["dds","tga","hdr","bmp","jpg","png"],
                           state="readonly", width=12)
        fmt.pack(anchor="w", pady=3)

        cb = ttk.Frame(o)
        cb.pack(fill="x", pady=(10, 0))
        self.no_mip = tk.BooleanVar()
        self.skip_non = tk.BooleanVar(value=True)
        ttk.Checkbutton(cb, text="No mipmaps", variable=self.no_mip).pack(side="left", padx=(0, 14))
        ttk.Checkbutton(cb, text="Skip non-texture", variable=self.skip_non).pack(side="left")

        # Run button
        ttk.Button(self, text="EXPORT", style="Accent.TButton", command=self._run).pack(pady=(16, 0))

    def _browse(self):
        p = filedialog.askopenfilename(title="Select .uasset", filetypes=[("uasset", "*.uasset")])
        if p: self.input_w.set(p)

    def _browse_out(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p: self.out_var.set(p)

    def _run(self):
        src = self.input_w.get(); out = self.out_var.get().strip()
        if not src: return self.log("Select input file\n", C.RED)
        args = [
            sys.executable, "-E", str(SRC_DIR / "main.py"), src,
            "--mode=export", f"--save_folder={out}", f"--version={self.ver_var.get()}",
            f"--export_as={self.fmt_var.get()}"
        ]
        if self.no_mip.get(): args.append("--no_mipmaps")
        if self.skip_non.get(): args.append("--skip_non_texture")
        self.log(f"⬆ export {Path(src).name}\n", C.BLUE)
        self.run_cmd(args)


# ═══════════════════════════════════════
#  INJECT TAB
# ═══════════════════════════════════════
class InjectTab(BaseTab):
    def _build(self):
        pad = {"padx": 24}

        h = ttk.Frame(self)
        h.pack(fill="x", padx=24, pady=(16, 0))
        ttk.Label(h, text="⬇ Inject Texture", style="Title.TLabel").pack(side="left")
        ttk.Label(h, text=".dds / .png → .uasset", style="Sub.TLabel").pack(side="left", padx=12)
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=(6, 12))

        card = ttk.LabelFrame(self, text=" Input & Output ")
        card.pack(fill="x", padx=24)
        c = ttk.Frame(card)
        c.pack(fill="x", padx=16, pady=(12, 8))

        ttk.Label(c, text="Uasset file or folder", style="Card.TLabel").pack(anchor="w")
        self.uasset_w = DropEntry(c, "Drop .uasset file or folder here", self._browse_uasset, "uasset")
        self.uasset_w.pack(fill="x", pady=(3, 10))

        ttk.Label(c, text="Texture file (DDS/PNG/TGA)", style="Card.TLabel").pack(anchor="w")
        self.tex_w = DropEntry(c, "Drop texture file here", self._browse_tex, "*")
        self.tex_w.pack(fill="x", pady=(3, 10))

        ttk.Label(c, text="Output folder", style="Card.TLabel").pack(anchor="w")
        out_row = ttk.Frame(c, style="Card.TFrame")
        out_row.pack(fill="x", pady=3)
        self.out_var = tk.StringVar(value="injected")
        ttk.Entry(out_row, textvariable=self.out_var).pack(side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse", style="Small.TButton", command=self._browse_out).pack(side="left", padx=4)

        opts = ttk.LabelFrame(self, text=" Options ")
        opts.pack(fill="x", padx=24, pady=(10, 0))
        o = ttk.Frame(opts); o.pack(fill="x", padx=16, pady=(10, 10))

        ttk.Label(o, text="UE Version", style="Card.TLabel").pack(anchor="w")
        self.ver_var = tk.StringVar(value="4.26")
        ttk.Combobox(o, textvariable=self.ver_var, state="readonly", width=20,
            values=["5.4","5.3","5.2","5.1","5.0","4.26","4.24","4.23","4.20","4.16",
                    "4.14","4.12","4.10","4.9","4.8","4.7","4.4","ff7r","borderlands3"]
        ).pack(anchor="w", pady=3)

        cb = ttk.Frame(o); cb.pack(fill="x", pady=(10, 0))
        self.no_mip = tk.BooleanVar()
        self.skip_non = tk.BooleanVar(value=True)
        self.force_unc = tk.BooleanVar()
        self.cubic = tk.BooleanVar()
        ttk.Checkbutton(cb, text="No mipmaps", variable=self.no_mip).grid(row=0, column=0, sticky="w", padx=(0, 14))
        ttk.Checkbutton(cb, text="Force uncompressed", variable=self.force_unc).grid(row=0, column=1, sticky="w", padx=(0, 14))
        ttk.Checkbutton(cb, text="Skip non-texture", variable=self.skip_non).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(cb, text="Cubic filter", variable=self.cubic).grid(row=1, column=1, sticky="w")

        ttk.Button(self, text="INJECT", style="Accent.TButton", command=self._run).pack(pady=(16, 0))

    def _browse_uasset(self):
        p = filedialog.askopenfilename(title="Select .uasset", filetypes=[("uasset","*.uasset")])
        if p: self.uasset_w.set(p)
    def _browse_tex(self):
        p = filedialog.askopenfilename(title="Select texture", filetypes=[("All","*.*")])
        if p: self.tex_w.set(p)
    def _browse_out(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p: self.out_var.set(p)

    def _run(self):
        src = self.uasset_w.get(); tex = self.tex_w.get(); out = self.out_var.get().strip()
        if not src or not tex: return self.log("Select uasset and texture\n", C.RED)
        args = [
            sys.executable, "-E", str(SRC_DIR / "main.py"), src, tex,
            f"--save_folder={out}", f"--version={self.ver_var.get()}"
        ]
        if self.no_mip.get(): args.append("--no_mipmaps")
        if self.skip_non.get(): args.append("--skip_non_texture")
        if self.force_unc.get(): args.append("--force_uncompressed")
        if self.cubic.get(): args.append("--image_filter=cubic")
        self.log(f"⬇ inject {Path(tex).name} → {Path(src).name}\n", C.TEAL)
        self.run_cmd(args)


# ═══════════════════════════════════════
#  SWIZZLE TAB
# ═══════════════════════════════════════
class SwizzleTab(BaseTab):
    def _build(self):
        pad = {"padx": 24}

        h = ttk.Frame(self)
        h.pack(fill="x", padx=24, pady=(16, 0))
        ttk.Label(h, text="🔄 Console Swizzler", style="Title.TLabel").pack(side="left")
        ttk.Label(h, text="PS4 · PS5 · Switch DDS swizzle", style="Sub.TLabel").pack(side="left", padx=12)
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=(6, 12))

        card = ttk.LabelFrame(self, text=" Input & Output ")
        card.pack(fill="x", padx=24)
        c = ttk.Frame(card); c.pack(fill="x", padx=16, pady=(12, 8))

        ttk.Label(c, text="DDS file or folder", style="Card.TLabel").pack(anchor="w")
        self.input_w = DropEntry(c, "Drop .dds file or folder here", self._browse_file, "dds")
        self.input_w.pack(fill="x", pady=(3, 10))

        ttk.Label(c, text="Output folder", style="Card.TLabel").pack(anchor="w")
        out_row = ttk.Frame(c, style="Card.TFrame"); out_row.pack(fill="x", pady=3)
        self.out_var = tk.StringVar(value="swizzled")
        ttk.Entry(out_row, textvariable=self.out_var).pack(side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse", style="Small.TButton", command=self._browse_out).pack(side="left", padx=4)

        # Options
        opts = ttk.LabelFrame(self, text=" Options ")
        opts.pack(fill="x", padx=24, pady=(10, 0))
        o = ttk.Frame(opts); o.pack(fill="x", padx=16, pady=(10, 10))

        grid = ttk.Frame(o); grid.pack(fill="x")
        ttk.Label(grid, text="Mode", style="Card.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 20))
        ttk.Label(grid, text="Platform", style="Card.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 20))
        ttk.Label(grid, text="GOBs (Switch)", style="Card.TLabel").grid(row=0, column=2, sticky="w")

        self.mode_var = tk.StringVar(value="unswizzle")
        m = ttk.Combobox(grid, textvariable=self.mode_var, state="readonly", width=14,
            values=["unswizzle (tiled→linear)", "swizzle (linear→tiled)"])
        m.grid(row=1, column=0, sticky="w", padx=(0, 20), pady=3)

        self.plat_var = tk.StringVar(value="ps5")
        p = ttk.Combobox(grid, textvariable=self.plat_var, state="readonly", width=10,
            values=["ps5", "ps4", "switch"])
        p.grid(row=1, column=1, sticky="w", padx=(0, 20), pady=3)

        self.gobs_var = tk.StringVar(value="8")
        ttk.Spinbox(grid, textvariable=self.gobs_var, values=["1","2","4","8","16","32"], state="readonly", width=5).grid(row=1, column=2, sticky="w", pady=3)

        # Quick info badges
        badges = ttk.Frame(o); badges.pack(fill="x", pady=(10, 0))
        ttk.Label(badges, text="PS4: 8×8 Morton  •  PS5: 64×64 Morton  •  Switch: GOBs (UE=8)", style="Sub.TLabel").pack()

        ttk.Button(self, text="RUN SWIZZLER", style="Accent.TButton", command=self._run).pack(pady=(16, 0))

    def _browse_file(self):
        p = filedialog.askopenfilename(title="Select .dds", filetypes=[("DDS","*.dds")])
        if p: self.input_w.set(p)
    def _browse_out(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p: self.out_var.set(p)

    def _run(self):
        src = self.input_w.get(); out = self.out_var.get().strip()
        if not src: return self.log("Select input\n", C.RED)
        if not out: out = os.path.dirname(src) or "."
        mode_raw = self.mode_var.get()
        mode = "unswizzle" if "unswizzle" in mode_raw else "swizzle"
        plat = self.plat_var.get(); gobs = self.gobs_var.get()

        # Detect folder vs file
        if os.path.isdir(src):
            cmd = "batch-u" if mode == "unswizzle" else "batch-s"
            args = [sys.executable, "-E", str(SRC_DIR / "console_swizzler.py"), cmd, src, plat, gobs]
        else:
            args = [sys.executable, "-E", str(SRC_DIR / "swizzle_gui.py"), mode, src, out, plat, gobs]

        label = "unswizzle" if mode == "unswizzle" else "swizzle"
        self.log(f"🔄 {label} [{plat.upper()}] {Path(src).name}\n", C.MAUVE)
        self.run_cmd(args)


# ═══════════════════════════════════════
#  CHECK TAB
# ═══════════════════════════════════════
class CheckTab(BaseTab):
    def _build(self):
        pad = {"padx": 24}
        h = ttk.Frame(self)
        h.pack(fill="x", padx=24, pady=(16, 0))
        ttk.Label(h, text="🔍 Check Version", style="Title.TLabel").pack(side="left")
        ttk.Label(h, text="Detect UE version of .uasset", style="Sub.TLabel").pack(side="left", padx=12)
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=(6, 12))

        card = ttk.LabelFrame(self, text=" Input ") ; card.pack(fill="x", padx=24)
        c = ttk.Frame(card); c.pack(fill="x", padx=16, pady=(12, 12))
        ttk.Label(c, text="Uasset file", style="Card.TLabel").pack(anchor="w")
        self.input_w = DropEntry(c, "Drop .uasset file here", self._browse, "uasset")
        self.input_w.pack(fill="x", pady=(3, 0))

        ttk.Button(self, text="CHECK VERSION", style="Accent.TButton", command=self._run).pack(pady=(16, 0))

    def _browse(self):
        p = filedialog.askopenfilename(title="Select .uasset", filetypes=[("uasset","*.uasset")])
        if p: self.input_w.set(p)
    def _run(self):
        src = self.input_w.get()
        if not src: return self.log("Select file\n", C.RED)
        args = [sys.executable, "-E", str(SRC_DIR / "main.py"), src, "--mode=check"]
        self.log(f"🔍 check {Path(src).name}\n", C.YELLOW)
        self.run_cmd(args)


# ═══════════════════════════════════════
#  CONVERT TAB
# ═══════════════════════════════════════
class ConvertTab(BaseTab):
    def _build(self):
        pad = {"padx": 24}
        h = ttk.Frame(self)
        h.pack(fill="x", padx=24, pady=(16, 0))
        ttk.Label(h, text="🎨 Convert Format", style="Title.TLabel").pack(side="left")
        ttk.Label(h, text="DDS ↔ TGA / PNG / BMP / JPG", style="Sub.TLabel").pack(side="left", padx=12)
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=24, pady=(6, 12))

        card = ttk.LabelFrame(self, text=" Input & Output ")
        card.pack(fill="x", padx=24)
        c = ttk.Frame(card); c.pack(fill="x", padx=16, pady=(12, 8))
        ttk.Label(c, text="Texture file", style="Card.TLabel").pack(anchor="w")
        self.input_w = DropEntry(c, "Drop texture file here", self._browse, "*")
        self.input_w.pack(fill="x", pady=(3, 10))

        ttk.Label(c, text="Output folder", style="Card.TLabel").pack(anchor="w")
        out_row = ttk.Frame(c, style="Card.TFrame"); out_row.pack(fill="x", pady=3)
        self.out_var = tk.StringVar(value="converted")
        ttk.Entry(out_row, textvariable=self.out_var).pack(side="left", fill="x", expand=True)
        ttk.Button(out_row, text="Browse", style="Small.TButton", command=self._browse_out).pack(side="left")

        opts = ttk.LabelFrame(self, text=" Options ")
        opts.pack(fill="x", padx=24, pady=(10, 0))
        o = ttk.Frame(opts); o.pack(fill="x", padx=16, pady=(10, 10))
        ttk.Label(o, text="Convert to", style="Card.TLabel").pack(anchor="w")
        self.fmt_var = tk.StringVar(value="dds")
        ttk.Combobox(o, textvariable=self.fmt_var, state="readonly", width=12,
            values=["dds","tga","hdr","bmp","jpg","png"]).pack(anchor="w", pady=3)
        self.no_mip = tk.BooleanVar()
        ttk.Checkbutton(o, text="No mipmaps", variable=self.no_mip).pack(anchor="w", pady=(8, 0))

        ttk.Button(self, text="CONVERT", style="Accent.TButton", command=self._run).pack(pady=(16, 0))

    def _browse(self):
        p = filedialog.askopenfilename(title="Select texture")
        if p: self.input_w.set(p)
    def _browse_out(self):
        p = filedialog.askdirectory(title="Select output folder")
        if p: self.out_var.set(p)
    def _run(self):
        src = self.input_w.get(); out = self.out_var.get().strip()
        if not src: return self.log("Select file\n", C.RED)
        args = [sys.executable, "-E", str(SRC_DIR / "main.py"), src, "--mode=convert",
                f"--save_folder={out}", f"--convert_to={self.fmt_var.get()}"]
        if self.no_mip.get(): args.append("--no_mipmaps")
        self.log(f"🎨 convert to {self.fmt_var.get()} {Path(src).name}\n", C.PINK)
        self.run_cmd(args)


# ═══════════════════════════════════════
#  MAIN APP
# ═══════════════════════════════════════
class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("UE Texture Tools")
        self.geometry("780x720")
        self.configure(bg=C.BASE)
        self.resizable(True, True)
        self.minsize(640, 500)

        apply_theme(self)

        # Top bar
        topbar = tk.Frame(self, bg=C.CRUST, height=36)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Label(topbar, text="  UE Texture Tools", bg=C.CRUST, fg=C.LAVENDER,
                font=("Segoe UI", 11, "bold")).pack(side="left", pady=6)
        tk.Label(topbar, text="Export · Inject · Swizzler · Check · Convert  ", bg=C.CRUST,
                fg=C.SUBTEXT0, font=FONT_SM).pack(side="right", pady=8)

        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="x", padx=0, pady=0)

        self.tabs = {}
        for cls, label in [(ExportTab, "  Export  "), (InjectTab, "  Inject  "),
                            (SwizzleTab, "  Swizzler  "), (CheckTab, "  Check  "),
                            (ConvertTab, "  Convert  ")]:
            tab = cls(nb, self)
            nb.add(tab, text=label)
            self.tabs[label] = tab

        # Log area
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="both", expand=True, padx=4, pady=(4, 4))

        log_header = tk.Frame(log_frame, bg=C.CRUST)
        log_header.pack(fill="x")
        tk.Label(log_header, text="  Output Log", bg=C.CRUST, fg=C.SUBTEXT0, font=FONT_SM).pack(side="left", pady=4)
        tk.Label(log_header, text="ready  ", bg=C.CRUST, fg=C.GREEN, font=FONT_SM).pack(side="right", pady=4)

        self.log_widget = scrolledtext.ScrolledText(
            log_frame, height=14, bg=C.MANTLE, fg=C.TEXT, font=FONT_MONO,
            state="disabled", wrap="word", relief="flat", borderwidth=0,
            insertbackground=C.LAVENDER, selectbackground=C.SURFACE2
        )
        self.log_widget.pack(fill="both", expand=True)
        for tag, color in [("err", C.RED), ("ok", C.GREEN), ("blue", C.BLUE),
                            ("teal", C.TEAL), ("mauve", C.MAUVE), ("yellow", C.YELLOW),
                            ("pink", C.PINK), ("dim", C.SUBTEXT0)]:
            self.log_widget.tag_config(tag, foreground=color)

        sys.stdout = OutputRedirector(self.log_widget)

        self.log("UE Texture Tools — PS4/PS5/Switch + UE Asset Tools\n", "teal")
        self.log("  Drag & drop files or use Browse buttons\n\n", "dim")

    def log(self, text, tag=None):
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", text, tag)
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def run_cmd(self, args):
        def _run():
            try:
                self.log("  Running...\n", "dim")
                proc = subprocess.Popen(
                    args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, cwd=str(SCRIPT_DIR), creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in proc.stdout:
                    self.log(f"  {line}")
                proc.wait()
                tag = "ok" if proc.returncode == 0 else "err"
                self.log(f"  {'Done' if proc.returncode == 0 else f'Failed ({proc.returncode})'}\n\n", tag)
            except Exception as e:
                self.log(f"  Error: {e}\n\n", "err")
        threading.Thread(target=_run, daemon=True).start()


def main():
    App().mainloop()


if __name__ == "__main__":
    main()
