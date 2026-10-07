# Evidence and canonical state — v3

## Ownership
`INVESTIGATION.json` owns objective, immutable artifact revisions, active revision IDs, profiles, questions/hypotheses, evidence claims/dependencies, compact probe records and exact NEXT. Target maps own layout conversions bound to one revision and refer to E-IDs; they do not repeat conclusions. Raw evidence under `evidence/<revision>/<run-or-probe>/` owns exact payloads. CURRENT-STATE and EVIDENCE-LEDGER are generated views; never edit a second copy of the same claim.

## Evidence semantics
- OBSERVED is the direct proposition exposed by a byte/source/metadata read or bounded runtime event. A tool report establishes what the provider reported, not automatically the program semantics it asserts.
- DERIVED is a deterministic result with dependencies and stated algorithm/preconditions.
- INFERRED is an interpretation with dependencies, alternatives and limits.
- UNKNOWN belongs to unanswered questions, not claim records.

Class, confidence and validity are independent. HIGH describes support for the exact proposition, MEDIUM a live alternative, LOW tentative reasoning. Validity is current, stale, historical or disputed. Do not automatically promote class/confidence or decay it with elapsed time. Runtime facts name artifact/load/run/input/environment/observation boundaries. One event is never universal execution coverage.

Every claim stores stable ID, artifact revisions, typed location, dependencies, class/confidence/validity, provider recipe, coverage, search boundary and limitations. Derived/inferred claims have observed/derived support paths; cycles and missing IDs are invalid. Partial/truncated/failed coverage cannot establish an exhaustive absence. A mechanical graph check does not establish whether a search method actually covered its claimed boundary.

## Validity and lineage
New evidence uses new IDs. Supersession links old IDs; no silent rewrite of the original proposition or rebinding to a different binary. `invalidate` marks explicit roots and dependent closure stale for active conclusions. `advance` binds new file bytes to a new revision, keeps old claims as historical, and makes dependent active conclusions stale. It conservatively requires revalidation of all old-revision claims; unrelated artifact facts remain current. Manual selective revalidation requires checking full dependencies, layout, callers, relocations, environment and search scope, not merely an unchanged local fingerprint.

Question status ANSWERED requires adequate current support for its scoped question; helper validation checks links/currentness, not truth. When support becomes stale/historical, affected answered questions become PARTIAL, evidence-backed supported/rejected hypotheses become UNTESTED, and obsolete NEXT is cleared. Select a new exact probe, preserving old probe outcomes.

## Checkpoints
Validate JSON and cross-record invariants before writing. Optional helper mutations take an expected checkpoint revision, use an exclusive writer lock and atomic same-directory replacement. Multi-writer conflicts fail rather than overwrite. A crash after rename can leave a stale lock; inspect/recover owner state explicitly before removing it. Maps/payloads should be durable before their references enter the snapshot. Generated view failure does not invalidate canonical JSON; regenerate it.

Read narrow views, active question and dependency slices during resume. Canonical JSON may grow over long investigations: compact view first, archive raw reports, and use offline slicing if the file exceeds a useful read budget. Do not load every historical claim at startup or automatically delete evidence. The current helper validates the whole JSON locally without injecting it into model context.
