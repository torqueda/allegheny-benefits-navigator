# Version Notes

## v1.0 — Phase 3 Final Submission (2026-04-25)

### What changed from Phase 2 prototype

**Architecture changes**
- Replaced full-index rebuild on upload with incremental `append_document_to_policy_index()` — only new document chunks are embedded
- Added per-program RAG query generation: each program now generates its own targeted retrieval query rather than using one shared query
- Added program selector UI in sidebar: users can scope which programs to evaluate
- Removed policy ingestion tab from UI (moved to backend-only capability)

**Bug fixes** (see `failure_log.md` for details)
- BUG-01: Clarification questions no longer shown as caveats
- BUG-02: Retrieval bonus double-count removed from priority score
- BUG-03: Program sort order now consistent with priority order
- BUG-04: Medicaid-specific query terms moved to Medicaid-only retrieval layer
- BUG-05: Upload now uses incremental indexing instead of full rebuild
- BUG-06: LIHWAP correctly distinguished from LIHEAP in program name detection
- BUG-07: Test cleanup fixture added to prevent cross-test contamination

**Evaluation improvements**
- Expanded from 3 programs to support uploaded custom programs
- 10-case evaluation set covering success, failure, and edge cases
- Cross-check disagreement now explicitly surfaced in output (`decision_status: ambiguous`)

### Known limitations in v1.0

- No county boundary enforcement (FAILURE-01)
- No explicit contradiction detection for conflicting structured inputs (FAILURE-02)
- Minimal fallback guidance when user withholds income information (FAILURE-03)
- Policy index covers SNAP, Medicaid/CHIP, and LIHEAP only — other PA programs not included
- Embeddings require OpenAI API key; local fallback uses hashed bag-of-words and is less accurate

### Planned improvements (not implemented)

- County validation in intake agent with explicit out-of-scope warning
- Contradiction detection between structured fields (e.g., employed + zero income)
- Richer fallback guidance for incomplete intake cases
- Expand policy corpus to include additional PA programs (TANF, WIC, General Assistance)
