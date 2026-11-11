# Issues Solved - Q&A Summary

This file captures the issues solved during this session in question-and-answer format.

## 1) Database and Docker Operations

### Q: How do I connect to the Postgres DB running in Docker?
**A:** Used Docker-based connection flow and provided `psql` commands against the running container/service. Confirmed the right way to access DB from terminal in this project context.

### Q: How do I run a `SELECT` statement (for example from `alerts`) from command line while connecting to Docker?
**A:** Shared direct `psql` command patterns for one-off SQL execution and interactive shell mode so `SELECT * FROM alerts;` can be run safely.

### Q: How do I run eval all in PowerShell?
**A:** Confirmed command execution path and helped align the eval runner invocation for PowerShell + project environment.

## 2) RAG / Retrieval Logic Explanations

### Q: Explain cache service behavior.
**A:** Explained cache purpose and behavior around retrieval reuse, likely cache hits/misses, and where cost/time savings come from.

### Q: Explain embedding-indexing logic (`idx_in_misses`, `original_idx`).
**A:** Clarified that these indices map miss-only processing back to original request order, so results are reassembled correctly after partial cache misses.

### Q: What does `"doc": doc` mean vs `**doc`?
**A:** Explained that `"doc": doc` is a dictionary key-value assignment (`"doc"` key, `doc` variable value), while `**doc` is dictionary unpacking in Python (or bold markup in Markdown context).

### Q: What does `generate(system_prompt=..., user_message=...)["text"]` mean?
**A:** Explained it as: call a function with named args, expect a dict-like response, and extract the `text` field; also noted it can raise `KeyError` if `text` is absent.

## 3) Ingestion Pipeline and Document Processing Fixes

### Q: Why is ingestion failing repeatedly?
**A:** Diagnosed multiple root causes and implemented fixes:
- Fixed vector payload bug where invalid chunk field access caused `AttributeError`.
- Added robust fallback chunking for `.txt/.md/.html/.htm` in document processing.
- Improved ingestion diagnostics and reason bucketing in seed pipeline.

### Q: Why are there device errors like `AcceleratorDeviceNotAvailableError`?
**A:** Removed assumptions that required unavailable accelerator paths in this environment and made ingestion path more resilient for Windows/CPU flows.

### Q: Why are PDF files failing with Hugging Face errors (401/RepositoryNotFoundError)?
**A:** Verified HF auth/token issue was the blocker and provided token-refresh/test flow (`model_info` check) to restore PDF model access.

### Q: Why did Pydantic settings fail on unknown env keys?
**A:** Traced strict settings validation mismatch and aligned understanding around declared settings vs incoming env variables.

## 4) Streamlit and Runtime Compatibility

### Q: Why did Streamlit crash on `use_container_width`?
**A:** Identified version/API mismatch as the cause and explained compatibility direction for current installed Streamlit.

## 5) Disk Space Incident

### Q: Why did my disk become full?
**A:** Measured disk usage and identified Docker as the primary contributor (large reclaimable image/build cache footprint). Provided cleanup guidance and safe prune strategy.

## 6) Eval Runner and Service Import Breakages (Fixed)

### Q: `ImportError: cannot import name 'search' from app.services.vector_store`
**A:** Restored/normalized `search` support in vector store and added compatibility handling for Qdrant client API differences (`search` vs `query_points`). Also removed duplicate function definitions that were overriding correct behavior.

### Q: Why does `uv run python -m eval.run_ragas --profile naive` keep failing?
**A:** Fixed a chain of blockers end-to-end:
- Pinned eval-related dependencies for stable compatibility in dev extras.
- Hardened `eval/ragas_adapter.py` imports and result normalization.
- Fixed dataset field mapping expected by eval rows.
- Fixed `eval/run_ragas.py` control flow and added module entrypoint (`main()` execution).
- Fixed schema typing errors in `eval/schema.py` (Literal usage) and converted strict missing-feature stop into warning.
- Fixed `rag_service` call mismatches:
  - `build_spotlight_context(retrieved_chunks)` argument
  - `generate(..., user_prompt=...)` parameter name
- Fixed reporting key mismatch (`forbidden_check` expected by reporter).

### Q: Did the naive eval run successfully in the end?
**A:** Yes. The command completed, produced a full table, and wrote output under `eval/results/..._naive.json`.

## 7) Security/Operational Note

### Q: Any urgent security follow-up discovered?
**A:** Yes. Exposed/real-looking secrets were detected in env content shared during troubleshooting; recommendation was to rotate/revoke them immediately.

---

If needed, this file can be extended with a per-issue timeline (timestamp, file changed, command used, and validation result).
