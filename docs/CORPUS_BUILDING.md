# Building The SNAP Corpus

The upgraded project supports a two-stage corpus-building workflow:

1. crawl raw SNAP handbook HTML into `data/raw_policy_downloads/snap/`
2. clean the raw HTML into retrieval-friendly markdown in
   `data/policy_corpus/snap/`

## 1. Crawl Raw HTML

Run from `retrieval_grounded_navigator/`:

```bash
python3 scripts/crawl_snap_handbook.py
```

Optional flags:

- `--start-url`: override or add handbook entry points
- `--allowed-prefix`: add or replace allowed SNAP handbook URL prefixes
- `--max-pages`: cap the crawl size
- `--delay-seconds`: be more polite or more aggressive
- `--timeout-seconds`: increase request timeout for slow handbook pages
- `--retries`: retry slow or flaky requests

Outputs:

- raw HTML files in `data/raw_policy_downloads/snap/`
- `manifest.json` listing downloaded pages and failures

If the handbook site is slow, try:

```bash
python3 scripts/crawl_snap_handbook.py --timeout-seconds 60 --retries 4 --delay-seconds 0.6
```

## 2. Clean Into Markdown

Run:

```bash
python3 scripts/clean_snap_handbook.py
```

Outputs:

- cleaned markdown files in `data/policy_corpus/snap/`
- `clean_manifest.json` describing which files were produced or skipped

## Notes

- The cleaner skips obvious glossary / memo index pages by title.
- The raw crawl is intentionally broader than the cleaned corpus.
- After cleaning, you can manually review the markdown files and keep only the
  pages you want in the active retrieval corpus.
- This workflow is designed to support source grounding, not legal-grade policy
  interpretation.
