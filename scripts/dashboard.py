"""Start/reuse a single localhost dashboard before invoking the interactive CLI."""

import argparse
import fcntl
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError, HTTPError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from api.integrations.codex import codex_home
from api.runtime import backend_revision
from api.store import Store

PORT = 48763
URL = f"http://127.0.0.1:{PORT}"


def read_health():
    try:
        with build_opener(ProxyHandler({})).open(URL + "/api/health", timeout=1) as response:
            data = json.load(response)
        if not isinstance(data, dict):
            raise RuntimeError("Port 48763 returned an unexpected response.")
        if (
            data.get("app") != "sw-agents-panel"
            or data.get("project_root") != str(ROOT)
            or not data.get("serves_ui")
        ):
            raise RuntimeError("Port 48763 is occupied by a different service.")
        return data
    except HTTPError:
        raise RuntimeError(
            "Port 48763 is occupied by a service without dashboard health information."
        ) from None
    except (URLError, TimeoutError, ConnectionError):
        return None
    except (ValueError, TypeError):
        raise RuntimeError("Port 48763 returned an unexpected response.") from None


def health(restart_stale=False, force_restart=False):
    data = read_health()
    if not data:
        return False
    if force_restart or (restart_stale and data.get("backend_revision") != backend_revision(ROOT)):
        pid = data.get("process_id")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 1:
            raise RuntimeError(
                "An older dashboard is running on port 48763. Restart that dashboard once to enable automatic updates."
            )
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return False
        deadline = time.monotonic() + 5
        while health():
            if time.monotonic() > deadline:
                raise RuntimeError("The old dashboard did not stop. Port 48763 was left unchanged.")
            time.sleep(0.1)
        return False
    return True


def launch_settings(args, cwd):
    """Inspect only discovery-related CLI flags; pass original arguments through untouched."""
    project = cwd
    profile = None
    for index, arg in enumerate(args):
        if arg == "--":
            break
        if arg in ("-C", "--cd", "-p", "--profile") and index + 1 < len(args):
            value = args[index + 1]
            if arg in ("-C", "--cd"):
                path = Path(value).expanduser()
                project = (path if path.is_absolute() else cwd / path).resolve()
            else:
                profile = value
        elif arg.startswith("--cd="):
            path = Path(arg.split("=", 1)[1]).expanduser()
            project = (path if path.is_absolute() else cwd / path).resolve()
        elif arg.startswith("--profile="):
            profile = arg.split("=", 1)[1]
    return project, profile


def ensure_dashboard(args=(), open_browser=True, restart=False):
    data_dir = ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    # The OS releases this lock after failures; simultaneous terminals share startup.
    with (data_dir / "dashboard-start.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        project, profile = launch_settings(args, Path.cwd())
        Store(data_dir / "dashboard.sqlite3").register_source(
            "codex", codex_home(), project, profile
        )
        if not health(restart_stale=True, force_restart=restart):
            index = ROOT / "ui/dist/dashboard/browser/index.html"
            if not index.is_file():
                raise RuntimeError("Dashboard UI is not built. Run npm run build in " + str(ROOT))
            start_background(data_dir)
    if open_browser:
        subprocess.run(["open", URL + "/overview"], check=True)
    return URL


def start_background(data_dir):
    with (data_dir / "dashboard.log").open("ab") as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "api.server", "--serve-ui", "--port", str(PORT)],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    deadline = time.monotonic() + 10
    while not health():
        if process.poll() is not None or time.monotonic() > deadline:
            if process.poll() is None:
                process.terminate()
            raise RuntimeError("Dashboard startup failed; inspect data/dashboard.log.")
        time.sleep(0.1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("cli_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cli_args = args.cli_args[1:] if args.cli_args[:1] == ["--"] else args.cli_args
    try:
        if args.stop:
            data_dir = ROOT / "data"
            data_dir.mkdir(exist_ok=True)
            with (data_dir / "dashboard-start.lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                health(force_restart=True)
            print("Project dashboard stopped.")
        else:
            ensure_dashboard(cli_args, open_browser=not args.no_browser, restart=args.restart)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Local Agents: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
