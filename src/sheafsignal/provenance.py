from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    """Return the SHA256 checksum for a file."""
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def describe_input(path: str | Path) -> dict[str, Any]:
    """Describe an input file without reading it as domain data."""
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "exists": False, "sha256": ""}
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def write_provenance(
    path: str | Path,
    *,
    inputs: dict[str, str | Path | None],
    parameters: dict[str, Any],
    annotation_version: str = "",
) -> Path:
    """Write a JSON provenance companion for generated result tables."""
    path = Path(path)
    payload = {
        "annotation_version": annotation_version,
        "inputs": {
            key: describe_input(value) if value is not None else {"path": "", "exists": False, "sha256": ""}
            for key, value in inputs.items()
        },
        "parameters": parameters,
        "python": sys.version,
        "platform": platform.platform(),
        "argv": sys.argv,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)
    return path

