# Investigation Strategy

## One question, one hypothesis cluster
Group probes around a concrete question: provenance, dispatch, serialization, initialization, or behavior difference. Do not batch unrelated exploration.

## Information-gain heuristic
Prefer probes that eliminate several hypotheses, confirm artifact freshness, find a unique provenance source, convert inference into direct evidence, resolve identity, or bridge application layers. Avoid large low-discrimination output.

## Escalation ladder
1. artifact metadata
2. exact string/name/symbol lookup
3. local code/data slice
4. xrefs/callers/callees
5. CFG/reaching definitions/object provenance
6. initialization/registration paths
7. cross-module/cross-layer tracing
8. runtime observation
9. controlled comparison/version diff

Stop when the question is sufficiently answered.

## Hypothesis table
Track hypothesis, supporting evidence, contradicting evidence, status, and next discriminator. Status: ACTIVE, SUPPORTED, REJECTED, UNTESTED. Preserve rejected hypotheses and why they failed.

## Negative claims
Negative claims require bounded searches. Prefer "No direct xref found within X using Y" over "This never happens" unless exhaustive coverage is established.

## Scheduling without ceremony
The escalation ladder is a menu: start at an already known sink/bridge rather than repeating metadata and strings. Estimate gain qualitatively (which alternatives can this distinguish?) and cost (latency, output, setup). Numerical entropy scores are unnecessary. End a probe with changed evidence, a narrowed boundary or a recorded failure and concrete alternative. An answered question ends its work; a saturated question does not end an overnight task if another viable question exists.
