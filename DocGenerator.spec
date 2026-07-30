# -*- mode: python ; coding: utf-8 -*-


analysis = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("templates/example", "templates/example"),
        ("catalog/example_catalog.xlsx", "catalog"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# tkcalendar uses Babel for Russian dates. PyInstaller's Babel hook otherwise
# copies more than a thousand unused locale files (about 32 MB).
required_babel_locales = {
    "root.dat",
    "ru.dat",
    "ru_RU.dat",
}
analysis.datas = [
    entry
    for entry in analysis.datas
    if not entry[0].replace("\\", "/").startswith("babel/locale-data/")
    or entry[0].replace("\\", "/").rsplit("/", 1)[-1]
    in required_babel_locales
]

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="DocGenerator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

distribution = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DocGenerator",
)
