from __future__ import annotations

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from internal import operations, validators


class GetChoicesTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage]:
        try:
            credentials = self.runtime.credentials or {}
            access_token = credentials.get("access_token")
            access_token_len: int | None = (
                len(access_token) if isinstance(access_token, str) else None
            )
            if not isinstance(access_token, str) or not access_token.strip():
                yield self.create_text_message(
                    "Missing or empty access_token. Please authorize again."
                )
                yield self.create_json_message(
                    {
                        "error": "missing_access_token",
                        "debug": {"access_token_len": access_token_len},
                    }
                )
                return
            access_token = access_token.strip()

            target = validators.validate_target(
                site_identifier=tool_parameters.get("site_identifier"),
                list_identifier=tool_parameters.get("list_identifier"),
            )
            field_identifier = tool_parameters.get("field_identifier")
            if (
                not isinstance(field_identifier, str)
                or not field_identifier.strip()
            ):
                yield self.create_text_message("field_identifier is required.")
                yield self.create_json_message(
                    {"error": "missing_field_identifier"}
                )
                return

            result = operations.get_choice_field_info(
                access_token=access_token,
                site_identifier=target.site_identifier,
                list_identifier=target.list_identifier,
                field_identifier=field_identifier.strip(),
            )

            yield self.create_json_message(result or {})
            yield self.create_text_message(
                "Choice options fetched successfully."
            )
        except Exception as e:  # noqa: BLE001
            yield self.create_json_message({"error": str(e)})
            yield self.create_text_message(f"Failed to fetch choices: {e}")
