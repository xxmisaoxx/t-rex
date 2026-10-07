# Reverse Engineering Investigator v3.1

One reverse-engineering core for OpenCode, Claude Code, Codex, Cursor, Antigravity, Pi and other coding agents. Keep provider-neutral native/managed/mixed-target reasoning, evidence dependencies, exact continuation and adaptive context headroom. Host adapters describe loading and invocation; the investigation remains independent of host chat history. All workflow instructions are in English.

## Install externally
Keep SKILL.md and its relative resource tree together under `reverse-engineering-investigator`. Install one visible version. Choose a documented layout below; `NAME` means `reverse-engineering-investigator`.

| Export host ID | Project skill directory | Personal skill directory |
| --- | --- | --- |
| `opencode` | `.opencode/skills/NAME/` | `~/.config/opencode/skills/NAME/` |
| `claude-code` | `.claude/skills/NAME/` | `~/.claude/skills/NAME/` |
| `codex` | `.agents/skills/NAME/` | `~/.agents/skills/NAME/` |
| `cursor` | `.cursor/skills/NAME/` | `~/.cursor/skills/NAME/` |
| `antigravity` (2.0 / IDE) | `.agents/skills/NAME/` | `~/.gemini/config/skills/NAME/` |
| `antigravity-cli` | `.agents/skills/NAME/` | `~/.gemini/antigravity-cli/skills/NAME/` |
| `pi` | `.agents/skills/NAME/` | `~/.agents/skills/NAME/` |
| `shared` | `.agents/skills/NAME/` | `~/.agents/skills/NAME/` |
| `generic` | `skills/NAME/` + explicit read | No automatic user discovery |

The shared layout is documented for OpenCode, Codex, Cursor, Antigravity and Pi. Use the Claude Code export separately. Native paths, invocation, scope caveats and dated official sources are in [hosts/registry.json](hosts/registry.json) and the adapter linked from SKILL.md. Local personal skills are not automatically present on every cloud/remote worker; put project skills in the workspace used there. A generic loader requires a host-supported instruction mechanism or explicit file read.

Optional exporter (Python 3.10+, standard library):

```sh
python scripts/export_host.py --host claude-code --out ./export-claude
python scripts/export_host.py --host codex --out ./export-codex
python scripts/export_host.py --host pi --scope user --out ./export-pi-home
```

Each output is a fresh staging tree representing a project root (or home root for `--scope user`), with the complete unchanged skill, an EXPORT.json receipt and a thin optional LOADER.fragment.md. Copy the skill tree into the corresponding root on the destination machine. Verify discovery and invocation there. The exporter refuses existing output paths and source overlap, verifies source hashes, and does not change actual home directories, project instruction files, settings, hooks or permissions. Python is optional for installation: copy the package manually using the table.

## Start and resume
Keep objective/target state in each investigation workspace, outside the installed skill. Recover existing state before discovery. For a new investigation, copy templates/INVESTIGATION.json and populate actual revision IDs, the question and exact NEXT as evidence is established. The empty template is a valid envelope, not an initialized investigation. Load only relevant profiles/references and the matching host adapter when needed.

INVESTIGATION.json owns claims; CURRENT-STATE and EVIDENCE-LEDGER are generated views. Raw evidence/maps remain external. Resolve bundled resources from the skill directory and target/state paths from the investigation directory. On a host/model/session switch, recover canonical evidence/NEXT, verify relevant artifact identity, and clear stale context measurements. A host switch alone does not invalidate artifact facts. See [host-portability](references/host-portability.md).

The optional dependency-free Python helper manages state mechanics only. It does not establish binary semantics, discover providers or invoke host compaction. No MCP implementation, particular analysis provider, subagents, hooks, fixed context limit or automated host configuration is required.

## Validate
```sh
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_package.py .
PYTHONDONTWRITEBYTECODE=1 python scripts/test_state.py
PYTHONDONTWRITEBYTECODE=1 python scripts/test_hosts.py
python scripts/re_state.py validate templates/INVESTIGATION.json
```

Canonical schema remains 3.0; valid v3.0 states need no migration. Read MIGRATION.md for older state. See [cross-host evals](evals/cross-host-tests.md) and VALIDATION-RESULTS.md for mechanical, behavioral and installed-host test boundaries. Historical v3.0 results remain dated; they are not renamed as successful product runs. Review/audit/changelog/eval files are release material, not startup instructions.
