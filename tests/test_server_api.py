"""Integration tests for server.py HTTP/API endpoints."""

import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen

from server import create_server


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout.strip()


class TestServerAPI(unittest.TestCase):
    """Integration tests against a live ThreadingHTTPServer instance."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        tmp_root = Path(self._tmpdir.name)
        self.repo_dir = tmp_root / "api-repo"
        self.repo_dir.mkdir()
        _git(self.repo_dir, "init", "-b", "main")
        _git(self.repo_dir, "config", "user.name", "Test User")
        _git(self.repo_dir, "config", "user.email", "test@example.com")
        (self.repo_dir / "main.py").write_text("print('v1')\n", encoding="utf-8")
        _git(self.repo_dir, "add", "main.py")
        _git(self.repo_dir, "commit", "-m", "chore: init")

        _git(self.repo_dir, "checkout", "-b", "feature/api")
        (self.repo_dir / "main.py").write_text("print('v2')  \n", encoding="utf-8")
        _git(self.repo_dir, "add", "main.py")
        _git(
            self.repo_dir,
            "commit",
            "-m",
            "feat: update output",
            "-m",
            "Why: 出力を更新するため\nTask: 1.4 [S01-03-01]\nExecuted-Command: manual",
        )
        self.commit_sha = _git(self.repo_dir, "rev-parse", "HEAD")

        self.static_dir = tmp_root / "static"
        self.static_dir.mkdir()
        (self.static_dir / "index.html").write_text("<html><body>Viewer</body></html>", encoding="utf-8")

        self.server = create_server(
            repo_path=self.repo_dir,
            port=0,
            host="127.0.0.1",
            static_dir=self.static_dir,
        )
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self._tmpdir.cleanup()

    def _get_json(self, path: str) -> tuple[int, dict]:
        url = f"http://127.0.0.1:{self.port}{path}"
        with urlopen(url, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_get_repo_info(self) -> None:
        status, data = self._get_json("/api/repo-info")
        self.assertEqual(status, 200)
        self.assertEqual(data["repo_name"], "api-repo")
        self.assertEqual(data["current_branch"], "feature/api")
        self.assertEqual(data["default_base"], "main")

    def test_get_prs_fallback(self) -> None:
        with patch("viewer_backend.git_service.shutil.which", return_value=None):
            status, data = self._get_json("/api/prs")
        self.assertEqual(status, 200)
        self.assertTrue(data["fallback"])
        self.assertEqual(data["prs"], [])

    def test_get_commits_and_diff(self) -> None:
        status, commits_data = self._get_json("/api/commits?base=main&head=feature/api")
        self.assertEqual(status, 200)
        self.assertEqual(len(commits_data["commits"]), 1)
        self.assertEqual(commits_data["commits"][0]["sha"], self.commit_sha)
        self.assertEqual(commits_data["commits"][0]["change_type"], "manual")

        diff_status, diff_data = self._get_json(f"/api/commits/{self.commit_sha}/diff")
        self.assertEqual(diff_status, 200)
        self.assertEqual(diff_data["sha"], self.commit_sha)
        self.assertEqual(diff_data["files"][0]["path"], "main.py")
        self.assertIn("print('v2')", diff_data["diff"])

    def test_static_serving(self) -> None:
        url = f"http://127.0.0.1:{self.port}/"
        with urlopen(url, timeout=5) as resp:
            html = resp.read().decode("utf-8")
            self.assertEqual(resp.status, 200)
            self.assertIn("Viewer", html)

    def test_invalid_sha_returns_400(self) -> None:
        url = f"http://127.0.0.1:{self.port}/api/commits/bad-sha!/diff"
        with self.assertRaises(HTTPError) as ctx:
            urlopen(url, timeout=5)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
