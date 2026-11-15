"""Unit tests for viewer_backend.git_service."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from viewer_backend.git_service import (
    GitRepositoryError,
    GitService,
    validate_commit_sha,
    validate_git_ref,
)


def _git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return proc.stdout.strip()


class TestGitServiceRepoAndPrs(unittest.TestCase):
    """Tests for repository info, branch listing, and gh PR fallback."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self._tmpdir.name) / "sample-repo"
        self.repo_dir.mkdir()
        _git(self.repo_dir, "init", "-b", "main")
        _git(self.repo_dir, "config", "user.name", "Test User")
        _git(self.repo_dir, "config", "user.email", "test@example.com")
        (self.repo_dir / "README.md").write_text("# Sample\n", encoding="utf-8")
        _git(self.repo_dir, "add", "README.md")
        _git(self.repo_dir, "commit", "-m", "chore: initial commit")
        _git(self.repo_dir, "checkout", "-b", "feature/viewer")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_get_repo_info_valid_repo(self) -> None:
        service = GitService(self.repo_dir)
        info = service.get_repo_info()
        self.assertEqual(info["repo_name"], "sample-repo")
        self.assertEqual(info["current_branch"], "feature/viewer")
        self.assertEqual(info["default_base"], "main")
        self.assertIn("main", info["branches"])
        self.assertIn("feature/viewer", info["branches"])

    def test_get_repo_info_non_git_dir_raises(self) -> None:
        with tempfile.TemporaryDirectory() as plain_dir:
            service = GitService(plain_dir)
            with self.assertRaises(GitRepositoryError):
                service.get_repo_info()

    def test_list_prs_fallback_when_gh_missing(self) -> None:
        service = GitService(self.repo_dir)
        with patch("viewer_backend.git_service.shutil.which", return_value=None):
            result = service.list_prs()
        self.assertTrue(result["fallback"])
        self.assertEqual(result["prs"], [])
        self.assertEqual(result["default_base"], "main")
        self.assertEqual(result["default_head"], "feature/viewer")

    def test_list_prs_fallback_when_gh_fails(self) -> None:
        service = GitService(self.repo_dir)
        real_run = subprocess.run

        def selective_run(cmd, *args, **kwargs):
            if cmd and cmd[0] == "gh":
                return subprocess.CompletedProcess(
                    args=cmd, returncode=1, stdout="", stderr="not logged in"
                )
            return real_run(cmd, *args, **kwargs)

        with (
            patch("viewer_backend.git_service.shutil.which", return_value="/usr/bin/gh"),
            patch("viewer_backend.git_service.subprocess.run", side_effect=selective_run),
        ):
            result = service.list_prs()
        self.assertTrue(result["fallback"])
        self.assertEqual(result["prs"], [])
        self.assertIn("not logged in", result["reason"])

    def test_list_prs_fallback_when_gh_returns_empty(self) -> None:
        service = GitService(self.repo_dir)
        empty = subprocess.CompletedProcess(args=["gh"], returncode=0, stdout="[]", stderr="")
        with (
            patch("viewer_backend.git_service.shutil.which", return_value="/usr/bin/gh"),
            patch("viewer_backend.git_service.subprocess.run", return_value=empty),
        ):
            result = service.list_prs()
        self.assertTrue(result["fallback"])
        self.assertEqual(result["prs"], [])

    def test_list_prs_success(self) -> None:
        service = GitService(self.repo_dir)
        prs_payload = [
            {
                "number": 42,
                "title": "Add commit viewer",
                "headRefName": "feature/viewer",
                "baseRefName": "main",
            }
        ]
        ok = subprocess.CompletedProcess(
            args=["gh"],
            returncode=0,
            stdout=json.dumps(prs_payload),
            stderr="",
        )
        with (
            patch("viewer_backend.git_service.shutil.which", return_value="/usr/bin/gh"),
            patch("viewer_backend.git_service.subprocess.run", return_value=ok),
        ):
            result = service.list_prs()
        self.assertFalse(result["fallback"])
        self.assertEqual(result["prs"], prs_payload)

    def test_validate_git_ref_and_sha(self) -> None:
        self.assertEqual(validate_git_ref("main"), "main")
        self.assertEqual(validate_git_ref("feature/test-1"), "feature/test-1")
        with self.assertRaises(ValueError):
            validate_git_ref("--exec=bad")
        with self.assertRaises(ValueError):
            validate_git_ref("")
        self.assertEqual(validate_commit_sha("abc1234"), "abc1234")
        with self.assertRaises(ValueError):
            validate_commit_sha("not-a-sha!")


if __name__ == "__main__":
    unittest.main()
