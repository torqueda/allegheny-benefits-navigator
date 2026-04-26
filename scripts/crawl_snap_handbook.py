from __future__ import annotations

import argparse
import ast
import json
import re
import time
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_START_URL = "https://services.dpw.state.pa.us/oimpolicymanuals/snap/index.htm"
DEFAULT_SECONDARY_START_URL = "https://services.dpw.state.pa.us/oimpolicymanuals/snap/SNAP_Handbook_Title_Page.htm"
DEFAULT_ALLOWED_PREFIX = "https://services.dpw.state.pa.us/oimpolicymanuals/snap/"
DEFAULT_OUTPUT_DIR = Path("data/raw_policy_downloads/snap")
DEFAULT_DELAY_SECONDS = 0.35

EXCLUDE_SUBSTRINGS = (
    "/assets/",
    "/OIMArchive/",
    "/whgdata/",
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    "mailto:",
    "javascript:",
)

DISCOVERY_JS_SUFFIXES = (
    "/whxdata/projectsettings.js",
    "/whxdata/search_topics.js",
    "/whxdata/search_db.js",
    "/whxdata/whtagdata.js",
    "/template/scripts/projectdata.js",
)

HTML_SUFFIXES = (".htm", ".html")
SAFE_TOPIC_PATTERN = re.compile(r"^[A-Za-z0-9_./-]+\.(?:htm|html)$", flags=re.IGNORECASE)
ROOT_DISCOVERY_RELATIVE_PATHS = (
    "whxdata/projectsettings.js",
    "whxdata/search_topics.js",
    "whxdata/search_db.js",
    "whxdata/whtagdata.js",
    "template/scripts/projectdata.js",
)


@dataclass
class DownloadRecord:
    url: str
    local_path: str
    title: str
    status_code: int
    downloaded_at_epoch: float


def normalize_url(base_url: str, href: str) -> str | None:
    if not href:
        return None
    href = href.strip()
    if not href:
        return None

    # Adobe RoboHelp search metadata often stores handbook-relative paths
    # with a leading slash even though they are not domain-root absolute URLs.
    parsed_base = urlparse(base_url)
    if href.startswith("/") and parsed_base.path.startswith("/oimpolicymanuals/"):
        href = href.lstrip("/")

    resolved = urljoin(base_url, href)
    resolved, _fragment = urldefrag(resolved)
    if any(token in resolved for token in EXCLUDE_SUBSTRINGS):
        return None

    parsed = urlparse(resolved)
    if parsed.scheme not in {"http", "https"}:
        return None
    return resolved


def url_allowed(url: str, allowed_prefixes: Iterable[str]) -> bool:
    return any(url.startswith(prefix) for prefix in allowed_prefixes)


def is_html_like_url(url: str) -> bool:
    lowered = url.lower()
    return any(lowered.endswith(suffix) for suffix in HTML_SUFFIXES)


def is_discovery_js_url(url: str) -> bool:
    lowered = url.lower()
    return any(lowered.endswith(suffix) for suffix in DISCOVERY_JS_SUFFIXES)


def should_fetch_url(url: str) -> bool:
    return is_html_like_url(url) or is_discovery_js_url(url)


def slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    parts = [segment for segment in parsed.path.split("/") if segment]
    if not parts:
        return "root"
    stem = "__".join(parts)
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in stem)
    return safe


def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return title
    h1 = soup.find("h1")
    return h1.get_text(" ", strip=True) if h1 else "Untitled Page"


def is_likely_topic_path(candidate: str) -> bool:
    candidate = candidate.strip()
    if not candidate:
        return False
    if not SAFE_TOPIC_PATTERN.match(candidate):
        return False
    if candidate.startswith(("http://", "https://", "//")):
        return False
    if any(token in candidate for token in (" ", "+", ":", "\\", "?", "&", "{", "}", "(", ")", ",")):
        return False
    lowered = candidate.lower()
    if lowered.startswith(("template/", "assets/", "whxdata/")):
        return False
    return True


def is_shell_html_url(url: str) -> bool:
    lowered = url.lower()
    path = urlparse(lowered).path
    file_name = Path(path).name
    if file_name in {"index.htm", "index.html", "csh-redirect.htm", "csh-redirect.html"}:
        return True
    if file_name in {"title_page.htm", "title_page.html"}:
        return True
    return file_name.endswith("_title_page.htm") or file_name.endswith("_title_page.html")


def collect_root_discovery_urls(allowed_prefixes: Iterable[str]) -> list[str]:
    discovered: list[str] = []
    for prefix in allowed_prefixes:
        for relative_path in ROOT_DISCOVERY_RELATIVE_PATHS:
            normalized = normalize_url(prefix, relative_path)
            if normalized and url_allowed(normalized, allowed_prefixes) and is_discovery_js_url(normalized):
                discovered.append(normalized)
    return discovered


def collect_links_from_html(base_url: str, html: str, allowed_prefixes: Iterable[str]) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    discovered: list[str] = collect_root_discovery_urls(allowed_prefixes)

    if not is_shell_html_url(base_url):
        # For topic pages, rely on search_topics.js as the authoritative page list.
        # Following intra-topic links causes many bogus nested paths.
        return discovered

    tag_specs = [
        ("a", "href"),
        ("frame", "src"),
        ("iframe", "src"),
    ]
    for tag_name, attr_name in tag_specs:
        for tag in soup.find_all(tag_name):
            candidate = tag.get(attr_name)
            normalized = normalize_url(base_url, candidate)
            if normalized and url_allowed(normalized, allowed_prefixes) and should_fetch_url(normalized):
                discovered.append(normalized)

    for meta_name in ("gDefaultTopic", "gCSHRedirectHTM"):
        tag = soup.find("meta", attrs={"name": meta_name})
        candidate = tag.get("content") if tag else None
        normalized = normalize_url(base_url, candidate or "")
        if normalized and url_allowed(normalized, allowed_prefixes) and should_fetch_url(normalized):
            discovered.append(normalized)

    # Allow the shell pages to reveal the two key RoboHelp discovery files.
    for match in re.findall(r"""['"]([^'"]+\.(?:js))(?:#[^'"]*)?['"]""", html, flags=re.IGNORECASE):
        normalized = normalize_url(base_url, match)
        if normalized and url_allowed(normalized, allowed_prefixes) and is_discovery_js_url(normalized):
            discovered.append(normalized)
    return discovered


def collect_links_from_discovery_js(base_url: str, text: str, allowed_prefixes: Iterable[str]) -> list[str]:
    discovered: list[str] = []
    root_base = next(iter(allowed_prefixes), base_url)

    if base_url.lower().endswith("/whxdata/search_topics.js"):
        exports_match = re.search(r"""rh\._\.exports\((.*)\)\s*;?\s*$""", text, flags=re.DOTALL)
        if exports_match:
            payload = exports_match.group(1).strip()
            try:
                exported = ast.literal_eval(payload)
            except (SyntaxError, ValueError):
                exported = None

            if isinstance(exported, str):
                try:
                    exported = json.loads(exported)
                except json.JSONDecodeError:
                    exported = None

            if isinstance(exported, dict):
                for topic in exported.get("metadata", {}).values():
                    if not isinstance(topic, dict):
                        continue
                    rel_url = topic.get("relUrl")
                    if not isinstance(rel_url, str):
                        continue
                    normalized = normalize_url(root_base, rel_url)
                    if normalized and url_allowed(normalized, allowed_prefixes) and is_html_like_url(normalized):
                        discovered.append(normalized)

    for match in re.findall(r"""['"]([^'"]+\.(?:htm|html))(?:#[^'"]*)?['"]""", text, flags=re.IGNORECASE):
        if not is_likely_topic_path(match):
            continue
        normalized = normalize_url(root_base, match)
        if normalized and url_allowed(normalized, allowed_prefixes) and is_html_like_url(normalized):
            discovered.append(normalized)

    return discovered


def collect_links(url: str, text: str, allowed_prefixes: Iterable[str]) -> list[str]:
    if is_discovery_js_url(url):
        return collect_links_from_discovery_js(url, text, allowed_prefixes)
    if is_html_like_url(url):
        return collect_links_from_html(url, text, allowed_prefixes)
    return []


def crawl_handbook(
    start_urls: list[str],
    output_dir: Path,
    *,
    allowed_prefixes: list[str],
    max_pages: int,
    delay_seconds: float,
    timeout_seconds: float,
    retries: int,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "RetrievalGroundedNavigator/1.0 (course project corpus builder)",
        }
    )

    queue = deque(start_urls)
    visited: set[str] = set()
    records: list[DownloadRecord] = []
    failures: list[dict] = []

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        if not should_fetch_url(url):
            continue
        visited.add(url)

        response = None
        last_error: str | None = None
        for attempt in range(1, retries + 1):
            try:
                response = session.get(url, timeout=timeout_seconds)
                response.raise_for_status()
                break
            except requests.RequestException as exc:
                last_error = f"attempt {attempt}/{retries}: {exc}"
                time.sleep(min(delay_seconds * attempt, 2.0))

        if response is None:
            failures.append({"url": url, "error": last_error or "unknown request failure"})
            continue

        body_text = response.text
        title = extract_title(body_text) if is_html_like_url(url) else Path(urlparse(url).path).name
        file_name = slug_from_url(url) + ".html"
        local_path = output_dir / file_name
        local_path.write_text(body_text, encoding="utf-8")

        records.append(
            DownloadRecord(
                url=url,
                local_path=str(local_path.relative_to(output_dir.parent.parent)),
                title=title,
                status_code=response.status_code,
                downloaded_at_epoch=time.time(),
            )
        )

        for discovered in collect_links(url, body_text, allowed_prefixes):
            if discovered not in visited:
                queue.append(discovered)

        time.sleep(delay_seconds)

    manifest = {
        "start_urls": start_urls,
        "allowed_prefixes": allowed_prefixes,
        "download_count": len(records),
        "failure_count": len(failures),
        "records": [asdict(record) for record in records],
        "failures": failures,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl the Pennsylvania SNAP handbook into raw local HTML.")
    parser.add_argument("--start-url", action="append", dest="start_urls")
    parser.add_argument("--allowed-prefix", action="append", dest="allowed_prefixes")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-pages", type=int, default=300)
    parser.add_argument("--delay-seconds", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--retries", type=int, default=3)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    start_urls = args.start_urls or [DEFAULT_START_URL, DEFAULT_SECONDARY_START_URL]
    allowed_prefixes = args.allowed_prefixes or [DEFAULT_ALLOWED_PREFIX]
    manifest = crawl_handbook(
        start_urls,
        Path(args.output_dir),
        allowed_prefixes=allowed_prefixes,
        max_pages=args.max_pages,
        delay_seconds=args.delay_seconds,
        timeout_seconds=args.timeout_seconds,
        retries=args.retries,
    )
    print(
        json.dumps(
            {
                "download_count": manifest["download_count"],
                "failure_count": manifest["failure_count"],
                "manifest_path": str(Path(args.output_dir) / "manifest.json"),
                "start_urls": start_urls,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
