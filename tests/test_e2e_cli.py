"""End-to-end and CLI configuration tests for server.py."""

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

from server import create_server, parse_args

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout.strip()


class TestCliAndE2E(unittest.TestCase):
    """Verify CLI options, env vars, --help, and full commit-review workflow."""

    def test_parse_args_cli_and_env(self) -> None:
        with patch.dict(os.environ, {"REPO_PATH": "/tmp/env-repo", "PORT": "9123"}, clear=False):
            env_args = parse_args([])
            self.assertEqual(env_args.repo, "/tmp/env-repo")
            self.assertEqual(env_args.port, 9123)

            cli_args = parse_args(["--repo", "/tmp/cli-repo", "--port", "8765"])
            self.assertEqual(cli_args.repo, "/tmp/cli-repo")
            self.assertEqual(cli_args.port, 8765)

    def test_server_help_exits_zero(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "server.py"), "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("--repo", proc.stdout)
        self.assertIn("--port", proc.stdout)

    def test_e2e_commit_history_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "e2e-repo"
            repo_dir.mkdir()
            _git(repo_dir, "init", "-b", "main")
            _git(repo_dir, "config", "user.name", "E2E User")
            _git(repo_dir, "config", "user.email", "e2e@example.com")
            (repo_dir / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
            _git(repo_dir, "add", "module.py")
            _git(repo_dir, "commit", "-m", "chore: initial commit")

            _git(repo_dir, "checkout", "-b", "feat/e2e")
            (repo_dir / "module.py").write_text("VALUE = 2\n", encoding="utf-8")
            _git(repo_dir, "add", "module.py")
            _git(
                repo_dir,
                "commit",
                "-m",
                "feat(core): update value",
                "-m",
                "Why: 設定値を更新するため\nTask: 1.1 [S01-03-01]\nExecuted-Command: manual",
            )

            (repo_dir / "module.py").write_text("VALUE   =   2\n", encoding="utf-8")
            _git(repo_dir, "add", "module.py")
            _git(
                repo_dir,
                "commit",
                "-m",
                "style(core): format spacing",
                "-m",
                "Executed-Command: sed -i 's/=/  =  /' module.py",
            )

            (repo_dir / "tests").mkdir()
            (repo_dir / "tests" / "test_module.py").write_text("assert True\n", encoding="utf-8")
            _git(repo_dir, "add", "tests/test_module.py")
            _git(
                repo_dir,
                "commit",
                "-m",
                "test(core): add module test",
                "-m",
                "Verification: python3 -m unittest\nExecuted-Command: manual",
            )

            server = create_server(repo_path=repo_dir, port=0, host="127.0.0.1")
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                with urlopen(f"http://127.0.0.1:{port}/", timeout=5) as resp:
                    self.assertEqual(resp.status, 200)
                    self.assertIn("GitHub Pull Request Commits Viewer", resp.read().decode("utf-8"))

                with urlopen(f"http://127.0.0.1:{port}/api/repo-info", timeout=5) as resp:
                    repo_info = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(repo_info["repo_name"], "e2e-repo")
                self.assertEqual(repo_info["current_branch"], "feat/e2e")

                with urlopen(
                    f"http://127.0.0.1:{port}/api/commits?base=main&head=feat/e2e",
                    timeout=5,
                ) as resp:
                    commits_data = json.loads(resp.read().decode("utf-8"))

                commits = commits_data["commits"]
                self.assertEqual(len(commits), 3)
                self.assertEqual([c["change_type"] for c in commits], ["manual", "command", "test"])

                cmd_sha = commits[1]["sha"]
                with urlopen(
                    f"http://127.0.0.1:{port}/api/commits/{cmd_sha}/diff?ignore_whitespace=true",
                    timeout=5,
                ) as resp:
                    diff_data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(diff_data["ignore_whitespace"])
                self.assertEqual(diff_data["diff"].strip(), "")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
