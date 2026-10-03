"""Run both local services and shut them down together."""

import subprocess
import os
import signal
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
processes = []
try:
    processes.append(
        subprocess.Popen(
            [sys.executable, "-m", "api.server", *sys.argv[1:]], cwd=root, start_new_session=True
        )
    )
    processes.append(subprocess.Popen(["npm", "start"], cwd=root / "ui", start_new_session=True))
    print("Dashboard: http://127.0.0.1:4200", flush=True)
    while all(p.poll() is None for p in processes):
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    for process in processes:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
if any(p.returncode not in (0, -15, -2) for p in processes):
    sys.exit(1)
