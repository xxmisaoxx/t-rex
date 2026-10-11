# Reports from evidence

Use three layers for a substantive report. Scale them to the question; a small answer can fit in a few paragraphs. Use [REPORT.md](../templates/REPORT.md) as a shape, not a mandatory form. Keep routine progress updates to the changed finding, support, uncertainty and NEXT.

## 1. Short answer

Lead with the answer to the user's question and its practical meaning. Name the investigated target/revision and the scope: source, static binary, observed runtime or a combination. State the main unresolved point or coverage limit. Describe a result as verified only within the checks actually performed. Keep broad stack/function inventories in artifacts unless they answer the question.

## 2. Findings with evidence

For each important conclusion, give its canonical E-ID(s), classification and a precise evidence locator. Identify the artifact revision and source lines, typed address, raw byte range, metadata key or recorded event/input. Link the retained file and identify a row/record or provider run/item ID when relevant; a path to a huge bundle alone is insufficient.

Explain the short reasoning step from evidence to conclusion. Treat provider output as an observation of what the provider reported; establish machine/source semantics separately. Use OBSERVED, DERIVED and INFERRED according to [evidence-state](evidence-state.md). Keep unanswered questions UNKNOWN rather than inventing claim records. Keep provider item IDs distinct from canonical E-IDs and connect them through the saved recipe.

Mention confidence or validity when it affects interpretation, and name material alternatives or limitations nearby. Bound negative statements to the exact search scope. A complete export does not establish complete program behavior. Cite only evidence already retained and inspected; a missing payload or locator is a gap to resolve or disclose.

Include only the decisive snippet, bytes, formula or call path in the report. Link longer disassembly, JSONL, tool logs and maps for inspection. Use tables for parallel findings; use prose when a causal argument needs explanation.

## 3. Investigation files and continuation

Before a completion/handoff report, save changed supported claims, probe outcomes, unresolved questions and NEXT in canonical `INVESTIGATION.json` using the existing checkpoint workflow. Reuse unchanged state. Write raw payloads before recording their references, and regenerate continuation/ledger views as needed. Treat the report as a snapshot of that checkpoint; it does not become another owner of claims.

List only useful files that actually exist: the canonical checkpoint, available generated views, target maps, selected evidence and provider manifests/logs. Give paths relative to the investigation workspace in durable reports; use the host's supported clickable links when presenting them. Name target revision/hash and relevant run identity once in this layer rather than repeating full hashes for every finding. Record enough provenance to reproduce the supporting operation.

State the checkpoint revision, unresolved question and exact next operation with its discriminator. If all in-scope questions are answered, say so and leave NEXT null; optional follow-up ideas are not active tasks. If work stopped on a failed or partial probe, link retained diagnostics and distinguish them from usable analysis evidence. If saving or validation failed, report that accurately; do not present a planned checkpoint as saved.

For build comparisons, apply the same layers with [DIFF-REPORT.md](../templates/DIFF-REPORT.md); keep both revision identities, address-domain normalization and claims needing revalidation explicit. On resume, recover canonical state and verify implicated artifacts before treating this report snapshot as current.
