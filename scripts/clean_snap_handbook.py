from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

DEFAULT_RAW_DIR = Path("data/raw_policy_downloads/snap")
DEFAULT_OUTPUT_DIR = Path("data/policy_corpus/snap")
SKIP_TITLE_SUBSTRINGS = (
    "glossary",
    "operations memoranda",
    "policy clarifications",
    "words list",
)


@dataclass
class CleanRecord:
    source_url: str
    source_title: str
    output_path: str
    chapter_hint: str


def sanitize_filename(text: str) -> str:
    lowered = text.strip().lower().replace("&", "and")
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    return lowered.strip("_") or "untitled"


def slugify_program_name(program_name: str) -> str:
    return sanitize_filename(program_name)


def chapter_hint_from_title(title: str) -> str:
    match = re.search(r"(\d+(?:\.\d+)?)", title)
    return match.group(1) if match else ""


def looks_skippable(title: str, url: str) -> bool:
    normalized = f"{title} {url}".lower()
    return any(token in normalized for token in SKIP_TITLE_SUBSTRINGS)


def clean_html_to_markdown(
    html: str,
    *,
    source_url: str,
    source_title: str,
    program_name: str,
) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    body = soup.body or soup
    lines: list[str] = []

    title = source_title.strip() or "Untitled Page"
    chapter_hint = chapter_hint_from_title(title)

    lines.append("---")
    lines.append(f"program: {program_name}")
    lines.append("source_type: official_handbook")
    lines.append(f"title: {title}")
    lines.append(f"chapter: {chapter_hint or 'unknown'}")
    lines.append(f"source_url: {source_url}")
    lines.append("accessed_date: 2026-04-19")
    lines.append("jurisdiction: Pennsylvania")
    lines.append("---")
    lines.append("")
    lines.append(f"# {title}")
    lines.append("")

    seen = set()
    for element in body.find_all(["h1", "h2", "h3", "p", "li"]):
        text = element.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        lower = text.lower()
        if lower in seen:
            continue
        if len(text) < 3:
            continue
        if "updated " in lower and len(text) < 80:
            pass
        seen.add(lower)

        if element.name == "h1":
            continue
        if element.name == "h2":
            lines.append(f"## {text}")
        elif element.name == "h3":
            lines.append(f"### {text}")
        elif element.name == "li":
            lines.append(f"- {text}")
        else:
            lines.append(text)
        lines.append("")

    markdown = "\n".join(lines).strip() + "\n"
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown


def clean_handbook(raw_dir: Path, output_dir: Path, *, program_name: str) -> dict:
    manifest_path = raw_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing manifest: {manifest_path}")

    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    clean_records: list[CleanRecord] = []
    skipped: list[dict] = []
    for record in raw_manifest.get("records", []):
        source_url = record["url"]
        source_title = record["title"]
        if looks_skippable(source_title, source_url):
            skipped.append({"url": source_url, "title": source_title, "reason": "skippable_title"})
            continue

        raw_file = raw_dir / Path(record["local_path"]).name
        if not raw_file.exists():
            skipped.append({"url": source_url, "title": source_title, "reason": "missing_raw_file"})
            continue

        html = raw_file.read_text(encoding="utf-8", errors="ignore")
        markdown = clean_html_to_markdown(
            html,
            source_url=source_url,
            source_title=source_title,
            program_name=program_name,
        )

        chapter_hint = chapter_hint_from_title(source_title)
        url_tail = Path(urlparse(source_url).path).stem
        program_slug = slugify_program_name(program_name)
        base_name = sanitize_filename(
            f"{program_slug}_{chapter_hint}_{url_tail}" if chapter_hint else f"{program_slug}_{url_tail}"
        )
        output_path = output_dir / f"{base_name}.md"
        output_path.write_text(markdown, encoding="utf-8")

        clean_records.append(
            CleanRecord(
                source_url=source_url,
                source_title=source_title,
                output_path=str(output_path.relative_to(output_dir.parent.parent)),
                chapter_hint=chapter_hint,
            )
        )

    clean_manifest = {
        "source_manifest": str(manifest_path),
        "clean_count": len(clean_records),
        "skipped_count": len(skipped),
        "records": [asdict(record) for record in clean_records],
        "skipped": skipped,
    }
    (output_dir / "clean_manifest.json").write_text(json.dumps(clean_manifest, indent=2), encoding="utf-8")
    return clean_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean raw handbook HTML into retrieval-friendly markdown.")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--program-name", default="SNAP")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    manifest = clean_handbook(Path(args.raw_dir), Path(args.output_dir), program_name=args.program_name)
    print(
        json.dumps(
            {
                "clean_count": manifest["clean_count"],
                "skipped_count": manifest["skipped_count"],
                "clean_manifest_path": str(Path(args.output_dir) / "clean_manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
