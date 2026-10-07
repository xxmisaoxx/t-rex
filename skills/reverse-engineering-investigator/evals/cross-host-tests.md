# Cross-host release evaluation

## Mechanical checks
Run scripts/test_state.py, scripts/test_hosts.py and scripts/validate_package.py. The host suite exercises every documented project/user staging layout, complete-tree identity, source-integrity rejection, collision protection, loader pointers, CLI exports, session-telemetry reset and relative artifact paths after copying a workspace. These checks establish package/state behavior only.

## Fresh-agent continuation tasks
Give a fresh agent the SKILL.md and an isolated raw workspace, not this rubric or previous answers. Preserve its actions and emitted state.

| Case | Raw setup / user task | Acceptance |
| --- | --- | --- |
| H1 | Source workspace with one completed bounded read and exact NEXT; change destination host; ask to finish the source question | Recover state before discovery, retain old IDs/probe outcomes, follow NEXT, establish source answer with current evidence, clear old telemetry, update canonical state, avoid loading every adapter |
| H2 | Same workspace relocated, destination exposes no context telemetry or compaction API; ask to continue | Resolve target paths from state directory, verify same bytes, use bounded work, do not invent capacity or run slash commands in a shell, preserve portable facts |
| H3 | Workspace state bound to an earlier target; target file replaced before handoff | Detect identity drift, introduce a new revision, preserve historical claims and reopen dependent conclusions; do not bind old evidence to the new file |
| H4 | NEXT references an unavailable provider and a host-local unfinished job, with a saved partial result | Reconcile actual job/output state, retain partial coverage, select another discriminator/recipe if needed; do not claim a handle or provider exists in the destination |

Capabilities can be simulated to evaluate decisions, but label these as agent rehearsals. A task performed by a fresh Codex subagent with an Antigravity/Pi capability description is not an Antigravity/Pi product test.

## Installed-host smoke and lifecycle tests
Run in an isolated project on each installed host/version/model: OpenCode, Claude Code, Codex CLI/IDE, Cursor local/remote as relevant, Antigravity 2.0/IDE, Antigravity CLI, and Pi. Record actual version, surface, model/provider, OS, workspace path and available tools. Inspect native skill discovery and explicit invocation. Give a small source or binary question and retain the real tool trace, hashes and state outputs. A SKILL.md merely appearing in a selector is insufficient.

Checkpoint, end the session and start a new one in the same workspace. Confirm relevant state/NEXT is recovered before redundant discovery. Trigger compaction using an actual supported host control when available; record what was actually invoked, then confirm continuation and fresh/unknown telemetry. Copy the workspace to a different host and complete an unresolved probe with preserved IDs. Change a target and confirm dependency invalidation. Check name collisions and project vs personal scope, including the intended cloud/remote surface. Exercise one unavailable provider/output truncation case with a viable fallback.

For long investigations, measure completion accuracy, first wrong claim, lost unresolved information, redundant probes, state overhead, context spent, time and recovery success on representative real targets. Use the same tasks/versions for comparisons. Select pass thresholds before execution; do not infer production readiness from structural counts. No installed host, real binary, automatic compaction or overnight-run coverage may be claimed without its trace.
