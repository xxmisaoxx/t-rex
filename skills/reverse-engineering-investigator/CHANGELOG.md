# Changelog

## 3.2 — 2026-10-11
- Add an optional direct Ghidra adapter with doctor, analyze, cached function query and verified paginated evidence view.
- Bind runs to binary SHA-256, exporter/provider version, private program database fingerprint and exported file hashes.
- Export bounded JSONL inventories, instruction bytes, entry xrefs and per-function pseudocode with explicit truncation, timeout and missing-selector outcomes.
- Preserve canonical state schema 3.0 and all host layouts. No REA dependency or bundled MCP server.
- Add control-plane tests, real PE64/ELF headless tests and an Ubuntu/Windows integration workflow. Actual platform results are recorded separately.

## 3.1 — 2026-10-07
- Make coding-agent portability explicit, independently of analysis-provider portability.
- Add documented loading/invocation adapters for OpenCode, Claude Code, Codex CLI/IDE, Cursor, Antigravity 2.0/IDE, Antigravity CLI and Pi; include shared and generic explicit-loader layouts.
- Add a standard-library exporter that verifies source bytes and produces fresh project/user staging trees with a loader fragment and receipt, without modifying host settings or existing instructions.
- Define host handoff, relative path ownership, lazy capability mapping, optional tooling, job reconciliation and context measurement invalidation.
- Add reset-context with expected-revision/atomic checkpoint handling; preserve schema 3.0, artifact facts, evidence IDs and NEXT.
- Add packaging, cross-workspace state and fresh-agent continuation tests; keep actual installed-host lifecycle tests distinct.

## v2
- Converted the PE-focused skill into a routed multi-target RE framework.
- Added profiles for PE, ELF, Mach-O, .NET, JVM, Electron/JavaScript, packaged Python, Android, iOS, WebAssembly, and generic native artifacts.
- Added cross-layer tracing for IPC, JNI, P/Invoke, native addons, protocols, files, and service boundaries.
- Added x86-64/System V/Windows x64/AArch64 architecture notes.
- Added version/binary diff reasoning that separates layout drift from semantic change.
- Added provider-neutral tool selection and cross-provider verification rules.
- Strengthened evidence dependency, negative-claim boundaries, artifact freshness, and drift handling.
- Added behavioral eval prompts.
- Retained adaptive context management with no fixed 150k threshold; compaction uses active capacity, headroom, and projected next-operation cost.

## 2.1-audited — 2026-10-07
See V2.1-CHANGELOG.md for audit-linked correctness, ownership and efficiency fixes. Preserved v2 profiles and methodology; no major v3 architecture.

## 3.0 — 2026-10-07
- Canonical normalized JSON for revisions, questions, hypotheses, evidence dependencies, probe outcomes and exact NEXT; generated Markdown views.
- Typed schemas plus graph/lineage/NEXT integrity checks; optional active-byte verification.
- Optional dependency-free helper for view, budget, explicit invalidation, conservative revision transition and repeat-probe advisory.
- Expected-revision conflict detection, exclusive writer lock and atomic canonical replacement.
- Preserved audited v2.1 format/ABI/bridge reasoning; no universal detector/provider adapter.
- Twenty behavior fixtures, actual synthetic agent responses and deterministic helper tests; real OpenCode lifecycle/target tests remain separate.
