"""Zero-dependency HTTP/API server for Local PR and MR Commits Viewer."""

from __future__ import annotations

import json
import re
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from viewer_backend.git_service import GitRepositoryError, GitService

DEFAULT_STATIC_DIR = Path(__file__).resolve().parent / "static"
_COMMIT_DIFF_PATH_RE = re.compile(r"^/api/commits/([^/]+)/diff$")


class ViewerHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Serves JSON API endpoints for Git/PR inspection and static UI assets."""

    def __init__(
        self,
        *args: Any,
        git_service: GitService,
        static_dir: Path,
        **kwargs: Any,
    ) -> None:
        self.git_service = git_service
        super().__init__(*args, directory=str(static_dir), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            self._handle_api_get(path, parse_qs(parsed.query))
            return

        super().do_GET()

    def _handle_api_get(self, path: str, query: dict[str, list[str]]) -> None:
        try:
            if path == "/api/repo-info":
                self._send_json(HTTPStatus.OK, self.git_service.get_repo_info())
                return

            if path == "/api/prs":
                self._send_json(HTTPStatus.OK, self.git_service.list_prs())
                return

            if path == "/api/commits":
                base = (query.get("base") or [""])[0].strip()
                head = (query.get("head") or ["HEAD"])[0].strip() or "HEAD"
                if not base:
                    base = self.git_service.get_repo_info()["default_base"]
                commits = self.git_service.get_commits(base=base, head=head)
                self._send_json(
                    HTTPStatus.OK,
                    {"base": base, "head": head, "commits": commits},
                )
                return

            diff_match = _COMMIT_DIFF_PATH_RE.match(path)
            if diff_match:
                sha = diff_match.group(1)
                raw_ws = (query.get("ignore_whitespace") or ["false"])[0].strip().lower()
                ignore_whitespace = raw_ws in {"true", "1", "yes"}
                diff_data = self.git_service.get_commit_diff(
                    sha=sha,
                    ignore_whitespace=ignore_whitespace,
                )
                self._send_json(HTTPStatus.OK, diff_data)
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Unknown API endpoint: {path}"})
        except ValueError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except GitRepositoryError as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def create_server(
    repo_path: str | Path = ".",
    port: int = 8000,
    host: str = "127.0.0.1",
    static_dir: str | Path | None = None,
) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer instance."""
    resolved_static = Path(static_dir).resolve() if static_dir else DEFAULT_STATIC_DIR
    git_service = GitService(repo_path)
    handler_cls = partial(
        ViewerHTTPRequestHandler,
        git_service=git_service,
        static_dir=resolved_static,
    )
    return ThreadingHTTPServer((host, port), handler_cls)


def main() -> None:
    """Start the HTTP server with default settings."""
    server = create_server()
    host, port = server.server_address[:2]
    print(f"Serving Local PR and MR Commits Viewer at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
