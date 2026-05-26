# -*- mode: python ; coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path


try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:
    ROOT = Path.cwd().resolve()
APP_NAME = "AutoPaper"

datas = []
for folder in ("config", "photos"):
    source = ROOT / folder
    if source.exists():
        datas.append((str(source), folder))

hiddenimports = [
    "pyautogui",
    "pyperclip",
    "cv2",
    "PIL",
    "PIL.Image",
    "PIL.ImageOps",
    "PIL.ImageTk",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

gui_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

worker_exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoPaperWorker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    gui_exe,
    worker_exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier="com.autopaper.app",
    )
