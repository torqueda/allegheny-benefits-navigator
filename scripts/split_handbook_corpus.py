from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_SOURCE_DIR = Path("data/policy_corpus/snap_v8_clean")
DEFAULT_HANDBOOK_DIR = Path("data/policy_corpus/snap_v8_handbook")
DEFAULT_GLOSSARY_DIR = Path("data/policy_corpus/snap_v8_glossary")

EXCLUDED_SOURCE_MARKERS = (
    "/whxdata/",
    "/whgdata/",
    "/template/scripts/",
    "/template/styles/",
    "/template/azure_blue/",
)
EXCLUDED_FILENAME_MARKERS = (
    "projectsettings",
    "search_topics",
    "search_db",
    "whtagdata",
    "projectdata",
    "csh_redirect",
)
GLOSSARY_SOURCE_MARKERS = (
    "/popups/",
    "/glossary/",
)
GLOSSARY_TEXT_MARKERS = (
    " glossary",
    "definitions",
    "definition of ",
    "define ",
    "terminology",
)


@dataclass
class SplitRecord:
    filename: str
    source_url: str
    source_title: str
    category: str
    destination_path: str


def categorize_record(source_url: str, source_title: str, filename: str) -> str:
    normalized = f"{source_url} {source_title} {filename}".lower()
    if any(marker in normalized for marker in EXCLUDED_SOURCE_MARKERS):
        return "excluded"
    if any(marker in filename.lower() for marker in EXCLUDED_FILENAME_MARKERS):
        return "excluded"
    if any(marker in normalized for marker in GLOSSARY_SOURCE_MARKERS):
        return "glossary"
    if any(marker in normalized for marker in GLOSSARY_TEXT_MARKERS):
        return "glossary"
    return "handbook"


def split_corpus(source_dir: Path, handbook_dir: Path, glossary_dir: Path) -> dict:
    manifest_path = source_dir / "clean_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing clean manifest: {manifest_path}")

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    handbook_dir.mkdir(parents=True, exist_ok=True)
    glossary_dir.mkdir(parents=True, exist_ok=True)

    handbook_records: list[SplitRecord] = []
    glossary_records: list[SplitRecord] = []
    excluded_records: list[SplitRecord] = []
    missing_files: list[str] = []

    for record in payload.get("records", []):
        filename = Path(record["output_path"]).name
        source_file = source_dir / filename
        if not source_file.exists():
            missing_files.append(filename)
            continue

        category = categorize_record(record["source_url"], record["source_title"], filename)
        if category == "excluded":
            excluded_records.append(
                SplitRecord(
                    filename=filename,
                    source_url=record["source_url"],
                    source_title=record["source_title"],
                    category=category,
                    destination_path="",
                )
            )
            continue

        destination_dir = handbook_dir if category == "handbook" else glossary_dir
        destination_file = destination_dir / filename
        shutil.copy2(source_file, destination_file)

        split_record = SplitRecord(
            filename=filename,
            source_url=record["source_url"],
            source_title=record["source_title"],
            category=category,
            destination_path=str(destination_file),
        )
        if category == "handbook":
            handbook_records.append(split_record)
        else:
            glossary_records.append(split_record)

    summary = {
        "source_dir": str(source_dir),
        "handbook_dir": str(handbook_dir),
        "glossary_dir": str(glossary_dir),
        "handbook_count": len(handbook_records),
        "glossary_count": len(glossary_records),
        "excluded_count": len(excluded_records),
        "missing_files": missing_files,
        "handbook_records": [asdict(record) for record in handbook_records],
        "glossary_records": [asdict(record) for record in glossary_records],
        "excluded_records": [asdict(record) for record in excluded_records],
    }
    (source_dir / "split_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Split a cleaned policy handbook corpus into handbook and glossary sets.")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR))
    parser.add_argument("--handbook-dir", default=str(DEFAULT_HANDBOOK_DIR))
    parser.add_argument("--glossary-dir", default=str(DEFAULT_GLOSSARY_DIR))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    summary = split_corpus(Path(args.source_dir), Path(args.handbook_dir), Path(args.glossary_dir))
    print(
        json.dumps(
            {
                "handbook_count": summary["handbook_count"],
                "glossary_count": summary["glossary_count"],
                "excluded_count": summary["excluded_count"],
                "missing_files": len(summary["missing_files"]),
                "split_manifest_path": str(Path(args.source_dir) / "split_manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
