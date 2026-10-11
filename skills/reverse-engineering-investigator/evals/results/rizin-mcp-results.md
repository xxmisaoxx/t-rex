# Rizin and MCP validation — v3.3

Date: 2026-10-11. This record covers the direct Rizin adapter and local stdio MCP server. Cutter is detected as a GUI; no Cutter GUI bridge is claimed.

## Local automated checks

Environment: Linux x86-64, Python 3.12, official Rizin 0.9.1 static archive and MCP Python SDK 2.3.0 in a dedicated virtual environment.

All 11 `test_rizin_mcp.py` cases passed with the real provider and SDK. They cover job persistence/restart, path and limit validation, process cancellation, explicit installation selection, project command quoting, PE machine bytes and address mapping, cached queries without reanalysis, target/project/output drift rejection, bounded coverage, an ELF caller fixture, and a real stdio client discovering seven tools, starting a job and reading evidence.

The existing 39 state and 20 host/packaging checks also passed. The Ghidra suite passed its 15 local control cases; three live Ghidra cases were skipped locally because Ghidra was absent. Dedicated CI runs the real Ghidra and Rizin/MCP suites on Ubuntu and Windows; consult the corresponding workflow results for their platform outcomes.

## Independent forward investigation

A fresh agent received the current skill and an unstripped 16,000-byte ELF x86-64 PIE, without its source or expected result. Target SHA-256: `b37925f09f9077db7e3c93b91c3d33068572e7d060463eff3b868c8c63ad8482`.

The agent used the local MCP server for provider operations, recovered the fee formula and three direct calls from `main`, and corroborated them with GNU disassembly, an independent ELF mapper and native probes. Its result matched the fixture source: zero when disabled; otherwise `17 * min_u32(amount, 45) + (amount <= 31 ? 900 : 800)`. It verified all 42 exported instruction byte mappings and 56 sampled native boundary cases. The unmodified program printed `1104 1565 0`.

The report kept observed byte/disassembly results separate from derived semantics and business interpretation. It preserved a canonical revision-2 checkpoint and completed a cached MCP function query after reconnecting. Root review independently reran `re_state.py validate --verify-files`: schema/graph and active file bytes passed.

One initial workspace client used SDK result attributes from an older interface; the agent corrected it to SDK 2.3.0 snake_case attributes. No skill/repository changes were needed for this investigation.

## Remaining scope

- The standalone Rizin runtime lacked rz-ghidra. Function details correctly reported partial coverage and unavailable pseudocode; plugin-backed decompilation has not been exercised by these tests.
- The native samples and caller audit are bounded, not universal input or runtime indirect-caller coverage.
- These tests verify stdio behavior with the official SDK, not discovery or lifecycle inside every supported coding agent.
- Cancellation/restart tests do not establish cleanup after an abrupt OS kill or multi-hour stability.
- GUI discovery does not verify installed editions, licenses or APIs for IDA, Binary Ninja, Cutter, x64dbg or ImHex.
