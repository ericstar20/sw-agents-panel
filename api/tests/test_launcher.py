import json
import io
import signal
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from scripts.dashboard import launch_settings, ensure_dashboard, health
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

    def health_response(self, **overrides):
        data = {
            "app": "sw-agents-panel",
            "project_root": str(ROOT),
            "serves_ui": True,
            "backend_revision": "current",
            "process_id": 12345,
        }
        data.update(overrides)
        return io.BytesIO(json.dumps(data).encode())

    def test_current_service_is_reused_without_stopping_process(self):
        opener = Mock()
        opener.open.return_value = self.health_response()
        with (
            patch("scripts.dashboard.build_opener", return_value=opener),
            patch("scripts.dashboard.backend_revision", return_value="current"),
            patch("scripts.dashboard.os.kill") as kill,
        ):
            self.assertTrue(health(restart_stale=True))
            kill.assert_not_called()

    def test_stale_dashboard_is_stopped_before_reusing_fixed_port(self):
        from urllib.error import URLError

        opener = Mock()
        opener.open.side_effect = [
            self.health_response(backend_revision="old"),
            URLError("service stopped"),
        ]
        with (
            patch("scripts.dashboard.build_opener", return_value=opener),
            patch("scripts.dashboard.backend_revision", return_value="current"),
            patch("scripts.dashboard.os.kill") as kill,
        ):
            self.assertFalse(health(restart_stale=True))
            kill.assert_called_once_with(12345, signal.SIGTERM)

    def test_unrelated_service_is_never_stopped(self):
        opener = Mock()
        opener.open.return_value = self.health_response(app="another-app")
        with (
            patch("scripts.dashboard.build_opener", return_value=opener),
            patch("scripts.dashboard.os.kill") as kill,
        ):
            with self.assertRaisesRegex(RuntimeError, "different service"):
                health(restart_stale=True)
            kill.assert_not_called()

    def test_legacy_service_without_process_identity_is_not_stopped(self):
        opener = Mock()
        opener.open.return_value = self.health_response(backend_revision=None, process_id=None)
        with (
            patch("scripts.dashboard.build_opener", return_value=opener),
            patch("scripts.dashboard.backend_revision", return_value="current"),
            patch("scripts.dashboard.os.kill") as kill,
        ):
            with self.assertRaisesRegex(RuntimeError, "Restart that dashboard once"):
                health(restart_stale=True)
            kill.assert_not_called()

    def test_explicit_restart_stops_current_project_service(self):
        opener = Mock()
        from urllib.error import URLError

        opener.open.side_effect = [self.health_response(), URLError("stopped")]
        with (
            patch("scripts.dashboard.build_opener", return_value=opener),
            patch("scripts.dashboard.os.kill") as kill,
        ):
            self.assertFalse(health(force_restart=True))
            kill.assert_called_once_with(12345, signal.SIGTERM)
