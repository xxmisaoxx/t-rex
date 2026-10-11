# Rizin, Cutter and local MCP

## Contents
- [Choose and discover](#choose-and-discover)
- [CLI evidence](#cli-evidence)
- [Connect MCP](#connect-mcp)
- [Jobs and continuation](#jobs-and-continuation)
- [Coverage and reporting](#coverage-and-reporting)

## Choose and discover

Keep Ghidra as the default native adapter. Use Rizin for an available lightweight CLI, an independent disassembly/xref check, or a Cutter-based setup that exposes the CLI. Cutter is a GUI powered by Rizin; detecting Cutter does not establish an installed `rizin` executable, decompiler plugin or live connection to an open Cutter project.

Resolve bundled scripts from the installed skill directory. From a repository checkout:

```sh
python skills/reverse-engineering-investigator/scripts/re_tools.py doctor --provider all
python skills/reverse-engineering-investigator/scripts/re_tools.py doctor --provider rizin --rizin-path "<rizin executable or directory>"
```

Use `RIZIN_PATH` or `RIZIN_HOME` for Rizin. Discovery checks PATH and shallow common installation folders. GUI discovery also checks `<TOOL>_HOME`: `CUTTER_HOME`, `IDA_HOME`, `BINARY_NINJA_HOME`, `X64DBG_HOME`, `IMHEX_HOME`. `not_detected` means absent from those search locations, not absent from the entire machine. Supply unusual locations explicitly. GUI records include official install links and mark editions/APIs unverified; no executable adapters for IDA, Binary Ninja, x64dbg or ImHex are bundled here.

If Rizin is missing, offer the [official CLI releases](https://github.com/rizinorg/rizin/releases). If the user wants an interactive workspace, offer [Cutter releases](https://github.com/rizinorg/cutter/releases). Check local tools first; install only what the next task requires. `doctor` does not download or configure software.

## CLI evidence

```sh
python skills/reverse-engineering-investigator/scripts/re_tools.py analyze "<binary>" --provider rizin --output "./investigation/rizin-01"
python skills/reverse-engineering-investigator/scripts/re_tools.py view --analysis "./investigation/rizin-01" --kind functions --contains retry --limit 20
python skills/reverse-engineering-investigator/scripts/re_tools.py function --analysis "./investigation/rizin-01" --function "<exact exported name or 0x entry VA>" --output "./investigation/function-01"
```

Infer the provider from saved analysis for `function`. Rizin names may include `dbg.` or `sym.`; use the exact name from the inventory or the numeric entry address. Resolve selectors against database functions in Python, never interpolate names into Rizin commands. A `0x` selector is an absolute analysis VA, not an RVA or file offset.

Use the same bounded options as Ghidra: `--max-items`, `--max-functions`, `--max-instructions`, `--max-refs`, `--max-text-chars`, `--max-pseudocode-chars`, `--analysis-timeout`, `--decompile-timeout`, `--timeout`. The default detail sample is 10 functions. Each Rizin response has a 16 MiB ceiling; a larger response fails explicitly and retains earlier slices. Inventory caps bound exported records; they do not make the initial database enumeration free.

Analyze with a fresh process and `aaa`; disable user startup scripts, open the target read-only and never execute it. Retain the private `project.rzdb`, raw provider responses and exact command log. Cached queries load a copy of the verified project on the current target with `Poo`, without repeating `aaa` or saving over the source project. Verify binary SHA-256, provider version/executable hash and project hash before reuse. Keep project access serialized.

The shared evidence envelope is schema 1.0: manifest, metadata, functions/strings/symbols/segments/details JSONL. Rizin `segments` rows describe binary sections and state this explicitly. Unresolved symbols can have a null address; do not invent address 0. Raw responses remain under `raw/`, with hashes in the manifest and command log. `view` verifies the selected JSONL file and returns page boundaries and analysis status.

## Connect MCP

MCP is optional; CLI/state scripts use Python's standard library. The stdio server uses the official MCP Python SDK, pinned in `scripts/requirements-mcp.txt`. Install it into a dedicated Python 3.10+ environment:

```sh
python -m venv .venv-trex
# POSIX:
.venv-trex/bin/python -m pip install -r "<skill-dir>/scripts/requirements-mcp.txt"
# Windows:
.venv-trex\Scripts\python.exe -m pip install -r "<skill-dir>\scripts\requirements-mcp.txt"
```

Configure your host's local stdio MCP launcher with:

```json
{
  "command": "<absolute path to venv Python>",
  "args": [
    "<absolute skill-dir>/scripts/re_mcp.py",
    "--workspace", "<absolute investigation workspace>",
    "--rizin-path", "<absolute Rizin executable>"
  ]
}
```

For Ghidra, add `--ghidra-home` and `--java-home`, or use the corresponding environment variables. Use the host's documented wrapper around this launcher object; MCP configuration containers differ between hosts. The server does not edit host settings. The workspace must exist and contain the investigation's targets and evidence. Installation locations can be outside it. Tools resolve workspace-relative paths and stay inside that workspace, including saved artifact/project paths.

The server exposes seven tools:

| Tool | Purpose |
|---|---|
| `doctor` | Check providers and shallow GUI discovery; return install guidance. |
| `analyze` | Start a bounded binary-analysis job and return its ID immediately. |
| `function` | Start a query from saved analysis, inferring its provider. |
| `job_status` | Read durable status, error and evidence location. |
| `cancel_job` | Request cancellation and retain existing output. |
| `list_jobs` | List up to 50 stored job records. |
| `view` | Read filtered, paginated, hash-verified evidence. |

For example, call `analyze` with `{"target":"target.exe","provider":"rizin","functions":["0x140001000"],"limits":{"max_functions":1,"timeout":300}}`, then poll `job_status` using the returned `job_id`. Once status is `success` or `partial`, call `view` with the returned output path and `kind:"details"`. Read capabilities, unresolved selectors and coverage before drawing conclusions. MCP pages are limited to 100 rows and 512 KiB; smaller pages or analysis bounds resolve oversized results.

## Jobs and continuation

Jobs persist inside the workspace's `.trex-jobs` directory. Serialize provider operations and accept at most eight unfinished jobs. The MCP request returns before analysis finishes; a client-side request timeout therefore does not require restarting analysis. Recover `list_jobs` and `job_status` first.

`cancel_job` first returns `cancelling`; poll for the terminal `cancelled` state. It signals the adapter, terminates the provider process and retains whatever was already written. Normal stdio shutdown and SIGTERM cancel owned work. An abrupt OS kill/power failure cannot guarantee cleanup; inspect retained manifests and the OS process list before launching a replacement. On server restart, unfinished records become `interrupted`; the server never adopts an unverified PID or silently reruns work.

A job record is an execution receipt, not canonical investigation state. Attach run IDs, file hashes and decisive slices to `INVESTIGATION.json`; retain the question, claims and NEXT there. A host/session change preserves evidence but invalidates runtime-local context telemetry and active job ownership.

## Coverage and reporting

Rizin's standalone release may lack `rz-ghidra`. Probe the actually installed plugin; set `decompile_status: unavailable` and capability `decompilation: false` when absent. Details remain partial, while disassembly/xrefs can still answer a bounded question. Do not substitute assembly text for pseudocode or describe an unsupported plugin as working. Plugin-enabled decompilation still needs independent validation; the shipped tests cover the standalone release without that plugin.

Bind addresses to the provider's analysis image base. Export instruction bytes and mapped file offsets; verify bytes against the current target. A byte mismatch or unmapped instruction keeps coverage partial. Incoming xrefs cover function entry only; outgoing xrefs cover instructions returned in the provider's function body. Complete export coverage never proves exhaustive discovery or complete runtime callers.

Write the report from the exported data and independent discriminators using [reporting](reporting.md): short answer, evidence-linked findings, then investigation files and continuation. Connect canonical E-IDs to the provider run/item IDs, artifact revision and exact retained file records. Distinguish the provider's claims from observed bytes and derived semantics. Preserve useful partial results, explain the capability gap, and switch to Ghidra or an available decompiler when pseudocode is actually needed.

Primary references: [Rizin JSON/analysis commands](https://book.rizin.re/src/analysis/code_analysis.html), [Rizin pipe API](https://github.com/rizinorg/rz-pipe), [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), [MCP lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle).
