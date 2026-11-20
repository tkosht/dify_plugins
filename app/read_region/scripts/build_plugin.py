"""Generate category-exclusive plugin overlays from one canonical source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import yaml


def generate(kind: str, destination: Path, source: Path) -> dict[str, str]:
    destination.mkdir(parents=True, exist_ok=False)
    common = [
        "main.py",
        "adapter.py",
        "region_contract.py",
        "requirements.txt",
        "LICENSE",
        "PRIVACY.md",
        "_assets/icon.svg",
    ]
    if kind == "agent":
        selected = common + [
            "strategy_core.py",
            "strategies/region_ocr.py",
            "strategies/region_ocr.yaml",
            "provider/region_ocr.py",
            "provider/region_ocr.yaml",
            "_assets/agent-input.schema.json",
        ]
    else:
        selected = (
            common
            + ["provider/read_region.py", "provider/read_region.yaml"]
            + [
                f"tools/{name}.{extension}"
                for name in ("prepare_images", "read_region", "cleanup_images")
                for extension in ("py", "yaml")
            ]
        )
    hashes = {}
    for relative in selected:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / relative, target)
        hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest = yaml.safe_load((source / "manifest.yaml").read_text())
    if kind == "agent":
        manifest["name"] = "read_region_agent"
        manifest["label"] = {
            "en_US": "Region OCR Agent (validation candidate)"
        }
        manifest["description"] = {
            "en_US": "Dedicated OCR Agent strategy; system-bound run context, fixed preparation/cleanup, normal Dify model provider."
        }
        manifest["plugins"] = {
            "agent_strategies": ["provider/region_ocr.yaml"]
        }
        manifest["resource"]["permission"] = {
            "model": {"enabled": True, "llm": True}
        }
        readme = source / "AGENT_README.md"
    else:
        manifest["plugins"] = {"tools": ["provider/read_region.yaml"]}
        manifest["resource"]["permission"] = {}
        readme = source / "README.md"
    assert (
        sum(
            bool(manifest["plugins"].get(k))
            for k in (
                "tools",
                "models",
                "agent_strategies",
                "endpoints",
                "datasources",
                "triggers",
            )
        )
        == 1
    )
    (destination / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False)
    )
    shutil.copyfile(readme, destination / "README.md")
    (destination / "SOURCE_SHA256.json").write_text(
        json.dumps({"variant": kind, "files": hashes}, indent=2) + "\n"
    )
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("tool", "agent"), required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--package", type=Path)
    parser.add_argument("--dify", type=Path)
    args = parser.parse_args()
    app = Path(__file__).resolve().parents[1]
    hashes = generate(args.kind, args.destination, app / "plugin")
    if args.package:
        executable = args.dify or app / ".local-bin/dify"
        subprocess.run(
            [
                str(executable.resolve()),
                "plugin",
                "package",
                str(args.destination),
                "-o",
                str(args.package),
            ],
            check=True,
        )
    print(
        json.dumps(
            {
                "variant": args.kind,
                "overlay": str(args.destination),
                "source_files": len(hashes),
                "package": str(args.package) if args.package else None,
            }
        )
    )


if __name__ == "__main__":
    main()
