"""Tests for static frontend assets served by server.py."""

import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

from server import create_server


class TestFrontendAssets(unittest.TestCase):
    """Verify static HTML/CSS/JS assets and required DOM/API hooks."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self._tmpdir.name)
        self.server = create_server(repo_path=".", port=0, host="127.0.0.1")
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self._tmpdir.cleanup()

    def _get_text(self, path: str) -> str:
        url = f"http://127.0.0.1:{self.port}{path}"
        with urlopen(url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            return resp.read().decode("utf-8")

    def test_index_html_contains_three_pane_and_header_elements(self) -> None:
        html = self._get_text("/")
        for expected_id in [
            'id="repo-name"',
            'id="current-branch"',
            'id="pr-select"',
            'id="base-branch-select"',
            'id="head-branch-select"',
            'id="commit-list"',
            'id="commit-summary"',
            'id="diff-viewer"',
        ]:
            self.assertIn(expected_id, html)

    def test_app_js_wires_api_endpoints(self) -> None:
        js = self._get_text("/app.js")
        self.assertIn("/api/repo-info", js)
        self.assertIn("/api/prs", js)
        self.assertIn("/api/commits", js)

    def test_style_css_served(self) -> None:
        css = self._get_text("/style.css")
        self.assertIn(".workspace-layout", css)
        self.assertIn(".badge-command", css)
        self.assertIn(".badge-manual", css)
        self.assertIn(".badge-test", css)
        self.assertIn(".d2h-code-linenumber", css)
        self.assertIn("position: sticky", css)

    def test_app_js_contains_commit_menu_badges_shortcuts_and_storage(self) -> None:
        js = self._get_text("/app.js")
        for token in [
            "🤖 Command",
            "✍️ Manual",
            "✅ Test",
            "localStorage",
            "ArrowDown",
            "ArrowUp",
            'event.key === "r"',
            "Reviewed",
        ]:
            self.assertIn(token, js)

    def test_app_js_contains_summary_and_diff_viewer_controls(self) -> None:
        js = self._get_text("/app.js")
        for token in [
            "/diff?",
            "ignore_whitespace",
            "Diff2HtmlUI",
            "side-by-side",
            "line-by-line",
            "executed-command-box",
            "scrollIntoView",
        ]:
            self.assertIn(token, js)


if __name__ == "__main__":
    unittest.main()
