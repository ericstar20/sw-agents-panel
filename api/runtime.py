"""Identify the backend code loaded by a dashboard service."""

import hashlib
from pathlib import Path


def backend_revision(root):
    digest = hashlib.sha256()
    for path in sorted((Path(root) / "api").rglob("*.py")):
        if "tests" in path.parts:
            continue
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
