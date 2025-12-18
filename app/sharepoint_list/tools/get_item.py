from __future__ import annotations

from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from internal import operations, validators


class GetItemTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage]:
        try:
            credentials = self.runtime.credentials or {}
            access_token = credentials.get("access_token")
            access_token_len = (
                len(access_token)
                if isinstance(access_token, str)
                else "non-str"
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
            item_id = tool_parameters.get("item_id")
            validators.ensure_item_id("read", item_id)
            select_fields = operations.parse_select_fields(
                tool_parameters.get("select_fields")
            )

            result = operations.get_item(
                access_token=access_token,
                target=target,
                item_id=item_id,
                select_fields=select_fields,
            )
            yield self.create_json_message(result or {})
            yield self.create_text_message("Item fetched successfully.")
        except Exception as e:  # noqa: BLE001
            yield self.create_json_message({"error": str(e)})
            yield self.create_text_message(f"Failed to get item: {e}")
