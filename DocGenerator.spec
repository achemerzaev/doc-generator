# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
import runpy

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
    # Test runners and the standard-library test suite are not runtime
    # dependencies. jinja2.tests implements template expressions and stays.
    excludes=[
        "unittest", "doctest", "pytest", "test", "tests", "tkinter.test",
        "test_catalog", "test_preferences",
    ],
    noarchive=False,
    optimize=0,
)

# tkcalendar uses Babel for Russian dates. PyInstaller's Babel hook otherwise
# copies more than a thousand unused locale files (about 32 MB).
required_babel_locales = {
    "root.dat",
    "ru.dat",
    "ru_RU.dat",
    "en.dat",
    "en_US.dat",
    "en_US_POSIX.dat",
}


def keep_locale_resource(destination):
    destination = destination.replace("\\", "/")
    if destination.startswith("babel/locale-data/"):
        return destination.rsplit("/", 1)[-1] in required_babel_locales
    # Tcl/Tk ship translated messages independently of Babel. Encodings and
    # timezone data are runtime resources and must remain intact.
    if "/msgs/" in destination and destination.endswith(".msg"):
        language = destination.rsplit("/", 1)[-1].split(".")[0].split("_")[0]
        return language in {"ru", "en"}
    return True


analysis.datas = [
    entry
    for entry in analysis.datas
    if keep_locale_resource(entry[0])
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

# Keep the guide visible beside the executable on both Windows and Linux.
# Generate it from this build environment so library versions cannot go stale.
runpy.run_path(str(Path(SPECPATH) / "build_instructions.py"))["write_instructions"](
    Path(DISTPATH) / "DocGenerator", source_dir=SPECPATH,
)
