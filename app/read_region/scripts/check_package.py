"""Check CLI-produced category-exclusive archives against canonical sources."""

import hashlib
import sys
import zipfile
from pathlib import Path

import yaml

package = Path(sys.argv[1])
with zipfile.ZipFile(package) as archive:
    names = set(archive.namelist())
    manifest = yaml.safe_load(archive.read("manifest.yaml"))
    categories = {k for k, value in manifest["plugins"].items() if value}
    assert categories in ({"tools"}, {"agent_strategies"}), categories
    required = {
        "main.py",
        "adapter.py",
        "region_contract.py",
        "requirements.txt",
    }
    if categories == {"agent_strategies"}:
        assert manifest["name"] == "read_region_agent"
        required |= {
            "strategy_core.py",
            "strategies/region_ocr.py",
            "strategies/region_ocr.yaml",
            "provider/region_ocr.py",
            "provider/region_ocr.yaml",
            "_assets/agent-input.schema.json",
        }
    else:
        assert manifest["name"] == "read_region"
        required |= {
            "provider/read_region.yaml",
            "tools/read_region.py",
            "tools/prepare_images.py",
            "tools/cleanup_images.py",
        }
    assert required <= names, names
    assert not any(
        ".env" in n
        or "__pycache__" in n
        or ".venv" in n
        or n.startswith("/")
        or ".." in n.split("/")
        for n in names
    )
    root = package.parent / "plugin"
    for name in required:
        assert archive.read(name) == (root / name).read_bytes(), name
print(
    "CLI package category and canonical payload match:",
    hashlib.sha256(package.read_bytes()).hexdigest(),
)
