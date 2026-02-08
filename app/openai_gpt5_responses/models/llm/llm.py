from __future__ import annotations

import logging
from collections.abc import Generator, Mapping
from typing import Any, cast

import openai
from dify_plugin import LargeLanguageModel
from dify_plugin.entities.model.llm import (
    LLMResult,
    LLMResultChunk,
    LLMResultChunkDelta,
)
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageTool,
)
from dify_plugin.errors.model import (
    CredentialsValidateFailedError,
    InvokeError,
)
from openai import APIConnectionError, APIStatusError, OpenAI

from app.openai_gpt5_responses.internal.credentials import normalize_api_base
from app.openai_gpt5_responses.internal.messages import (
    extract_output_text,
    extract_tool_calls,
    prompt_messages_to_responses_input,
)
from app.openai_gpt5_responses.internal.payloads import (
    build_responses_request,
    coerce_bool_strict,
)

logger = logging.getLogger(__name__)


class OpenAIGPT5LargeLanguageModel(LargeLanguageModel):
    @property
    def _invoke_error_mapping(
        self,
    ) -> dict[type[InvokeError], list[type[Exception]]]:
        return {
            InvokeError: [
                openai.APIConnectionError,
                openai.APITimeoutError,
                openai.AuthenticationError,
                openai.PermissionDeniedError,
                openai.RateLimitError,
                openai.InternalServerError,
                openai.BadRequestError,
                openai.NotFoundError,
                openai.UnprocessableEntityError,
                openai.APIError,
            ]
        }

    def _to_credential_kwargs(
        self, credentials: Mapping[str, Any]
    ) -> dict[str, Any]:
        api_base = normalize_api_base(credentials.get("openai_api_base"))
        timeout_seconds = self._safe_int(
            credentials.get("request_timeout_seconds"), 300
        )
        timeout_seconds = max(30, min(900, timeout_seconds))
        max_retries = self._safe_int(credentials.get("max_retries"), 1)
        max_retries = max(0, min(5, max_retries))

        kwargs: dict[str, Any] = {
            "api_key": credentials.get("openai_api_key"),
            "timeout": float(timeout_seconds),
            "max_retries": max_retries,
        }

        if api_base:
            kwargs["base_url"] = api_base

        organization = str(
            credentials.get("openai_organization") or ""
        ).strip()
        if organization:
            kwargs["organization"] = organization

        return kwargs

    @staticmethod
    def _safe_int(value: object, default: int) -> int:
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return default

    def validate_credentials(self, model: str, credentials: Mapping) -> None:
        if not credentials.get("openai_api_key"):
            raise CredentialsValidateFailedError("openai_api_key is required")

        try:
            client = OpenAI(**self._to_credential_kwargs(credentials))
            payload = build_responses_request(
                model=model,
                user_input="ping",
                model_parameters={
                    "max_output_tokens": 8,
                    "enable_stream": False,
                },
                tools=[],
                stream=False,
            )
            payload["store"] = False
            client.responses.create(**payload)
        except Exception as exc:  # noqa: BLE001
            raise CredentialsValidateFailedError(str(exc)) from exc

    def get_num_tokens(
        self,
        model: str,
        credentials: Mapping,
        prompt_messages: list[PromptMessage],
        tools: list[PromptMessageTool] | None = None,
    ) -> int:
        joined_text = "\n".join(
            [
                str(message.content)
                for message in prompt_messages
                if getattr(message, "content", None)
            ]
        )
        return self._get_num_tokens_by_gpt2(joined_text)

    def _invoke(
        self,
        model: str,
        credentials: Mapping,
        prompt_messages: list[PromptMessage],
        model_parameters: dict,
        tools: list[PromptMessageTool] | None = None,
        stop: list[str] | None = None,
        stream: bool = True,
        user: str | None = None,
    ) -> LLMResult | Generator[LLMResultChunk, None, None]:
        try:
            model_parameters = self._normalize_parameters(
                model=model,
                credentials=credentials,
                model_parameters=model_parameters,
            )
            user_input = prompt_messages_to_responses_input(prompt_messages)
            request_payload = build_responses_request(
                model=model,
                user_input=user_input,
                model_parameters=model_parameters,
                tools=tools or [],
                stream=False,
            )

            # Responses API stop tokens are not consistent across all models.
            if user:
                request_payload["user"] = user

            if stop:
                request_payload["truncation"] = "disabled"

            client = OpenAI(**self._to_credential_kwargs(credentials))

            with self.timing_context():
                response = client.responses.create(**request_payload)

            llm_result = self._to_llm_result(
                model=model,
                credentials=credentials,
                prompt_messages=prompt_messages,
                response=response,
            )

            effective_stream = (
                coerce_bool_strict(
                    model_parameters.get("enable_stream", True),
                    field_name="enable_stream",
                )
                and stream
            )
            if effective_stream:
                return self._as_single_chunk_stream(
                    llm_result, prompt_messages
                )

            return llm_result
        except (APIStatusError, APIConnectionError, openai.APIError) as exc:
            raise self._transform_invoke_error(exc) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("OpenAI GPT-5 responses invoke failed")
            raise self._transform_invoke_error(exc) from exc

    def _normalize_parameters(
        self,
        *,
        model: str,
        credentials: Mapping,
        model_parameters: Mapping[str, Any],
    ) -> dict[str, Any]:
        allowed = {
            "max_output_tokens",
            "reasoning_effort",
            "verbosity",
            "response_format",
            "json_schema",
            "tool_choice",
            "parallel_tool_calls",
            "enable_stream",
        }

        try:
            filtered = self._validate_and_filter_model_parameters(
                model=model,
                model_parameters=dict(model_parameters),
                credentials=dict(credentials),
            )
            if filtered:
                return filtered
        except ValueError:
            # Fall back to minimal filtering to preserve API-compatible parameters
            pass

        return {k: v for k, v in model_parameters.items() if k in allowed}

    def _to_llm_result(
        self,
        *,
        model: str,
        credentials: Mapping,
        prompt_messages: list[PromptMessage],
        response: Any,
    ) -> LLMResult:
        output_text = extract_output_text(response)
        tool_calls = extract_tool_calls(response)

        converted_tool_calls: list[AssistantPromptMessage.ToolCall] = []
        for tool_call in tool_calls:
            converted_tool_calls.append(
                AssistantPromptMessage.ToolCall(
                    id=tool_call["id"],
                    type="function",
                    function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                        name=tool_call["name"],
                        arguments=tool_call["arguments"],
                    ),
                )
            )

        assistant_prompt_message = AssistantPromptMessage(
            content=output_text,
            tool_calls=converted_tool_calls,
        )

        usage = None
        usage_obj = getattr(response, "usage", None)
        if usage_obj is not None:
            prompt_tokens = int(getattr(usage_obj, "input_tokens", 0) or 0)
            completion_tokens = int(
                getattr(usage_obj, "output_tokens", 0) or 0
            )
            usage = self._calc_response_usage(
                model=model,
                credentials=dict(credentials),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

        return LLMResult(
            model=str(getattr(response, "model", model)),
            prompt_messages=prompt_messages,
            message=assistant_prompt_message,
            usage=usage,
            system_fingerprint=None,
        )

    def _as_single_chunk_stream(
        self,
        llm_result: LLMResult,
        prompt_messages: list[PromptMessage],
    ) -> Generator[LLMResultChunk, None, None]:
        yield LLMResultChunk(
            model=llm_result.model,
            prompt_messages=prompt_messages,
            system_fingerprint=llm_result.system_fingerprint,
            delta=LLMResultChunkDelta(
                index=0,
                message=cast(AssistantPromptMessage, llm_result.message),
                finish_reason="stop",
                usage=llm_result.usage,
            ),
        )
