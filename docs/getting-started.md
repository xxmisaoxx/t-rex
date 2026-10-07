# Getting started

## Install with Skills CLI

Run the following from the project where your agent will work:

```sh
npx skills add xxmisaoxx/t-rex --skill reverse-engineering-investigator
```

This route requires Node.js, npm and Git. The CLI discovers the skill inside the repository and handles supported agent destinations. It may select a detected agent automatically or ask you to choose. Review the installation summary for the destination.

To select an agent and use copies instead of symlinks:

```sh
npx skills add xxmisaoxx/t-rex --skill reverse-engineering-investigator --agent claude-code --copy
```

Other agent IDs include `opencode`, `codex`, `cursor`, `antigravity` and `pi`; the [CLI's supported-agent list](https://github.com/vercel-labs/skills#supported-agents) is authoritative for its current integrations. Add `--global` for a user-wide installation. Use one visible version per host.

To check repository discovery without installing:

```sh
npx skills add xxmisaoxx/t-rex --list
```

The result should list `reverse-engineering-investigator`. This discovery command was checked against the public repository on 2026-10-07; discovery is separate from actual invocation inside each product.

## Install manually

Clone the repository or download its ZIP from GitHub's Code menu. Copy the complete `skills/reverse-engineering-investigator` folder, including references, profiles, schemas, templates and scripts. Copying only `SKILL.md` breaks its relative links.

| Host | Project destination |
| --- | --- |
| OpenCode | `.opencode/skills/reverse-engineering-investigator/` |
| Claude Code | `.claude/skills/reverse-engineering-investigator/` |
| Codex | `.agents/skills/reverse-engineering-investigator/` |
| Cursor | `.cursor/skills/reverse-engineering-investigator/` |
| Antigravity IDE / CLI | `.agents/skills/reverse-engineering-investigator/` |
| Pi | `.agents/skills/reverse-engineering-investigator/` |

For personal destinations, invocation and scope details, read the [host adapters](../skills/reverse-engineering-investigator/hosts/registry.json) and [package guide](../skills/reverse-engineering-investigator/README.md). Project skills must be present in the workspace used by a remote worker.

## Make the first question concrete

Give your agent a target path and one question. For example:

```text
Use the reverse-engineering-investigator skill to inspect ./app.
Trace where the retry delay is calculated and which inputs change it.
Keep observations separate from deductions. Save the evidence and exact next
step in ./investigation-retry so another session can continue.
```

T-REX is the repository name; the skill is named `reverse-engineering-investigator`. If your host does not discover it, ask the agent to read the installed `SKILL.md` explicitly. Check its response for the target identity, active question, evidence and next step.

Keep investigation files in your project workspace, outside the installed skill directory. For source-level practice, use the [retry-policy example](../examples/retry-policy/README.md).

## Resume

Point the new session at the same investigation workspace:

```text
Use the reverse-engineering-investigator skill to continue ./investigation-retry.
Recover CURRENT-STATE.md and the relevant INVESTIGATION.json evidence.
Verify the relevant target identity and execute the saved NEXT.
```

If you change hosts, copy the target, raw evidence and investigation state together. Old host session IDs, job handles and token measurements do not transfer; the destination uses its own capabilities.

## Troubleshooting

- Skill not found: check the destination and installed skill name; explicitly read its SKILL.md.
- Missing references: reinstall the complete directory tree.
- Several copies load: keep one visible installation for that host.
- Helper cannot run: its scripts require Python 3.10+; the investigation workflow can still use other tools.
- Binary analysis unavailable: provide an installed analysis tool or accessible source. The profiles are guidance, not bundled decompilers.
- Windows symlink trouble: use the CLI's `--copy` option or manual copying.

For a useful bug report, include your host/version, installation method, expected behavior and a small reproducible example. [Open an issue](https://github.com/xxmisaoxx/t-rex/issues/new/choose).
