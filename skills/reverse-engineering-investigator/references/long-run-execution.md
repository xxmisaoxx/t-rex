# Long-Run Autonomous Execution

Long-running work must accumulate knowledge, not activity. Each substantial operation should answer a question, eliminate a hypothesis, reduce ambiguity, establish durable evidence, or unlock a better probe.

## Resume protocol
1. read durable state;
2. verify artifact identity;
3. verify selected profiles;
4. pick the highest-priority unresolved question;
5. continue from its exact next probe.

Do not restart broad reconnaissance unless drift invalidated prior work.

Schedule probes by approximate `expected_information_gain / cost`. Favor a decisive write-xref, unique caller slice, byte freshness check, or discriminating runtime observation over repeated dumps or broad decompilation.

Perform stronger drift checks after patching, rebuilding, replacing binaries, switching branches/workspaces, restoring backups, long interruptions, or conflicting tool output.

Change direction when repeated probes add no evidence, the search boundary is exhausted, the question is sufficiently answered, or another unresolved question has greater expected value. Record why.

When one tool fails, preserve state and use an alternate representation/provider when possible. Do not spend an unlimited session repairing analysis tooling unless that is the requested blocker.

## Recoverable probe outcomes
Store a compact probe signature: artifact revision + question + capability + normalized scope/parameters. Record outcome, novelty and retry condition. Repeat an unchanged probe only for an explicit changed condition (input, version, coverage, decoder or hypothesis). After two comparable no-novelty probes, inspect saturation and change the discriminator or question; this is a strategy heuristic, not a stop timer. Failed tools do not count as evidence against the target hypothesis.

Checkpoint before mutation or an operation likely to lose process/session state. On a model switch invalidate old context telemetry, retain project IDs/evidence and recover the exact probe. On prompt re-paste reuse the objective unless scope changes. On partial checkpoint failure preserve linked records and reconcile them before advancing NEXT.
