import json
import logging
import os
import time
from collections.abc import Generator
from copy import deepcopy
from typing import Any, cast

from dify_plugin.entities.agent import AgentInvokeMessage
from dify_plugin.entities.model import ModelFeature
from dify_plugin.entities.model.llm import (
    LLMModelConfig,
    LLMResult,
    LLMResultChunk,
    LLMUsage,
)
from dify_plugin.entities.model.message import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageContentType,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from dify_plugin.entities.tool import ToolInvokeMessage, ToolProviderType
from dify_plugin.interfaces.agent import (
    AgentModelConfig,
    AgentStrategy,
    ToolEntity,
    ToolInvokeMeta,
)
from pydantic import BaseModel

from app.gpt5_agent_strategies.internal.flow import (
    build_round_prompt_messages,
    extract_blocking_tool_calls,
    extract_stream_tool_calls,
    should_emit_response_text,
)
from app.gpt5_agent_strategies.internal.tooling import (
    parse_tool_arguments,
    resolve_tool_instance,
)

logger = logging.getLogger(__name__)


class LogMetadata:
    """Metadata keys for logging"""

    STARTED_AT = "started_at"
    PROVIDER = "provider"
    FINISHED_AT = "finished_at"
    ELAPSED_TIME = "elapsed_time"
    TOTAL_PRICE = "total_price"
    CURRENCY = "currency"
    TOTAL_TOKENS = "total_tokens"


class ExecutionMetadata(BaseModel):
    """Execution metadata with default values"""

    total_price: float = 0.0
    currency: str = ""
    total_tokens: int = 0
    prompt_tokens: int = 0
    prompt_unit_price: float = 0.0
    prompt_price_unit: float = 0.0
    prompt_price: float = 0.0
    completion_tokens: int = 0
    completion_unit_price: float = 0.0
    completion_price_unit: float = 0.0
    completion_price: float = 0.0
    latency: float = 0.0

    @classmethod
    def from_llm_usage(cls, usage: LLMUsage | None) -> "ExecutionMetadata":
        """Create ExecutionMetadata from LLMUsage, handling None case"""
        if usage is None:
            return cls()

        return cls(
            total_price=float(usage.total_price),
            currency=usage.currency,
            total_tokens=usage.total_tokens,
            prompt_tokens=usage.prompt_tokens,
            prompt_unit_price=float(usage.prompt_unit_price),
            prompt_price_unit=float(usage.prompt_price_unit),
            prompt_price=float(usage.prompt_price),
            completion_tokens=usage.completion_tokens,
            completion_unit_price=float(usage.completion_unit_price),
            completion_price_unit=float(usage.completion_price_unit),
            completion_price=float(usage.completion_price),
            latency=usage.latency,
        )


class ContextItem(BaseModel):
    content: str
    title: str
    metadata: dict[str, Any]


class GPT5FunctionCallingParams(BaseModel):
    query: str
    instruction: str | None
    model: AgentModelConfig
    tools: list[ToolEntity] | None
    maximum_iterations: int = 3
    context: list[ContextItem] | None = None


class GPT5FunctionCallingStrategy(AgentStrategy):
    _LOCAL_FILE_ROOT = "/files"
    _MAX_BLOB_FILE_BYTES = 5 * 1024 * 1024
    _TOOL_INVOKE_ERROR_MESSAGE = "tool invoke error: failed to execute tool"

    query: str = ""
    instruction: str | None = ""

    @property
    def _user_prompt_message(self) -> UserPromptMessage:
        return UserPromptMessage(content=self.query)

    @property
    def _system_prompt_message(self) -> SystemPromptMessage:
        from app.gpt5_agent_strategies.internal.policy import (
            build_system_instruction,
        )

        return SystemPromptMessage(
            content=build_system_instruction(self.instruction or "")
        )

    def _invoke(
        self, parameters: dict[str, Any]
    ) -> Generator[AgentInvokeMessage, None, None]:
        """
        Run FunctionCall agent application
        """
        fc_params = GPT5FunctionCallingParams(**parameters)

        # init prompt messages
        query = fc_params.query
        self.query = query
        self.instruction = fc_params.instruction
        history_prompt_messages = build_round_prompt_messages(
            history_prompt_messages=fc_params.model.history_prompt_messages,
            system_message=self._system_prompt_message,
            user_message=self._user_prompt_message,
        )

        # convert tool messages
        tools = fc_params.tools
        tool_instances = (
            {tool.identity.name: tool for tool in tools} if tools else {}
        )
        prompt_messages_tools = self._init_prompt_tools(tools)

        # init model parameters
        stream = (
            ModelFeature.STREAM_TOOL_CALL in fc_params.model.entity.features
            if fc_params.model.entity and fc_params.model.entity.features
            else False
        )
        model = fc_params.model
        stop = (
            fc_params.model.completion_params.get("stop", [])
            if fc_params.model.completion_params
            else []
        )

        # init function calling state
        iteration_step = 1
        max_iteration_steps = fc_params.maximum_iterations
        current_thoughts: list[PromptMessage] = []
        function_call_state = (
            True  # continue to run until there is not any tool call
        )
        llm_usage: dict[str, LLMUsage | None] = {"usage": None}
        final_answer = ""

        while function_call_state and iteration_step <= max_iteration_steps:
            # start a new round
            function_call_state = False
            round_started_at = time.perf_counter()
            round_log = self.create_log_message(
                label=f"ROUND {iteration_step}",
                data={},
                metadata={
                    LogMetadata.STARTED_AT: round_started_at,
                },
                status=ToolInvokeMessage.LogMessage.LogStatus.START,
            )
            yield round_log

            # recalc llm max tokens
            prompt_messages = self._organize_prompt_messages(
                history_prompt_messages=history_prompt_messages,
                current_thoughts=current_thoughts,
                model=model,
            )
            if model.entity and model.completion_params:
                self.recalc_llm_max_tokens(
                    model.entity, prompt_messages, model.completion_params
                )
            # invoke model
            model_started_at = time.perf_counter()
            model_log = self.create_log_message(
                label=f"{model.model} Thought",
                data={},
                metadata={
                    LogMetadata.STARTED_AT: model_started_at,
                    LogMetadata.PROVIDER: model.provider,
                },
                parent=round_log,
                status=ToolInvokeMessage.LogMessage.LogStatus.START,
            )
            yield model_log
            model_config = LLMModelConfig(**model.model_dump(mode="json"))
            chunks: Generator[LLMResultChunk, None, None] | LLMResult = (
                self.session.model.llm.invoke(
                    model_config=model_config,
                    prompt_messages=prompt_messages,
                    stop=stop,
                    stream=stream,
                    tools=prompt_messages_tools,
                )
            )

            tool_calls: list[tuple[str, str, dict[str, Any], str | None]] = []

            # save full response
            response = ""

            # save tool call names and inputs
            tool_call_names = ""

            current_llm_usage = None

            if isinstance(chunks, Generator):
                stream_text_fragments: list[str] = []
                for chunk in chunks:
                    # check if there is any tool call
                    if self.check_tool_calls(chunk):
                        function_call_state = True
                        tool_calls.extend(self.extract_tool_calls(chunk) or [])
                        tool_call_names = ";".join(
                            [tool_call[1] for tool_call in tool_calls]
                        )

                    if chunk.delta.message and chunk.delta.message.content:
                        if isinstance(chunk.delta.message.content, list):
                            for content in chunk.delta.message.content:
                                response += content.data
                                stream_text_fragments.append(content.data)
                        else:
                            chunk_text = str(chunk.delta.message.content)
                            response += chunk_text
                            stream_text_fragments.append(chunk_text)

                    if chunk.delta.usage:
                        self.increase_usage(llm_usage, chunk.delta.usage)
                        current_llm_usage = chunk.delta.usage

                if stream_text_fragments and should_emit_response_text(
                    has_tool_calls=bool(tool_calls),
                    iteration_step=iteration_step,
                    max_iteration_steps=max_iteration_steps,
                ):
                    yield self.create_text_message(
                        "".join(stream_text_fragments)
                    )

            else:
                result = chunks
                result = cast(LLMResult, result)
                # check if there is any tool call
                if self.check_blocking_tool_calls(result):
                    function_call_state = True
                    tool_calls.extend(
                        self.extract_blocking_tool_calls(result) or []
                    )
                    tool_call_names = ";".join(
                        [tool_call[1] for tool_call in tool_calls]
                    )

                if result.usage:
                    self.increase_usage(llm_usage, result.usage)
                    current_llm_usage = result.usage

                result_message = result.message
                if result.message and result.message.content:
                    if isinstance(result.message.content, list):
                        for content in result.message.content:
                            response += content.data
                    else:
                        response += str(result.message.content)

                if result_message is not None and not result_message.content:
                    result_message.content = ""
                if result_message is not None and should_emit_response_text(
                    has_tool_calls=bool(tool_calls),
                    iteration_step=iteration_step,
                    max_iteration_steps=max_iteration_steps,
                ):
                    if isinstance(result_message.content, str):
                        yield self.create_text_message(result_message.content)
                    elif isinstance(result_message.content, list):
                        for content in result_message.content:
                            yield self.create_text_message(content.data)

            yield self.finish_log_message(
                log=model_log,
                data={
                    "output": response,
                    "tool_name": tool_call_names,
                    "tool_input": [
                        {"name": tool_call[1], "args": tool_call[2]}
                        for tool_call in tool_calls
                    ],
                },
                metadata={
                    LogMetadata.STARTED_AT: model_started_at,
                    LogMetadata.FINISHED_AT: time.perf_counter(),
                    LogMetadata.ELAPSED_TIME: time.perf_counter()
                    - model_started_at,
                    LogMetadata.PROVIDER: model.provider,
                    LogMetadata.TOTAL_PRICE: (
                        current_llm_usage.total_price
                        if current_llm_usage
                        else 0
                    ),
                    LogMetadata.CURRENCY: (
                        current_llm_usage.currency if current_llm_usage else ""
                    ),
                    LogMetadata.TOTAL_TOKENS: (
                        current_llm_usage.total_tokens
                        if current_llm_usage
                        else 0
                    ),
                },
            )

            # If there are tool calls, merge all tool calls into
            # a single assistant message.
            if tool_calls:
                tool_call_objects = [
                    AssistantPromptMessage.ToolCall(
                        id=tool_call_id,
                        type="function",
                        function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                            name=tool_call_name,
                            arguments=json.dumps(
                                tool_call_args, ensure_ascii=False
                            ),
                        ),
                    )
                    for (
                        tool_call_id,
                        tool_call_name,
                        tool_call_args,
                        _parse_error,
                    ) in tool_calls
                ]
                assistant_message = AssistantPromptMessage(
                    content=response,  # Preserve LLM returned content, even if empty
                    tool_calls=tool_call_objects,
                )
                current_thoughts.append(assistant_message)
            elif response.strip():
                # If no tool calls but has response, add a regular assistant message
                assistant_message = AssistantPromptMessage(
                    content=response, tool_calls=[]
                )
                current_thoughts.append(assistant_message)

            final_answer += response + "\n"

            # call tools
            tool_responses = []
            # Check if max iterations reached.
            # Allow tool calls when max_iteration_steps == 1.
            if (
                tool_calls
                and iteration_step == max_iteration_steps
                and max_iteration_steps > 1
            ):
                # Max iterations reached, return message instead of calling tools
                for (
                    tool_call_id,
                    tool_call_name,
                    tool_call_args,
                    _parse_error,
                ) in tool_calls:
                    # Create log entry for the skipped tool call
                    tool_call_started_at = time.perf_counter()
                    tool_call_log = self.create_log_message(
                        label=f"CALL {tool_call_name}",
                        data={},
                        metadata={
                            LogMetadata.STARTED_AT: time.perf_counter(),
                            LogMetadata.PROVIDER: (
                                tool_instances[
                                    tool_call_name
                                ].identity.provider
                                if tool_instances.get(tool_call_name)
                                else ""
                            ),
                        },
                        parent=round_log,
                        status=ToolInvokeMessage.LogMessage.LogStatus.START,
                    )
                    yield tool_call_log

                    # Return error message instead of calling tool
                    tool_response = {
                        "tool_call_id": tool_call_id,
                        "tool_call_name": tool_call_name,
                        "tool_response": (
                            f"Maximum iteration limit ({max_iteration_steps}) reached. "
                            f"Cannot call tool '{tool_call_name}'. "
                            f"Please consider increasing the iteration limit."
                        ),
                    }
                    tool_responses.append(tool_response)

                    yield self.finish_log_message(
                        log=tool_call_log,
                        data={"output": tool_response},
                        metadata={
                            LogMetadata.STARTED_AT: tool_call_started_at,
                            LogMetadata.PROVIDER: (
                                tool_instances[
                                    tool_call_name
                                ].identity.provider
                                if tool_instances.get(tool_call_name)
                                else ""
                            ),
                            LogMetadata.FINISHED_AT: time.perf_counter(),
                            LogMetadata.ELAPSED_TIME: time.perf_counter()
                            - tool_call_started_at,
                        },
                    )

                    # Add to current_thoughts for context
                    current_thoughts.append(
                        AssistantPromptMessage(
                            content="",
                            tool_calls=[
                                AssistantPromptMessage.ToolCall(
                                    id=tool_call_id,
                                    type="function",
                                    function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                                        name=tool_call_name,
                                        arguments=json.dumps(
                                            tool_call_args, ensure_ascii=False
                                        ),
                                    ),
                                )
                            ],
                        )
                    )
                    current_thoughts.append(
                        ToolPromptMessage(
                            content=tool_response["tool_response"],
                            tool_call_id=tool_call_id,
                            name=tool_call_name,
                        )
                    )
            else:
                for (
                    tool_call_id,
                    tool_call_name,
                    tool_call_args,
                    parse_error,
                ) in tool_calls:
                    tool_instance = resolve_tool_instance(
                        tool_instances, tool_call_name
                    )
                    tool_provider = (
                        tool_instance.identity.provider
                        if tool_instance
                        else ""
                    )
                    tool_call_started_at = time.perf_counter()
                    tool_call_log = self.create_log_message(
                        label=f"CALL {tool_call_name}",
                        data={},
                        metadata={
                            LogMetadata.STARTED_AT: time.perf_counter(),
                            LogMetadata.PROVIDER: tool_provider,
                        },
                        parent=round_log,
                        status=ToolInvokeMessage.LogMessage.LogStatus.START,
                    )
                    yield tool_call_log
                    if parse_error:
                        parse_error_message = (
                            f"tool arguments parse error: {parse_error}"
                        )
                        tool_response = {
                            "tool_call_id": tool_call_id,
                            "tool_call_name": tool_call_name,
                            "tool_response": parse_error_message,
                            "meta": ToolInvokeMeta.error_instance(
                                parse_error_message
                            ).to_dict(),
                        }
                    elif not tool_instance:
                        tool_not_found = (
                            f"there is not a tool named {tool_call_name}"
                        )
                        tool_response = {
                            "tool_call_id": tool_call_id,
                            "tool_call_name": tool_call_name,
                            "tool_response": tool_not_found,
                            "meta": ToolInvokeMeta.error_instance(
                                tool_not_found
                            ).to_dict(),
                        }
                    else:
                        # invoke tool
                        try:
                            tool_invoke_responses = self.session.tool.invoke(
                                provider_type=ToolProviderType(
                                    tool_instance.provider_type
                                ),
                                provider=tool_instance.identity.provider,
                                tool_name=tool_instance.identity.name,
                                parameters={
                                    **tool_instance.runtime_parameters,
                                    **tool_call_args,
                                },
                            )
                            tool_result = ""
                            for tool_invoke_response in tool_invoke_responses:
                                if (
                                    tool_invoke_response.type
                                    == ToolInvokeMessage.MessageType.TEXT
                                ):
                                    tool_result += cast(
                                        ToolInvokeMessage.TextMessage,
                                        tool_invoke_response.message,
                                    ).text
                                elif (
                                    tool_invoke_response.type
                                    == ToolInvokeMessage.MessageType.LINK
                                ):
                                    tool_result += (
                                        "result link: "
                                        + cast(
                                            ToolInvokeMessage.TextMessage,
                                            tool_invoke_response.message,
                                        ).text
                                        + "."
                                        + " please tell user to check it."
                                    )
                                elif tool_invoke_response.type in {
                                    ToolInvokeMessage.MessageType.IMAGE_LINK,
                                    ToolInvokeMessage.MessageType.IMAGE,
                                }:
                                    # Extract file path or URL from the message.
                                    if hasattr(
                                        tool_invoke_response.message, "text"
                                    ):
                                        file_info = cast(
                                            ToolInvokeMessage.TextMessage,
                                            tool_invoke_response.message,
                                        ).text
                                        # Try to create a blob response from file.
                                        try:
                                            local_file = (
                                                self._read_local_file_for_blob(
                                                    file_info
                                                )
                                            )
                                            if local_file is not None:
                                                file_content, filename = (
                                                    local_file
                                                )
                                                blob = self.create_blob_message(
                                                    blob=file_content,
                                                    meta={
                                                        "mime_type": "image/png",
                                                        "filename": filename,
                                                    },
                                                )
                                                yield blob
                                        except Exception:
                                            logger.exception(
                                                "Failed to create blob message "
                                                "from local image output"
                                            )
                                            yield self.create_text_message(
                                                "Failed to process generated image "
                                                "file."
                                            )
                                    tool_result += (
                                        "image generated and sent to user. "
                                        "Tell user to review it now."
                                    )
                                    yield self._to_agent_invoke_message(
                                        tool_invoke_response
                                    )
                                elif (
                                    tool_invoke_response.type
                                    == ToolInvokeMessage.MessageType.JSON
                                ):
                                    text = json.dumps(
                                        cast(
                                            ToolInvokeMessage.JsonMessage,
                                            tool_invoke_response.message,
                                        ).json_object,
                                        ensure_ascii=False,
                                    )
                                    tool_result += f"tool response: {text}."
                                elif (
                                    tool_invoke_response.type
                                    == ToolInvokeMessage.MessageType.BLOB
                                ):
                                    tool_result += "Generated file ... "
                                    yield self._to_agent_invoke_message(
                                        tool_invoke_response
                                    )
                                else:
                                    response_repr = repr(
                                        tool_invoke_response.message
                                    )
                                    tool_result += (
                                        f"tool response: {response_repr}."
                                    )
                        except Exception:
                            logger.exception(
                                "Tool invoke failed: tool=%s", tool_call_name
                            )
                            tool_result = self._TOOL_INVOKE_ERROR_MESSAGE
                        tool_response = {
                            "tool_call_id": tool_call_id,
                            "tool_call_name": tool_call_name,
                            "tool_call_input": {
                                **tool_instance.runtime_parameters,
                                **tool_call_args,
                            },
                            "tool_response": tool_result,
                        }

                    yield self.finish_log_message(
                        log=tool_call_log,
                        data={
                            "output": tool_response,
                        },
                        metadata={
                            LogMetadata.STARTED_AT: tool_call_started_at,
                            LogMetadata.PROVIDER: tool_provider,
                            LogMetadata.FINISHED_AT: time.perf_counter(),
                            LogMetadata.ELAPSED_TIME: time.perf_counter()
                            - tool_call_started_at,
                        },
                    )
                    tool_responses.append(tool_response)
                    if tool_response["tool_response"] is not None:
                        current_thoughts.append(
                            ToolPromptMessage(
                                content=str(tool_response["tool_response"]),
                                tool_call_id=tool_call_id,
                                name=tool_call_name,
                            )
                        )
            # Insert blank line so the next assistant thought
            # appears on a new line in the user interface.
            if tool_calls:
                yield self.create_text_message("\n")

            # update prompt tool
            for prompt_tool in prompt_messages_tools:
                self.update_prompt_message_tool(
                    tool_instances[prompt_tool.name], prompt_tool
                )
            yield self.finish_log_message(
                log=round_log,
                data={
                    "output": {
                        "llm_response": response,
                        "tool_responses": tool_responses,
                    },
                },
                metadata={
                    LogMetadata.STARTED_AT: round_started_at,
                    LogMetadata.FINISHED_AT: time.perf_counter(),
                    LogMetadata.ELAPSED_TIME: time.perf_counter()
                    - round_started_at,
                    LogMetadata.TOTAL_PRICE: (
                        current_llm_usage.total_price
                        if current_llm_usage
                        else 0
                    ),
                    LogMetadata.CURRENCY: (
                        current_llm_usage.currency if current_llm_usage else ""
                    ),
                    LogMetadata.TOTAL_TOKENS: (
                        current_llm_usage.total_tokens
                        if current_llm_usage
                        else 0
                    ),
                },
            )
            # If max_iteration_steps=1, need to return tool responses
            if tool_responses and max_iteration_steps == 1:
                for resp in tool_responses:
                    yield self.create_text_message(str(resp["tool_response"]))
            iteration_step += 1

        # If context is a list of dict, create retriever resource message
        if isinstance(fc_params.context, list):
            yield self.create_retriever_resource_message(
                retriever_resources=[
                    ToolInvokeMessage.RetrieverResourceMessage.RetrieverResource(
                        content=ctx.content,
                        position=ctx.metadata.get("position"),
                        dataset_id=ctx.metadata.get("dataset_id"),
                        dataset_name=ctx.metadata.get("dataset_name"),
                        document_id=ctx.metadata.get("document_id"),
                        document_name=ctx.metadata.get("document_name"),
                        data_source_type=ctx.metadata.get(
                            "document_data_source_type"
                        ),
                        segment_id=ctx.metadata.get("segment_id"),
                        retriever_from=ctx.metadata.get("retriever_from"),
                        score=ctx.metadata.get("score"),
                        hit_count=ctx.metadata.get("segment_hit_count"),
                        word_count=ctx.metadata.get("segment_word_count"),
                        segment_position=ctx.metadata.get("segment_position"),
                        index_node_hash=ctx.metadata.get(
                            "segment_index_node_hash"
                        ),
                        page=ctx.metadata.get("page"),
                        doc_metadata=ctx.metadata.get("doc_metadata"),
                    )
                    for ctx in fc_params.context
                ],
                context="",
            )

        metadata = ExecutionMetadata.from_llm_usage(llm_usage["usage"])
        yield self.create_json_message(
            {"execution_metadata": metadata.model_dump()}
        )

    def check_tool_calls(self, llm_result_chunk: LLMResultChunk) -> bool:
        """
        Check if there is any tool call in llm result chunk
        """
        return bool(extract_stream_tool_calls(llm_result_chunk))

    def check_blocking_tool_calls(self, llm_result: LLMResult) -> bool:
        """
        Check if there is any blocking tool call in llm result
        """
        return bool(extract_blocking_tool_calls(llm_result))

    def extract_tool_calls(
        self, llm_result_chunk: LLMResultChunk
    ) -> list[tuple[str, str, dict[str, Any], str | None]]:
        """
        Extract tool calls from llm result chunk

        Returns:
            List[Tuple[str, str, Dict[str, Any], Optional[str]]]:
                [(tool_call_id, tool_call_name, tool_call_args, parse_error)]
        """
        tool_calls = []
        for prompt_message in extract_stream_tool_calls(llm_result_chunk):
            parsed = parse_tool_arguments(prompt_message.function.arguments)

            tool_calls.append(
                (
                    prompt_message.id,
                    prompt_message.function.name,
                    parsed.args,
                    parsed.error,
                )
            )

        return tool_calls

    def extract_blocking_tool_calls(
        self, llm_result: LLMResult
    ) -> list[tuple[str, str, dict[str, Any], str | None]]:
        """
        Extract blocking tool calls from llm result

        Returns:
            List[Tuple[str, str, Dict[str, Any], Optional[str]]]:
                [(tool_call_id, tool_call_name, tool_call_args, parse_error)]
        """
        tool_calls = []
        for prompt_message in extract_blocking_tool_calls(llm_result):
            parsed = parse_tool_arguments(prompt_message.function.arguments)

            tool_calls.append(
                (
                    prompt_message.id,
                    prompt_message.function.name,
                    parsed.args,
                    parsed.error,
                )
            )

        return tool_calls

    def _init_system_message(
        self, prompt_template: str, prompt_messages: list[PromptMessage]
    ) -> list[PromptMessage]:
        """
        Initialize system message
        """
        if not prompt_messages and prompt_template:
            return [
                SystemPromptMessage(content=prompt_template),
            ]

        if (
            prompt_messages
            and not isinstance(prompt_messages[0], SystemPromptMessage)
            and prompt_template
        ):
            prompt_messages.insert(
                0, SystemPromptMessage(content=prompt_template)
            )

        return prompt_messages or []

    def _clear_user_prompt_image_messages(
        self, prompt_messages: list[PromptMessage]
    ) -> list[PromptMessage]:
        """
        Clear image messages from prompt messages.
        Converts image content to "[image]" placeholder text.

        This is needed because:
        1. Some models don't support vision at all
        2. Some models support vision in the first iteration,
            but not in subsequent iterations
            (when tool calls are involved)
        """
        prompt_messages = deepcopy(prompt_messages)

        for prompt_message in prompt_messages:
            if isinstance(prompt_message, UserPromptMessage) and isinstance(
                prompt_message.content, list
            ):
                prompt_message.content = "\n".join(
                    [
                        (
                            content.data
                            if content.type == PromptMessageContentType.TEXT
                            else (
                                "[image]"
                                if content.type
                                == PromptMessageContentType.IMAGE
                                else "[file]"
                            )
                        )
                        for content in prompt_message.content
                    ]
                )

        return prompt_messages

    def _organize_prompt_messages(
        self,
        current_thoughts: list[PromptMessage],
        history_prompt_messages: list[PromptMessage],
        model: AgentModelConfig | None = None,
    ) -> list[PromptMessage]:
        prompt_messages = [
            *history_prompt_messages,
            *current_thoughts,
        ]

        # Check if model supports vision
        supports_vision = (
            ModelFeature.VISION in model.entity.features
            if model and model.entity and model.entity.features
            else False
        )

        # Clear images if: model doesn't support vision OR it's not the first iteration
        if not supports_vision or len(current_thoughts) != 0:
            prompt_messages = self._clear_user_prompt_image_messages(
                prompt_messages
            )

        return prompt_messages

    def _to_agent_invoke_message(
        self, tool_invoke_response: ToolInvokeMessage
    ) -> AgentInvokeMessage:
        """Normalize tool-invoke payloads to AgentInvokeMessage for downstream UI."""
        return cast(AgentInvokeMessage, tool_invoke_response)

    def _max_blob_file_bytes(self) -> int:
        return self._MAX_BLOB_FILE_BYTES

    def _resolve_safe_local_file_path(self, file_info: str) -> str | None:
        if not file_info.startswith(f"{self._LOCAL_FILE_ROOT}/"):
            return None

        root_real = os.path.realpath(self._LOCAL_FILE_ROOT)
        candidate_real = os.path.realpath(file_info)
        try:
            common = os.path.commonpath([root_real, candidate_real])
        except ValueError:
            return None

        if common != root_real:
            return None

        return candidate_real

    def _read_local_file_for_blob(
        self, file_info: str
    ) -> tuple[bytes, str] | None:
        safe_path = self._resolve_safe_local_file_path(file_info)
        if safe_path is None or not os.path.exists(safe_path):
            return None

        max_bytes = self._max_blob_file_bytes()
        file_size = os.path.getsize(safe_path)
        if file_size > max_bytes:
            raise ValueError("local file is too large")

        with open(safe_path, "rb") as f:
            content = f.read(max_bytes + 1)

        if len(content) > max_bytes:
            raise ValueError("local file is too large")

        return content, os.path.basename(safe_path)
