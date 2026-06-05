from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def cleanup_uploaded_policies():
    yield
    upload_dir = ROOT / "data" / "uploaded_policies"
    if upload_dir.exists():
        for path in upload_dir.glob("*.md"):
            path.unlink(missing_ok=True)
