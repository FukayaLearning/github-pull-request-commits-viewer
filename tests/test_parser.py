"""Unit tests for viewer_backend.parser."""

import unittest

from viewer_backend.parser import (
    classify_change_type,
    extract_task_ids,
    extract_trailers,
    parse_commit_metadata,
)


class TestParser(unittest.TestCase):
    """Tests for Git Trailers extraction and commit classification."""

    def test_extract_all_trailers(self) -> None:
        body = (
            "Why: 構造化メタデータを抽出するため\n"
            "What: parser.py を実装\n\n"
            "Issue: #12\n"
            "Task: 1.1 [S01-03-02, S01-03-03]\n"
            "Verification: python3 -m unittest tests/test_parser.py\n"
            "Executed-Command: manual\n"
        )
        trailers = extract_trailers(body)
        self.assertEqual(trailers["issue"], "#12")
        self.assertEqual(trailers["task"], "1.1 [S01-03-02, S01-03-03]")
        self.assertEqual(trailers["why"], "構造化メタデータを抽出するため")
        self.assertEqual(trailers["what"], "parser.py を実装")
        self.assertEqual(trailers["verification"], "python3 -m unittest tests/test_parser.py")
        self.assertEqual(trailers["executed_command"], "manual")

    def test_extract_missing_trailers_returns_none(self) -> None:
        trailers = extract_trailers("Plain commit message without trailers.")
        self.assertEqual(
            trailers,
            {
                "issue": None,
                "task": None,
                "why": None,
                "what": None,
                "executed_command": None,
                "verification": None,
            },
        )

    def test_classify_command_commit(self) -> None:
        body = "Executed-Command: npx eslint --fix .\n"
        trailers = extract_trailers(body)
        self.assertEqual(
            classify_change_type("style: format code", body, trailers),
            "command",
        )

    def test_classify_manual_when_executed_command_is_manual(self) -> None:
        body = "Executed-Command: manual\n"
        trailers = extract_trailers(body)
        self.assertEqual(
            classify_change_type("feat(api): add endpoint", body, trailers),
            "manual",
        )

    def test_classify_manual_when_executed_command_is_quoted_manual(self) -> None:
        body = 'Executed-Command: "manual"\n'
        trailers = extract_trailers(body)
        self.assertEqual(
            classify_change_type("feat(api): add endpoint", body, trailers),
            "manual",
        )

    def test_classify_test_commit_by_subject(self) -> None:
        body = "Executed-Command: manual\n"
        trailers = extract_trailers(body)
        self.assertEqual(
            classify_change_type("test(parser): add unit tests", body, trailers),
            "test",
        )

    def test_classify_test_commit_by_files(self) -> None:
        body = ""
        trailers = extract_trailers(body)
        self.assertEqual(
            classify_change_type(
                "chore: update assertions",
                body,
                trailers,
                files=["tests/test_parser.py"],
            ),
            "test",
        )

    def test_command_takes_precedence_over_test_subject(self) -> None:
        body = "Executed-Command: sed -i 's/foo/bar/g' tests/test_parser.py\n"
        trailers = extract_trailers(body)
        self.assertEqual(
            classify_change_type("test: bulk rename", body, trailers),
            "command",
        )

    def test_extract_task_ids(self) -> None:
        trailers = {"task": "1.1 [S01-03-02, S01-03-03]"}
        ids = extract_task_ids("feat: parse [S01-03-02]", "Ref: S03-01", trailers)
        self.assertEqual(ids, ["S01-03-02", "S01-03-03", "S03-01"])

    def test_parse_commit_metadata_combined(self) -> None:
        body = (
            "Why: テスト用\n"
            "Task: 1.1 [S01-03-02]\n"
            "Executed-Command: python3 -m black .\n"
        )
        metadata = parse_commit_metadata("style: format", body)
        self.assertEqual(metadata["change_type"], "command")
        self.assertEqual(metadata["task_ids"], ["S01-03-02"])
        self.assertEqual(metadata["trailers"]["executed_command"], "python3 -m black .")


if __name__ == "__main__":
    unittest.main()
