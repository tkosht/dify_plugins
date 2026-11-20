from pathlib import Path

import yaml

from scripts.build_plugin import generate


def test_category_exclusive_overlays_use_identical_canonical_source(tmp_path):
    source = Path(__file__).resolve().parents[1] / "plugin"
    for kind in ("tool", "agent"):
        destination = tmp_path / kind
        hashes = generate(kind, destination, source)
        manifest = yaml.safe_load((destination / "manifest.yaml").read_text())
        categories = {k for k, v in manifest["plugins"].items() if v}
        assert categories == (
            {"tools"} if kind == "tool" else {"agent_strategies"}
        )
        assert manifest["name"] == (
            "read_region" if kind == "tool" else "read_region_agent"
        )
        assert (destination / "adapter.py").read_bytes() == (
            source / "adapter.py"
        ).read_bytes()
        assert (destination / "region_contract.py").read_bytes() == (
            source / "region_contract.py"
        ).read_bytes()
        assert ".env" not in {p.name for p in destination.rglob("*")}
        assert hashes
