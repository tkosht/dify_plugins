from collections.abc import Generator
from typing import Any

from dify_plugin import AgentStrategy
from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.entities.model.message import (
    PromptMessageTool,
    ensure_prompt_message,
)

from region_contract import Failure
from strategy_core import execute, load_application


class RegionOcrStrategy(AgentStrategy):
    def _invoke(
        self, parameters: dict[str, Any]
    ) -> Generator[AgentInvokeMessage, None, None]:
        try:
            app_id = self.session.app_id

            def model(messages, tools, selection):
                try:
                    result = self.session.model.llm.invoke(
                        model_config=selection,
                        prompt_messages=[
                            ensure_prompt_message(m) for m in messages
                        ],
                        tools=[
                            PromptMessageTool(**tool["function"])
                            for tool in tools
                        ],
                        stream=False,
                    )
                    return result.message.model_dump(mode="json")
                except Exception:
                    raise Failure(502, "MODEL_FAILED") from None

            result = execute(
                parameters, app_id, load_application(app_id), model=model
            )
            yield self.create_json_message(result)
            yield self.create_text_message(result["answer"])
        except Failure as exc:
            suffix = (
                "; CLEANUP_FAILED" if exc.details.get("cleanup_failed") else ""
            )
            raise ValueError(f"HTTP {exc.status} {exc.code}{suffix}") from None
        except Exception:
            raise ValueError("STRATEGY_FAILED") from None
