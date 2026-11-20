from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from adapter import Adapter, resolve_context
from region_contract import Failure, validate_read


class ReadRegionTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        try:
            if set(tool_parameters) - {
                "image_id",
                "x_min",
                "y_min",
                "x_max",
                "y_max",
                "scale",
            }:
                raise Failure(422, "INVALID_REQUEST")
            validate_read(tool_parameters, flat=True)
            context = resolve_context(self.session)
            adapter = Adapter(self.runtime.credentials, context)
            yield self.create_json_message(adapter.read(tool_parameters))
        except Failure as exc:
            raise ValueError(f"HTTP {exc.status} {exc.code}") from None
        except Exception:
            raise ValueError("TOOL_FAILED") from None
