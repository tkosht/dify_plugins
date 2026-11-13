"""Check a CLI-produced archive against expected plugin source payload."""

import hashlib
import sys
import zipfile
from pathlib import Path

package = Path(sys.argv[1])
with zipfile.ZipFile(package) as archive:
    names = archive.namelist()
    required = {
        "manifest.yaml",
        "main.py",
        "adapter.py",
        "region_contract.py",
        "requirements.txt",
        "provider/read_region.yaml",
        "tools/read_region.py",
        "tools/prepare_images.py",
        "tools/cleanup_images.py",
    }
    assert required <= set(names), set(names)
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
    "CLI package source payload matches:",
    hashlib.sha256(package.read_bytes()).hexdigest(),
)
