import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.dashboard import launch_settings, ensure_dashboard
from scripts.install_terminal import install, ROOT


class LauncherTests(unittest.TestCase):
    def test_launch_settings_handles_project_profile_and_argument_separator(self):
        cwd = Path("/tmp/work")
        project, profile = launch_settings(["--cd=../other", "--profile", "work"], cwd)
        self.assertEqual(project, Path("/tmp/other").resolve())
        self.assertEqual(profile, "work")
        project, profile = launch_settings(["--", "--cd", "/bad"], cwd)
        self.assertEqual(project, cwd)
        self.assertIsNone(profile)

    def test_install_is_idempotent_and_backs_up_existing_rc(self):
        with tempfile.TemporaryDirectory() as folder:
            rc = Path(folder) / ".zshrc"
            original = "export EXISTING_SETTING=1\n"
            rc.write_text(original)
            self.assertTrue(install(rc))
            self.assertFalse(install(rc))
            self.assertEqual(rc.read_text().count("source "), 1)
            self.assertIn(original.strip(), rc.read_text())
            self.assertEqual(rc.with_name(".zshrc.sw-agents-panel.bak").read_text(), original)

    def test_wrapper_preserves_arguments_and_exit_status_after_dashboard_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            bin_dir = Path(folder)
            python = bin_dir / "python3"
            python.write_text("#!/bin/sh\nexit 1\n")
            python.chmod(0o755)
            codex = bin_dir / "codex"
            codex.write_text(
                f"#!{sys.executable}\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\nsys.exit(7)\n"
            )
            codex.chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:/usr/bin:/bin")
            args = [
                "--profile",
                "work",
                "--cd",
                "/tmp/project with spaces",
                "prompt with $characters",
            ]
            result = subprocess.run(
                [
                    "/bin/zsh",
                    "-f",
                    "-c",
                    'source "$1"; shift; codex "$@"',
                    "test",
                    str(ROOT / "scripts/terminal.zsh"),
                    *args,
                ],
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(result.stdout), args)
            self.assertEqual(result.returncode, 7)

    def test_reuses_service_and_records_custom_home(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            built = root / "ui/dist/dashboard/browser"
            built.mkdir(parents=True)
            (built / "index.html").write_text("dashboard")
            with (
                patch("scripts.dashboard.ROOT", root),
                patch("scripts.dashboard.health", side_effect=[False, True, True]),
                patch("scripts.dashboard.subprocess.Popen") as start,
                patch("scripts.dashboard.subprocess.run") as open_browser,
                patch.dict(os.environ, {"CODEX_HOME": str(root / "custom")}),
            ):
                ensure_dashboard(open_browser=False)
                ensure_dashboard(open_browser=False)
                self.assertEqual(start.call_count, 1)
                open_browser.assert_not_called()
            from api.store import Store

            sources = Store(root / "data/dashboard.sqlite3").integration_sources()
            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0]["home"], str(root / "custom"))

    def test_help_bypasses_dashboard(self):
        with tempfile.TemporaryDirectory() as folder:
            bin_dir = Path(folder)
            python = bin_dir / "python3"
            python.write_text("#!/bin/sh\necho dashboard-should-not-start\n")
            python.chmod(0o755)
            codex = bin_dir / "codex"
            codex.write_text("#!/bin/sh\necho codex-help\n")
            codex.chmod(0o755)
            result = subprocess.run(
                [
                    "/bin/zsh",
                    "-f",
                    "-c",
                    'source "$1"; codex --help',
                    "test",
                    str(ROOT / "scripts/terminal.zsh"),
                ],
                env=dict(os.environ, PATH=f"{bin_dir}:/usr/bin:/bin"),
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.strip(), "codex-help")
