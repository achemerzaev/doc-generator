"""Place the offline user guide and actual build versions beside the executable."""

from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
import platform
import subprocess
import tkinter


def write_instructions(destination, source_dir=None):
    source_dir = Path(source_dir) if source_dir else Path(__file__).resolve().parent
    destination = Path(destination)
    requirements = []
    for line in (source_dir / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name, pinned_version = line.split("==", 1)
            # Missing or mismatched dependencies must fail the build, rather
            # than produce a misleading inventory for vulnerability checks.
            installed_version = metadata.version(name)
            if installed_version != pinned_version:
                raise ValueError(
                    f"{name}: installed {installed_version}, expected {pinned_version}"
                )
            requirements.append(f"   {name}=={installed_version}")

    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=source_dir,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "не определён (сборка без Git)"

    # Include build tools and transitive packages as well, and identify this
    # broader list explicitly: installed does not mean bundled by PyInstaller.
    environment = sorted({
        f"{dist.metadata['Name']}=={dist.version}"
        for dist in metadata.distributions()
        if dist.metadata["Name"]
    }, key=str.casefold)
    versions = [
        "", "Сведения о конкретной сборке", "---------------------------",
        f"Дата сборки (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Коммит исходного кода: {commit}",
        "Коммит обозначает базовую ревизию; локальная сборка может содержать правки.",
        f"Платформа сборки: {platform.system()} / {platform.machine()}",
        f"Python: {platform.python_version()}",
        f"Tcl: {tkinter.Tcl().call('info', 'patchlevel')}",
        f"Tk (версия интерфейса): {tkinter.TkVersion}",
        "tkinter и стандартные модули поставляются с Python.",
        "", "Библиотеки приложения (фактические версии из среды сборки):",
        *requirements,
        "", "Все Python-пакеты среды сборки, включая инструменты сборки",
        "и косвенные зависимости (не каждый из них входит в исполняемый файл):",
        *(f"   {entry}" for entry in environment),
        "", "Версии выше служат для проверки известных уязвимостей и не означают,",
        "что сборка уже прошла такую проверку. Вложенные нативные библиотеки",
        "могут требовать отдельного анализа специалистом.",
    ]
    guide = (source_dir / "INSTRUCTION.txt").read_text(encoding="utf-8")
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / "INSTRUCTION.txt"
    # A BOM lets older Windows Notepad versions recognise Russian UTF-8 text.
    output.write_text(guide + "\n".join(versions) + "\n", encoding="utf-8-sig")
    return output
