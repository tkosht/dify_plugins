from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from adapter import Adapter, resolve_context
from region_contract import Failure


class CleanupImagesTool(Tool):
    def _invoke(
        self, tool_parameters: dict[str, Any]
    ) -> Generator[ToolInvokeMessage, None, None]:
        try:
            if set(tool_parameters) - set():
                raise Failure(422, "INVALID_REQUEST")
            # Fixed-node parameters are checked before resolving transport context.
            context = resolve_context(self.session)
            adapter = Adapter(self.runtime.credentials, context)
            yield self.create_json_message(adapter.cleanup())
        except Failure as exc:
            raise ValueError(f"HTTP {exc.status} {exc.code}") from None
        except Exception:
            raise ValueError("TOOL_FAILED") from None
