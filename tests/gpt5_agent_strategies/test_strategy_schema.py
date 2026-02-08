from __future__ import annotations

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
PLUGIN_DIR = BASE_DIR / "app" / "gpt5_agent_strategies"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _parameter_names(strategy_yaml: str) -> set[str]:
    data = _load_yaml(PLUGIN_DIR / "strategies" / strategy_yaml)
    return {item["name"] for item in data["parameters"]}


def test_function_calling_strategy_has_required_parameters() -> None:
    names = _parameter_names("gpt5_function_calling.yaml")
    assert {
        "model",
        "tools",
        "instruction",
        "query",
        "maximum_iterations",
    }.issubset(names)


def test_react_strategy_has_required_parameters() -> None:
    names = _parameter_names("gpt5_react.yaml")
    assert {
        "model",
        "tools",
        "instruction",
        "query",
        "maximum_iterations",
    }.issubset(names)
