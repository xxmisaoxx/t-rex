# Optional state helper

Use Python 3.10+; no third-party dependencies. This helper manages state only, never the target or RE provider. Relative artifact paths are resolved from the state file's parent. Reproduction payload/map paths are workspace-relative; schema shapes and graph checks do not prove payload files exist unless inspected separately.

Commands:
```sh
python scripts/re_state.py validate INVESTIGATION.json --verify-files
python scripts/re_state.py view INVESTIGATION.json --out CURRENT-STATE.md
python scripts/re_state.py view INVESTIGATION.json --ledger-out EVIDENCE-LEDGER.md
python scripts/re_state.py budget --capacity 1000000 --used 780000 --next-cost 12000 --future 25000 --margin 20000 --durable
python scripts/re_state.py invalidate INVESTIGATION.json E1 --expected-revision 12
python scripts/re_state.py advance INVESTIGATION.json R1 R2 --expected-revision 12 --reason patch
python scripts/re_state.py reset-context INVESTIGATION.json --expected-revision 12
python scripts/re_state.py loops INVESTIGATION.json
```

`validate` checks schema vocabulary, IDs, graph cycles, revision lineage, active/current dependencies and NEXT/question binding. --verify-files hashes active artifact bytes; invoke at recovery/change boundaries rather than every probe. It does not verify runtime mappings or execute provider recipes.

`view` defaults to a compact continuation: active revisions, profiles, up to five unresolved questions, active evidence IDs, exact NEXT and workflow caveats. Ledger output is an optional full generated view for offline review. Neither view is canonical. Profile/ref loading remains conditional.

`budget` uses C-U versus N+F+M. Unknown input => bounded work/checkpoint policy, never invented telemetry. If shortage and not durable => checkpoint first; durable shortage => reduce planned output or seek host compaction. It does not call a compaction API.

`reset-context` clears capacity, usage and projected-operation estimates and marks telemetry noncurrent after a host, model or session switch. It preserves artifact revisions, evidence, questions, probes and NEXT. The validated atomic checkpoint becomes durable and increments its revision; a stale expected revision or active writer lock aborts as for other mutations.

`invalidate` computes transitive dependency closure. `advance` hashes the current bytes at old revision's path (which may now contain a replacement), creates a new immutable record with lineage, switches active IDs and conservatively revalidates old-revision evidence. It does not patch bytes or infer change ranges. Add exact changed ranges/mapping changes only when established. All writes validate and increment checkpoint revision; expected revision mismatches or writer locks abort.

`loops` flags comparable probe signatures with two no-novelty outcomes; use it as advice to change discriminator/question. A signature includes artifact revision, question, capability and normalized operation scope/parameters. New artifact/input/coverage/decoder changes warrant a different signature or explicit retry condition. It is not an autonomous watchdog process and does not stop the run.

External JSON Schema engines can check the published Draft 2020-12 documents. Bundled schema_check implements only $ref, type, properties, required, additionalProperties, items, enum, const, minimum, minLength, pattern, minItems and uniqueItems plus annotations/$defs. Unsupported validation keywords fail closed; it is not a general standards validator.
