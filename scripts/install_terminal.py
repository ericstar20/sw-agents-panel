"""Idempotently add a reviewable dashboard hook to the user's zsh startup file."""

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "# Local Agents dashboard terminal integration"


def install(path):
    original = path.read_text() if path.exists() else ""
    source = str(ROOT / "scripts/terminal.zsh").replace("'", "'\\''")
    block = f"{MARKER}\nsource '{source}'\n"
    if MARKER in original:
        return False
    if path.exists():
        backup = path.with_name(path.name + ".sw-agents-panel.bak")
        if not backup.exists():
            shutil.copy2(path, backup)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(original.rstrip("\n") + "\n\n" + block)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rc", type=Path, default=Path.home() / ".zshrc")
    args = parser.parse_args()
    changed = install(args.rc)
    print(
        "Installed terminal integration."
        if changed
        else "Terminal integration is already installed."
    )
