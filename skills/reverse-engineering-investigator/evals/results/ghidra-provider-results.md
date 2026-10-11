# Ghidra provider validation — v3.2

Recorded 2026-10-11. These results cover the direct Ghidra adapter, separately from the historical v3.1 state and host evaluations.

## Reproduce

Use Python 3.10+ and an official Ghidra installation with its required JDK. Set `GHIDRA_HOME` and `JAVA_HOME`, then run from the repository root:

```sh
python skills/reverse-engineering-investigator/scripts/test_tools.py -v
python skills/reverse-engineering-investigator/scripts/test_state.py
python skills/reverse-engineering-investigator/scripts/test_hosts.py
python skills/reverse-engineering-investigator/scripts/validate_package.py
```

Without `GHIDRA_HOME`, the three real-provider cases are skipped. The remaining tests use simulated provider responses and do not establish disassembly accuracy.

## Local results

Environment: Linux x86-64, Ghidra 12.1.4, Temurin JDK 21.0.12.1+1. The Ghidra release archive matched SHA-256 `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db` from the official release asset.

| Check | Result and scope |
|---|---|
| Adapter control plane | 15 tests passed: discovery, JDK checks, launch arguments, timeout termination, output preservation, target/project/export identity, partial results and verified pagination. |
| Real PE64 | Passed: constructed return-42 executable, instruction bytes and addresses, decompilation, cached read-only query and missing-selector handling. |
| Real ELF with symbols | Passed: compiled retry-policy fixture, arithmetic and call references, cached query and explicit instruction/reference/pseudocode caps. |
| Optimized stripped ELF | Passed: optimized fixture, entrypoint query, decompilation and inventory/string caps. |
| Canonical state | 39 tests passed. Schema 3.0 retained. |
| Host packaging | 20 tests passed, covering existing supported layouts. |
| Structural validation | Manifest bytes, local links, templates and core instruction budget passed. |

The real cases invoke Ghidra headlessly. They import and analyze target binaries; the adapter does not execute the targets. Temporary integration-test projects are removed after each test.

## Fresh-agent investigation

A fresh agent received the installed skill instructions and an executable, with no expected answer or fixture source supplied. It used the adapter, cached queries, `readelf` and `objdump`, then wrote a report and canonical checkpoint.

- Target: 17,480-byte x86-64 ELF, SHA-256 `7f9f91738b1986f15b36033389d2cf7832d29da730fa44c498b313cab36757b9`.
- Initial analysis run: `27a66140b34448108d2656b177d14ff2`; cached query: `9954d34e72554da582dc483542a8ebd2`. Both succeeded with the same private database fingerprint.
- Recovered behavior: disabled returns 0; otherwise `min(250 + 150 * min_unsigned(attempt, 6), 1000)`.
- Identified four direct callsites in `main`, and distinguished two unwind-data references from callers.
- Independently checked 72 instruction byte slices against the current binary and distinguished Ghidra analysis addresses from ELF addresses and file offsets.
- An additional run of this self-built fixture produced `250 1000 1000 0` and exit code 0. This observes four built-in inputs, not every boundary value or a runtime instruction trace.
- The checkpoint passed schema/graph validation with current artifact hashes verified. It retained unresolved runtime checks and an exact continuation step.

The agent did not accept Ghidra's inferred `__stdcall` label as ABI proof; it checked the actual System V register usage. This illustrates why exported pseudocode remains provider evidence for an agent to assess.

## Remaining scope

The Ubuntu/Windows workflow runs the actual provider. Windows runs the real PE64 case; the two Unix compiler fixtures are skipped there. Local Windows execution was not performed. Consult the workflow result for platform validation.

These fixtures do not establish accuracy for arbitrary binaries, obfuscation, all architectures, Mach-O, large programs or multi-hour stability. Complete export coverage means complete within the current Ghidra database and requested bounds, not exhaustive discovery of program behavior. Dedicated CFG/import/export tables, other provider adapters and an MCP server are not included in v3.2.
