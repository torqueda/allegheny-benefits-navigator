from __future__ import annotations

import json
import os
import re
import hashlib
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from .models import PolicyChunk, PolicyDocument

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "your",
    "have",
    "when",
    "they",
    "are",
    "can",
    "may",
    "not",
    "only",
    "still",
    "need",
    "needs",
}

DEFAULT_INDEX_DIR = Path("data/policy_index/main")
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
LOCAL_EMBEDDING_MODEL = "hashed-bow-v1"
DEFAULT_BATCH_SIZE = 64
LOCAL_EMBEDDING_DIM = 768
MIN_CHUNK_TOKENS = 80
TARGET_CHUNK_TOKENS = 220
MAX_CHUNK_TOKENS = 320

NON_INDEXABLE_TITLE_MARKERS = (
    "forms and publications",
    "operations memoranda",
    "policy clarifications",
    "copy of ",
)

NOISE_LINE_PATTERNS = (
    re.compile(r"^\(?spanish\)?(\s+\(?[a-z][a-z\s-]+\)?)*$", flags=re.IGNORECASE),
    re.compile(r"^\(?chinese\)?(\s+\(?[a-z][a-z\s-]+\)?)*$", flags=re.IGNORECASE),
    re.compile(r"^\(.*\)$"),
    re.compile(r"^updated\s+\w+", flags=re.IGNORECASE),
    re.compile(r"^form or publication number$", flags=re.IGNORECASE),
    re.compile(r"^[A-Z0-9/-]{2,}$"),
)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


load_dotenv(project_root() / ".env")


def data_dir() -> Path:
    return project_root() / "data"


def policy_corpus_dir() -> Path:
    return data_dir() / "policy_corpus"


def uploaded_policy_dir() -> Path:
    return data_dir() / "uploaded_policies"


def policy_index_dir() -> Path:
    return project_root() / DEFAULT_INDEX_DIR


def embedding_provider() -> str:
    return os.getenv("POLICY_EMBEDDING_PROVIDER", "openai").strip().lower()


def allow_local_embedding_fallback() -> bool:
    return os.getenv("POLICY_ALLOW_LOCAL_EMBEDDING_FALLBACK", "").strip().lower() in {"1", "true", "yes"}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9/+-]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def handbook_corpus_dirs() -> list[Path]:
    corpus_root = policy_corpus_dir()
    if not corpus_root.exists():
        return []
    return sorted(
        path
        for path in corpus_root.iterdir()
        if path.is_dir() and path.name.endswith("_handbook")
    )


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return {}, text
    metadata_block, body = parts
    metadata: dict[str, str] = {}
    for line in metadata_block.splitlines()[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, body.strip()


def _guess_program_name(title: str, content: str) -> str:
    normalized = f"{title}\n{content}".lower()
    if "lihwap" in normalized or "water assistance program" in normalized:
        return "LIHWAP"
    if "snap" in normalized:
        return "SNAP"
    if "chip" in normalized or "medicaid" in normalized or "medical assistance" in normalized:
        return "Medicaid/CHIP"
    if "liheap" in normalized or "heating" in normalized or "utility" in normalized:
        return "LIHEAP"
    return title


def _infer_tags(text: str) -> list[str]:
    normalized = text.lower()
    tags = []
    for tag, keywords in {
        "food": ["food", "groceries", "nutrition", "meals"],
        "health": ["medicaid", "chip", "insurance", "coverage", "pregnancy"],
        "energy": ["liheap", "heating", "utility", "energy", "gas bill", "shutoff"],
        "documents": ["proof", "document", "application", "submit", "bring"],
    }.items():
        if any(keyword in normalized for keyword in keywords):
            tags.append(tag)
    return tags


def load_policy_documents(*, include_uploaded: bool = True) -> list[PolicyDocument]:
    documents: list[PolicyDocument] = []

    for source_dir in handbook_corpus_dirs():
        for path in sorted(source_dir.glob("*.md")):
            raw_content = path.read_text(encoding="utf-8")
            metadata, content = _split_frontmatter(raw_content)
            title = metadata.get("title", path.stem.replace("_", " ").title())
            program_name = metadata.get("program") or _guess_program_name(title, content)
            if not _is_indexable_document(title, metadata.get("source_url", ""), content):
                continue
            documents.append(
                PolicyDocument(
                    document_id=path.stem,
                    title=title,
                    program_name=program_name,
                    source_type="local_policy_corpus",
                    content=content,
                    source_url=metadata.get("source_url"),
                    tags=_infer_tags(content),
                    uploaded=False,
                )
            )

    if include_uploaded:
        upload_dir = uploaded_policy_dir()
        if upload_dir.exists():
            for path in sorted(upload_dir.glob("*.md")):
                raw_content = path.read_text(encoding="utf-8")
                metadata, content = _split_frontmatter(raw_content)
                title = metadata.get("title", path.stem.replace("_", " ").title())
                program_name = metadata.get("program") or _guess_program_name(title, content)
                documents.append(
                    PolicyDocument(
                        document_id=path.stem,
                        title=title,
                        program_name=program_name,
                        source_type="uploaded_policy",
                        content=content,
                        source_url=metadata.get("source_url"),
                        tags=_infer_tags(content),
                        uploaded=True,
                    )
                )

    return documents


def build_chunks_from_text(
    text: str,
    document_id: str,
    title: str,
    program_name: str,
    source_url: str | None = None,
) -> list[PolicyChunk]:
    lines = text.splitlines()
    current_section = title
    paragraph_buffer: list[str] = []
    paragraph_groups: list[tuple[str, list[str]]] = []
    chunks: list[PolicyChunk] = []
    chunk_index = 0

    def flush_paragraph() -> None:
        nonlocal paragraph_buffer
        block = " ".join(paragraph_buffer).strip()
        paragraph_buffer = []
        if not block:
            return
        normalized = _normalize_line(block)
        if not normalized:
            return
        paragraph_groups.append((current_section, [normalized]))

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue
        if line.startswith("#"):
            flush_paragraph()
            current_section = line.lstrip("#").strip() or current_section
            continue
        normalized_line = _normalize_line(line)
        if not normalized_line:
            continue
        paragraph_buffer.append(normalized_line)

    flush_paragraph()

    if not paragraph_groups:
        normalized = _normalize_line(text)
        if not normalized:
            return []
        paragraph_groups = [(title, [normalized])]

    current_chunk_section = paragraph_groups[0][0]
    current_chunk_parts: list[str] = []
    current_chunk_tokens = 0

    def flush_chunk() -> None:
        nonlocal chunk_index, current_chunk_parts, current_chunk_tokens, current_chunk_section
        block = " ".join(current_chunk_parts).strip()
        if not block:
            current_chunk_parts = []
            current_chunk_tokens = 0
            return
        chunks.append(
            PolicyChunk(
                chunk_id=f"{document_id}::chunk_{chunk_index}",
                document_id=document_id,
                program_name=program_name,
                title=title,
                section_title=current_chunk_section,
                source_url=source_url,
                text=block,
            )
        )
        chunk_index += 1
        current_chunk_parts = []
        current_chunk_tokens = 0

    for section_title, parts in paragraph_groups:
        for part in parts:
            part_tokens = len(_tokenize(part))
            if part_tokens == 0:
                continue
            if not current_chunk_parts:
                current_chunk_section = section_title
            if current_chunk_parts and (
                current_chunk_tokens + part_tokens > MAX_CHUNK_TOKENS
                or (section_title != current_chunk_section and current_chunk_tokens >= MIN_CHUNK_TOKENS)
            ):
                flush_chunk()
                current_chunk_section = section_title
            current_chunk_parts.append(part)
            current_chunk_tokens += part_tokens
            if current_chunk_tokens >= TARGET_CHUNK_TOKENS:
                flush_chunk()

    flush_chunk()

    return chunks


def build_policy_chunks(documents: list[PolicyDocument]) -> list[PolicyChunk]:
    chunks: list[PolicyChunk] = []
    for document in documents:
        chunks.extend(
            build_chunks_from_text(
                document.content,
                document.document_id,
                document.title,
                document.program_name,
                document.source_url,
            )
        )
    return chunks


def embed_texts(texts: list[str], *, model: str = DEFAULT_EMBEDDING_MODEL, batch_size: int = DEFAULT_BATCH_SIZE) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=np.float32)

    provider = embedding_provider()
    if model == LOCAL_EMBEDDING_MODEL or provider == "local":
        return _hashed_bow_embeddings(texts)

    if provider != "openai":
        raise ValueError(
            f"Unsupported POLICY_EMBEDDING_PROVIDER '{provider}'. "
            "Use 'openai' or 'local'."
        )

    client = _openai_client()
    rows: list[list[float]] = []
    try:
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = client.embeddings.create(model=model, input=batch)
            rows.extend(item.embedding for item in response.data)
        return np.asarray(rows, dtype=np.float32)
    except Exception as exc:
        if allow_local_embedding_fallback():
            return _hashed_bow_embeddings(texts)
        raise RuntimeError(
            f"OpenAI embedding request failed for model '{model}'. "
            "Check OPENAI_API_KEY, network connectivity, and model access. "
            "If you intentionally want a local fallback, set POLICY_ALLOW_LOCAL_EMBEDDING_FALLBACK=true."
        ) from exc


def embed_policy_chunks(
    chunks: list[PolicyChunk],
    *,
    model: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> np.ndarray:
    if not chunks:
        return np.zeros((0, 0), dtype=np.float32)
    return embed_texts([chunk.text for chunk in chunks], model=model, batch_size=batch_size)


def save_policy_index(
    chunks: list[PolicyChunk],
    embeddings: np.ndarray,
    output_dir: Path | None = None,
    *,
    embedding_model: str = "hashed-bow-v1",
) -> dict:
    if embeddings.shape[0] != len(chunks):
        raise ValueError("Embedding row count must match the number of chunks.")

    index_dir = output_dir or policy_index_dir()
    index_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = index_dir / "chunks.jsonl"
    with chunks_path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")

    embeddings_path = index_dir / "embeddings.npy"
    np.save(embeddings_path, embeddings)

    manifest = {
        "chunk_count": len(chunks),
        "embedding_dim": int(embeddings.shape[1]) if embeddings.ndim == 2 and embeddings.size else 0,
        "embedding_model": embedding_model,
        "program_counts": _program_counts(chunks),
        "chunks_path": str(chunks_path),
        "embeddings_path": str(embeddings_path),
    }
    manifest_path = index_dir / "index_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_policy_index(index_dir: Path | None = None) -> tuple[list[PolicyChunk], np.ndarray, dict]:
    resolved_index_dir = index_dir or policy_index_dir()
    manifest_path = resolved_index_dir / "index_manifest.json"
    chunks_path = resolved_index_dir / "chunks.jsonl"
    embeddings_path = resolved_index_dir / "embeddings.npy"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing index manifest: {manifest_path}")
    if not chunks_path.exists():
        raise FileNotFoundError(f"Missing chunk store: {chunks_path}")
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Missing embedding store: {embeddings_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    chunks = [
        PolicyChunk(**json.loads(line))
        for line in chunks_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    embeddings = np.load(embeddings_path)
    return chunks, embeddings, manifest


def build_and_save_policy_index(
    *,
    include_uploaded: bool = True,
    output_dir: Path | None = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    documents = load_policy_documents(include_uploaded=include_uploaded)
    chunks = build_policy_chunks(documents)
    embeddings = embed_policy_chunks(chunks, model=embedding_model, batch_size=batch_size)
    used_embedding_model = embedding_model
    if (
        embedding_provider() == "local"
        or (
            embeddings.ndim == 2
            and embeddings.shape[1] == LOCAL_EMBEDDING_DIM
            and embedding_model != LOCAL_EMBEDDING_MODEL
        )
    ):
        used_embedding_model = LOCAL_EMBEDDING_MODEL
    return save_policy_index(chunks, embeddings, output_dir, embedding_model=used_embedding_model)


def append_document_to_policy_index(
    document: PolicyDocument,
    *,
    output_dir: Path | None = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict:
    try:
        existing_chunks, existing_embeddings, _ = load_policy_index(output_dir)
    except FileNotFoundError:
        return build_and_save_policy_index(output_dir=output_dir, embedding_model=embedding_model, batch_size=batch_size)

    # Remove stale chunks for this document so re-uploading the same title doesn't duplicate
    keep_indices = [i for i, c in enumerate(existing_chunks) if c.document_id != document.document_id]
    filtered_chunks = [existing_chunks[i] for i in keep_indices]
    filtered_embeddings = existing_embeddings[keep_indices] if keep_indices else np.zeros((0, existing_embeddings.shape[1] if existing_embeddings.ndim == 2 else 0), dtype=np.float32)

    new_chunks = build_chunks_from_text(
        document.content, document.document_id, document.title,
        document.program_name, document.source_url,
    )
    if not new_chunks:
        return save_policy_index(filtered_chunks, filtered_embeddings, output_dir, embedding_model=embedding_model)

    new_embeddings = embed_policy_chunks(new_chunks, model=embedding_model, batch_size=batch_size)
    used_model = LOCAL_EMBEDDING_MODEL if (
        embedding_provider() == "local"
        or (new_embeddings.ndim == 2 and new_embeddings.shape[1] == LOCAL_EMBEDDING_DIM and embedding_model != LOCAL_EMBEDDING_MODEL)
    ) else embedding_model

    if filtered_chunks and filtered_embeddings.size > 0:
        all_chunks = filtered_chunks + new_chunks
        all_embeddings = np.vstack([filtered_embeddings, new_embeddings])
    else:
        all_chunks = new_chunks
        all_embeddings = new_embeddings

    return save_policy_index(all_chunks, all_embeddings, output_dir, embedding_model=used_model)


def _program_counts(chunks: list[PolicyChunk]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for chunk in chunks:
        counts[chunk.program_name] = counts.get(chunk.program_name, 0) + 1
    return counts


def _normalize_line(text: str) -> str:
    normalized = text.replace("Â", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized:
        return ""
    lowered = normalized.lower()
    if any(marker in lowered for marker in ("(spanish)", "(chinese)", "(russian)", "(vietnamese)", "(arabic)", "(cambodian)", "(haitian creole)", "(nepali)", "(portuguese)")):
        return ""
    if any(pattern.match(normalized) for pattern in NOISE_LINE_PATTERNS):
        return ""
    if len(_tokenize(normalized)) < 5 and not re.search(r"\b(must|may|eligible|income|application|verification|benefit|household|medical|energy|assistance|snap|liheap|chip)\b", lowered):
        return ""
    return normalized


def _is_indexable_document(title: str, source_url: str, content: str) -> bool:
    normalized = f"{title} {source_url}".lower()
    if any(marker in normalized for marker in NON_INDEXABLE_TITLE_MARKERS):
        return False
    if "forms and publications" in normalized:
        return False
    if len(_tokenize(content)) < 40:
        return False
    return True


def _openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment before building the policy index.")
    return OpenAI(api_key=api_key)


def _hashed_bow_embeddings(texts: list[str], *, dim: int = LOCAL_EMBEDDING_DIM) -> np.ndarray:
    matrix = np.zeros((len(texts), dim), dtype=np.float32)
    for row_idx, text in enumerate(texts):
        for token in _tokenize(text):
            token_hash = hashlib.md5(token.encode("utf-8")).hexdigest()
            bucket = int(token_hash[:8], 16) % dim
            matrix[row_idx, bucket] += 1.0

        norm = float(np.linalg.norm(matrix[row_idx]))
        if norm > 0:
            matrix[row_idx] /= norm
    return matrix
