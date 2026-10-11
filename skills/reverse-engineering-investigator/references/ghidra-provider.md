# Ghidra provider

Contents: [Discover](#discover-and-install) · [Analyze](#analyze-and-narrow) ·
[Evidence contract](#evidence-contract-schema-10) · [Report](#turn-data-into-a-report-and-checkpoint) ·
[Other providers](#other-providers)

Use this adapter for native binaries when the next question needs functions, strings, symbols,
segments, instruction bytes, entry xrefs or pseudocode. Use an existing suitable provider when
available; prefer Ghidra for a new automated native workflow. No REA dependency is needed.

## Discover and install

Resolve `scripts/re_tools.py` from this installed skill directory. Use Python 3.10+ and a Ghidra
official release ZIP. The Java exporter uses Ghidra's Java API and bundled Gson; no pip package or
PyGhidra setup is required. Run:

```sh
python "<skill directory>/scripts/re_tools.py" doctor
python "<skill directory>/scripts/re_tools.py" doctor --ghidra-home "<Ghidra directory>" --java-home "<JDK directory>"
```

Discovery checks an explicit path, `GHIDRA_HOME`, the launcher on PATH, then shallow common tool
directories. A missing result means not found in those locations, not proof the tool is absent from
the machine. Ask for an installation path if the user already has Ghidra elsewhere. Discovery is
not a launch test (`launch_verified: false`). A successful analysis verifies the actual launcher.

If missing, present the [official releases](https://github.com/NationalSecurityAgency/ghidra/releases)
and that release's Getting Started guide. Download its release ZIP, extract into a new directory,
and use the JDK required by the installed release, not a fixed Java version. `doctor` reads its
`application.java.min`; a configured `JAVA_HOME_OVERRIDE` in Ghidra takes precedence. Pass explicit
paths or set `GHIDRA_HOME` and `JAVA_HOME`. Install using the host's normal authorized workflow.
The adapter itself does not install packages or change agent settings. A machine with an unsuitable
PATH Java may still have a compatible JDK elsewhere; supply `--java-home` instead of reinstalling.

## Analyze and narrow

Keep output in the target's investigation directory, outside the global skill. Use a fresh output
path for each run. Start with one named function if known; otherwise use the bounded sample and
inventory to select the next function:

```sh
python "<skill directory>/scripts/re_tools.py" analyze "<binary>" --output "<investigation>/analysis-01"
python "<skill directory>/scripts/re_tools.py" view --analysis "<investigation>/analysis-01" --kind functions --contains "retry" --limit 20
python "<skill directory>/scripts/re_tools.py" function --analysis "<investigation>/analysis-01" --function retry_delay_ms --output "<investigation>/function-01"
python "<skill directory>/scripts/re_tools.py" view --analysis "<investigation>/function-01" --kind details --limit 1
```

Pass `--ghidra-home` and `--java-home` to analyze/function if discovery needs them. Initial analysis
creates an isolated Ghidra project. `function` uses `-process -noanalysis -readOnly`, checks the
target and exported program SHA-256, and refuses a Ghidra version change. The manifest records the
private program database fingerprint; cached queries verify it before and after the run. A database
modified in the GUI requires a new analysis. Retain the original
project directory for later queries. Moving/deleting it requires a new analysis. Serialize access
to the same project; a locked project should be closed or queried later.

Use repeatable `--function NAME` or `--function 0xABSOLUTE_ADDRESS`. Names are exact and all matches
are considered; narrow an ambiguous name by its entry address. Numeric selectors are absolute
addresses in the program's default address space, not RVAs. The sample is the first discovered
non-external functions, not a relevance ranking.

Defaults: 5,000 inventory rows per collection; 10 detailed functions; 2,000 instructions and 1,000
incoming/outgoing references per function; 4,096 characters per string; 100,000 characters per
pseudocode; 30 seconds per decompile; 300 seconds for initial auto-analysis; 900 seconds for the
whole process. Override the corresponding `--max-*`, `--decompile-timeout`, `--analysis-timeout`
and `--timeout` options when the next probe requires it. JSONL is streamed to disk; read filtered
pages instead of placing every file in the chat. `view` paginates the exported rows; it cannot
recover rows omitted by an export cap. Increase the cap in a new analysis when needed.

On Windows, launch the official `.bat` through cmd with quoted arguments. Spaces and ampersands
are supported; paths/selectors containing `%`, `!`, `^`, quotes or newlines are rejected because
cmd may expand them. Use a workspace path without those characters.

## Evidence contract, schema 1.0

| File | Meaning |
| --- | --- |
| `manifest.json` | Run ID, target path/size/SHA-256, provider/version/exporter hash, command, limits, project pointer/fingerprint, result status and exported file hashes. |
| `metadata.json` | Ghidra program identity, format, language/compiler, image base, analysis timeout and collection counts/coverage. Written after the export finishes. |
| `functions.jsonl` | Discovered functions, entry address/RVA, names, signature, body size, external/thunk flags. |
| `strings.jsonl` | Defined string data from Ghidra's database, address, type and explicit text truncation. Not an exhaustive byte-level string search. |
| `symbols.jsonl` | Symbols with type, source and external flag. External symbols are not a complete import/export table. |
| `segments.jsonl` | Ghidra memory blocks and permissions. Their boundaries can differ from original file sections. |
| `details.jsonl` | Selected functions' bytes/disassembly, incoming entry references, outgoing instruction references, pseudocode and per-slice coverage/errors. |
| `request.json`, `headless.log`, `ghidra.log`, `script.log` | Exact request and retained execution diagnostics. |

Function-only runs export metadata/details and logs; obtain inventories from the original analysis.
Each observation has a run-local evidence ID and address space. Memory addresses use hex; stack
and other spaces retain Ghidra's typed address text. Interpret RVA only within the stated image
base/space. Static addresses are not runtime VAs unless the loaded module mapping is established.

`success` means the run completed and exported the declared scopes. `partial` means an analysis
timeout, a cap/truncation, missing selectors or a decompiler failure. `failed` includes launch
failure, missing export completion, process timeout or identity drift. Exit code is 0 for success
and partial, 1 for failed/unavailable; inspect JSON status rather than the exit code alone. Preserve
failed-run partial files/logs as diagnostics, not as a completed evidence bundle.

**Complete export coverage is not complete program understanding.** Xrefs come from the current
Ghidra database; absent indirect calls, undiscovered code and undefined strings remain possible.
Incoming references cover only the function entry. Pseudocode and inferred signatures are provider
reports. Validate important semantics against instruction bytes, ABI, caller context or another
provider. The adapter performs static analysis; it does not execute the target binary.

## Turn data into a report and checkpoint

Read manifest/metadata first, then only inventory pages and details implicated in the user's
question. Follow [reporting](reporting.md): short answer, evidence-linked findings, then investigation
files and continuation. Cite canonical E-IDs, the provider run/item ID, retained output file and
precise address/record for substantial findings. Separate observed bytes/tool output from derived
semantics and inferred intent. Bound absence claims to the actual search scope.

Save the report's supported claims and probe outcome in canonical investigation state using the
existing state workflow. Link raw evidence files and their hashes; do not paste the whole bundle
into `INVESTIGATION.json`. Recover prior state and cached project before starting another analysis
of unchanged input. These scripts export evidence; they do not automatically write claims or a
finished report. The optional [local MCP server](rizin-mcp.md) exposes these same adapters;
the agent still owns report synthesis and canonical state updates.

## Other providers

The bundled executable adapters support Ghidra and [Rizin](rizin-mcp.md). Cutter is detected as a
GUI; automation uses Rizin directly. Treat Hyperion as experimental. Use IDA and Binary
Ninja according to the installed edition's actual APIs/MCP capability. Use x64dbg for runtime
questions and ImHex for structured byte/pattern questions. Their adapters are planned; locating an
application or seeing a tool name does not establish a working integration.

API references: [HeadlessScript](https://ghidra.re/ghidra_docs/api/ghidra/app/util/headless/HeadlessScript.html),
[DecompInterface](https://ghidra.re/ghidra_docs/api/ghidra/app/decompiler/DecompInterface.html), and the
installed `support/analyzeHeadlessREADME.html`. Check versions before applying newer API examples.
