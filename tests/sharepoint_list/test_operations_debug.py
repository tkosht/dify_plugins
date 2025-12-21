"""Tests for debug logging in operations.py."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pytest

from app.sharepoint_list.internal import operations


class TestDebugLogEnabled:
    """_is_debug_log_enabled のテスト"""

    def test_disabled_by_default(self) -> None:
        """デフォルトでは無効"""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing SHAREPOINT_LIST_DEBUG_LOG
            os.environ.pop("SHAREPOINT_LIST_DEBUG_LOG", None)
            assert operations._is_debug_log_enabled() is False

    def test_enabled_by_env_var_1(self) -> None:
        """SHAREPOINT_LIST_DEBUG_LOG=1 で有効"""
        with patch.dict(os.environ, {"SHAREPOINT_LIST_DEBUG_LOG": "1"}):
            assert operations._is_debug_log_enabled() is True

    def test_enabled_by_env_var_true(self) -> None:
        """SHAREPOINT_LIST_DEBUG_LOG=true で有効"""
        with patch.dict(os.environ, {"SHAREPOINT_LIST_DEBUG_LOG": "true"}):
            assert operations._is_debug_log_enabled() is True

    def test_enabled_by_env_var_yes(self) -> None:
        """SHAREPOINT_LIST_DEBUG_LOG=yes で有効"""
        with patch.dict(os.environ, {"SHAREPOINT_LIST_DEBUG_LOG": "yes"}):
            assert operations._is_debug_log_enabled() is True

    def test_enabled_by_env_var_on(self) -> None:
        """SHAREPOINT_LIST_DEBUG_LOG=on で有効"""
        with patch.dict(os.environ, {"SHAREPOINT_LIST_DEBUG_LOG": "on"}):
            assert operations._is_debug_log_enabled() is True

    def test_case_insensitive(self) -> None:
        """大文字小文字を区別しない"""
        with patch.dict(os.environ, {"SHAREPOINT_LIST_DEBUG_LOG": "TRUE"}):
            assert operations._is_debug_log_enabled() is True

    def test_disabled_with_invalid_value(self) -> None:
        """無効な値では無効"""
        with patch.dict(os.environ, {"SHAREPOINT_LIST_DEBUG_LOG": "invalid"}):
            assert operations._is_debug_log_enabled() is False


class TestLogDebug:
    """_log_debug のテスト"""

    def test_writes_ndjson_when_enabled(self) -> None:
        """有効時にNDJSON形式でログを書き込む"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ndjson") as f:
            log_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "SHAREPOINT_LIST_DEBUG_LOG": "1",
                    "SHAREPOINT_LIST_DEBUG_LOG_PATH": log_path,
                },
            ):
                operations._log_debug(
                    location="test",
                    message="test message",
                    data={"key": "value"},
                )

                with open(log_path) as f:
                    content = f.read()

                lines = content.strip().split("\n")
                assert len(lines) == 1

                log_entry = json.loads(lines[0])
                assert log_entry["location"] == "test"
                assert log_entry["message"] == "test message"
                assert log_entry["data"] == {"key": "value"}
                assert "timestamp" in log_entry
        finally:
            os.unlink(log_path)

    def test_does_not_write_when_disabled(self) -> None:
        """無効時には書き込まない"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ndjson") as f:
            log_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "SHAREPOINT_LIST_DEBUG_LOG": "0",
                    "SHAREPOINT_LIST_DEBUG_LOG_PATH": log_path,
                },
            ):
                operations._log_debug(
                    location="test",
                    message="test message",
                    data={"key": "value"},
                )

                with open(log_path) as f:
                    content = f.read()

                assert content == ""
        finally:
            os.unlink(log_path)


class TestSendRequestDebugLogging:
    """_send_request でのデバッグログテスト"""

    @patch("app.sharepoint_list.internal.http_client.requests.request")
    def test_authorization_header_excluded_from_log(self, mock_request: Mock) -> None:
        """Authorizationヘッダーがログから除外される"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = "{}"
        mock_resp.json.return_value = {"id": "test-site"}
        mock_request.return_value = mock_resp

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ndjson") as f:
            log_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "SHAREPOINT_LIST_DEBUG_LOG": "1",
                    "SHAREPOINT_LIST_DEBUG_LOG_PATH": log_path,
                },
            ):
                from app.sharepoint_list.internal import request_builders

                spec = request_builders.RequestSpec(
                    url="https://graph.microsoft.com/v1.0/test",
                    method="GET",
                )
                # Call with extra headers including Authorization
                operations._send_request(
                    spec=spec,
                    access_token="secret-token-12345",
                    extra_headers={"Authorization": "Bearer secret", "Prefer": "test"},
                )

                with open(log_path) as f:
                    content = f.read()

                # Check log entries
                for line in content.strip().split("\n"):
                    if not line:
                        continue
                    log_entry = json.loads(line)
                    if "data" in log_entry and "headers" in log_entry["data"]:
                        headers = log_entry["data"]["headers"]
                        # Authorization header should be excluded
                        assert "Authorization" not in headers
                        assert "authorization" not in headers
                        # Other headers should be present
                        assert headers.get("Prefer") == "test"
        finally:
            os.unlink(log_path)

    @patch("app.sharepoint_list.internal.http_client.requests.request")
    def test_access_token_not_in_log_data(self, mock_request: Mock) -> None:
        """アクセストークンがログデータに含まれない"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = "{}"
        mock_resp.json.return_value = {"id": "test-site"}
        mock_request.return_value = mock_resp

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ndjson") as f:
            log_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "SHAREPOINT_LIST_DEBUG_LOG": "1",
                    "SHAREPOINT_LIST_DEBUG_LOG_PATH": log_path,
                },
            ):
                from app.sharepoint_list.internal import request_builders

                spec = request_builders.RequestSpec(
                    url="https://graph.microsoft.com/v1.0/test",
                    method="GET",
                )
                operations._send_request(
                    spec=spec,
                    access_token="super-secret-token-xyz",
                )

                with open(log_path) as f:
                    content = f.read()

                # Access token should not appear anywhere in the log
                assert "super-secret-token-xyz" not in content
        finally:
            os.unlink(log_path)


class TestGetDebugLogPath:
    """_get_debug_log_path のテスト"""

    def test_default_path(self) -> None:
        """デフォルトパス"""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SHAREPOINT_LIST_DEBUG_LOG_PATH", None)
            assert operations._get_debug_log_path() == "/tmp/sharepoint_list.debug.ndjson"

    def test_custom_path(self) -> None:
        """カスタムパス"""
        with patch.dict(
            os.environ, {"SHAREPOINT_LIST_DEBUG_LOG_PATH": "/custom/path.ndjson"}
        ):
            assert operations._get_debug_log_path() == "/custom/path.ndjson"
