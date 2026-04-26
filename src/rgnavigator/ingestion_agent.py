from __future__ import annotations

import re
from pathlib import Path

from .models import PolicyDocument
from .policy_store import _guess_program_name, _infer_tags, append_document_to_policy_index, data_dir


def ingest_policy_text(title: str, raw_text: str) -> Path:
    if not title.strip():
        raise ValueError("Policy title is required.")
    if not raw_text.strip():
        raise ValueError("Policy text is required.")

    clean_title = title.strip()
    clean_text = raw_text.strip()
    safe_name = re.sub(r"[^a-z0-9]+", "_", clean_title.lower()).strip("_")
    path = data_dir() / "uploaded_policies" / f"{safe_name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {clean_title}\n\n{clean_text}\n", encoding="utf-8")

    document = PolicyDocument(
        document_id=safe_name,
        title=clean_title,
        program_name=_guess_program_name(clean_title, clean_text),
        source_type="uploaded_policy",
        content=clean_text,
        tags=_infer_tags(clean_text),
        uploaded=True,
    )
    append_document_to_policy_index(document)
    return path
