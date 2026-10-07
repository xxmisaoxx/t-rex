# v3.1 fresh-agent continuation results — 2026-10-07

Three independent fresh Codex agents received the final workflow and isolated source/state directories. Their user tasks requested continuation after changing hosts with explicit destination capability descriptions. No acceptance rubric, expected integer or diagnosis was included. The named destinations describe simulated capability setups; these were not Claude Code, Cursor or Pi product runs.

| Case | Agent output | Verified saved behavior |
| --- | --- | --- |
| continue (Claude Code to fresh Codex session description) | sink receives 35; E1 seed=11, E2 produce arithmetic, E3 derived argument | Checkpoint 10, R1 retained, E1/P1 preserved, bounded NEXT source body inspected, Q1 answered, NEXT null, telemetry cleared, canonical/active bytes/payloads valid |
| drift (OpenCode to Cursor-style session description) | current sink receives 44; E3 seed=13, E4 current body, E5 derived argument | Same-size replacement detected by SHA-256; R2 introduced, R1 E1/E2 historical, new evidence supports answer, checkpoint 9, telemetry cleared, canonical/active bytes/payloads valid |
| fallback (OpenCode to Pi capability description) | sink receives 50; E1 seed=17, E2 body, E3 derived argument | Missing Ghidra/provider and old job handle recorded; source fallback used, checkpoint 10, R1 E1/P1 preserved, Q1 answered, NEXT null, telemetry cleared, canonical/active bytes/payloads valid |

The drift agent also noted that the old derived claim's metadata did not establish the claimed complete produce coverage and did not reuse it as current support. That fixture is deliberately not evidence of a previous host having run a correct analysis.

After the agents finished, an independent C harness compiled each current source and printed its actual sink argument. Outputs were 35, 44 and 50. This is an answer oracle for these tiny source cases, not a test of agent reasoning over the generated binaries. Parent verification also checked graph/schema validity, current file hashes, payload paths, original IDs/probes and context reset.

Task inputs were the SKILL.md and the case workspace. Continue asked to resume the source-level question with files/commands and unknown context/compaction. Drift asked to check the current source question in the moved workspace without disclosing the replacement. Fallback asked to continue with files/commands but no Ghidra, previous-host job control, telemetry or compaction API. The release review archive includes saved source/evidence/state workspaces and the machine-readable acceptance checks. These reports summarize agent responses and saved artifacts, not full tool-call transcripts.
