"""Tests for debug logging in operations.py."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import Mock, patch

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
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".ndjson"
        ) as f:
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

                raw_line = lines[0].lstrip()
                assert raw_line.startswith('{"ts":')
                log_entry = json.loads(raw_line)
                # Ensure key order (ts, timestamp first) for readability
                assert list(log_entry.keys())[:2] == ["ts", "timestamp"]
                assert isinstance(log_entry["ts"], int)
                assert isinstance(log_entry["timestamp"], str)
                assert log_entry["location"] == "test"
                assert log_entry["message"] == "test message"
                assert log_entry["data"] == {"key": "value"}
                assert "timestamp" in log_entry
        finally:
            os.unlink(log_path)

    def test_does_not_write_when_disabled(self) -> None:
        """無効時には書き込まない"""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".ndjson"
        ) as f:
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
    def test_authorization_header_excluded_from_log(
        self, mock_request: Mock
    ) -> None:
        """Authorizationヘッダーがログから除外される"""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = "{}"
        mock_resp.json.return_value = {"id": "test-site"}
        mock_request.return_value = mock_resp

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".ndjson"
        ) as f:
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
                    extra_headers={
                        "Authorization": "Bearer secret",
                        "Prefer": "test",
                    },
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

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".ndjson"
        ) as f:
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
            assert (
                operations._get_debug_log_path()
                == "/tmp/sharepoint_list.debug.ndjson"
            )

    def test_custom_path(self) -> None:
        """カスタムパス"""
        with patch.dict(
            os.environ,
            {"SHAREPOINT_LIST_DEBUG_LOG_PATH": "/custom/path.ndjson"},
        ):
            assert operations._get_debug_log_path() == "/custom/path.ndjson"


class TestListItemsDebugLogging:
    """list_items のデバッグログが出力されることを確認"""

    @patch("app.sharepoint_list.internal.http_client.requests.request")
    def test_list_items_emits_debug_entries(self, mock_request: Mock) -> None:
        status_internal = "_x30b9__x30c6__x30fc__x30bf__x30"
        detail_internal = "_x8a73__x7d30_"
        category_internal = "_x30ab__x30c6__x30b4__x30ea_"

        columns_response = {
            "value": [
                {"name": "Title", "displayName": "Title"},
                {"name": "id", "displayName": "ID"},
                {"name": status_internal, "displayName": "ステータス"},
                {"name": detail_internal, "displayName": "詳細"},
                {"name": category_internal, "displayName": "カテゴリ"},
            ]
        }
        items_response = {
            "value": [
                {
                    "id": "item-1",
                    "fields": {
                        "Title": "Item 1",
                        "id": "1",
                        status_internal: "処理中",
                        # detail/category omitted by Graph when empty
                    },
                }
            ],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/sites/site/lists/list/items?$skiptoken=abc123",
        }

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.text = "{}"
        mock_resp.json.side_effect = [columns_response, items_response]
        mock_request.return_value = mock_resp

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".ndjson"
        ) as f:
            log_path = f.name

        try:
            with patch.dict(
                os.environ,
                {
                    "SHAREPOINT_LIST_DEBUG_LOG": "1",
                    "SHAREPOINT_LIST_DEBUG_LOG_PATH": log_path,
                    "SHAREPOINT_LIST_DEBUG_RUN_ID": "test",
                },
            ):
                from app.sharepoint_list.internal import validators

                target = validators.TargetSpec(
                    # GUIDs: bypass resolve_site_id/resolve_list_id extra calls
                    site_identifier="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    list_identifier="b2c3d4e5-f6a7-8901-bcde-f12345678901",
                )
                operations.list_items(
                    access_token="test-token",
                    target=target,
                    select_fields="ID,Title,ステータス,詳細,カテゴリ",
                    filters_raw='[{"field":"ステータス","op":"eq","value":"処理中"}]',
                )

                with open(log_path) as lf:
                    lines = [ln for ln in lf.read().splitlines() if ln.strip()]

                messages = {json.loads(ln).get("message") for ln in lines}
                # High-signal events from list_items flow
                assert "select_fields_mapping" in messages
                assert "request_args" in messages
                assert "response_fields_presence" in messages
                assert "normalized_missing_fields" in messages
                assert "response_fields_presence_normalized" in messages
                assert "return_summary" in messages
        finally:
            os.unlink(log_path)
