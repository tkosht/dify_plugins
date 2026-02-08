from app.gpt5_agent_strategies.strategies.gpt5_function_calling import (
    GPT5FunctionCallingParams,
    GPT5FunctionCallingStrategy,
)


class GPT5ReActParams(GPT5FunctionCallingParams):
    """Reuse function-calling parameters for a ReAct-like strategy."""


class GPT5ReActStrategy(GPT5FunctionCallingStrategy):
    """Reuse robust function-calling execution as a ReAct-like policy."""
