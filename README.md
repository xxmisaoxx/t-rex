![T-REX — Trace-driven Reverse Engineering eXplorer](assets/t-rex-banner.png)

# T-REX

*Follow the evidence. Uncover the logic.*

A portable reverse-engineering skill for OpenCode, Claude Code, Codex, Cursor, Antigravity, Pi and other coding agents. Release 3.1; canonical investigation schema 3.0.

This repository keeps one source package in [skills/reverse-engineering-investigator](skills/reverse-engineering-investigator). Its [SKILL.md](skills/reverse-engineering-investigator/SKILL.md) contains the shared workflow. Host adapters map installation and invocation; target profiles and analysis providers remain independent of the coding agent.

## Install from this repository

Copy the complete `skills/reverse-engineering-investigator` directory into your host's documented skill directory. Keep its directory name and relative resource tree. Choose one visible installation per host.

| Host | Project destination |
| --- | --- |
| OpenCode | `.opencode/skills/reverse-engineering-investigator/` |
| Claude Code | `.claude/skills/reverse-engineering-investigator/` |
| Codex | `.agents/skills/reverse-engineering-investigator/` |
| Cursor | `.cursor/skills/reverse-engineering-investigator/` |
| Antigravity IDE / CLI | `.agents/skills/reverse-engineering-investigator/` |
| Pi | `.agents/skills/reverse-engineering-investigator/` |

For shared-layout hosts, one `.agents/skills` copy can serve several compatible agents. For another host without native discovery, explicitly read SKILL.md through its instruction mechanism. The repository's `skills/` directory is a distribution location; cloning it alone does not install it in every host.

For personal paths, invocation commands, scope caveats and official sources, read the [skill README](skills/reverse-engineering-investigator/README.md) and [host registry](skills/reverse-engineering-investigator/hosts/registry.json).

Optional staging exporter (Python 3.10+, no third-party dependencies), run from this repository root:

```sh
python skills/reverse-engineering-investigator/scripts/export_host.py --host claude-code --out ../export-claude
python skills/reverse-engineering-investigator/scripts/export_host.py --host shared --out ../export-shared
```

The output contains the host-specific directory tree and an optional loader fragment. Copy the skill tree into your actual project/home root. The exporter verifies the source manifest and refuses existing output directories; it does not edit host settings or project policies.

## Continue an investigation

Keep project facts in an investigation workspace, outside this source repository and the installed skill. Recover canonical INVESTIGATION.json and relevant evidence/NEXT before new discovery. On a host/model/session switch, verify relevant artifact identity, clear stale context measurements and continue with the destination's actual tools. No fixed context limit, mandatory MCP, subagents or Python runtime is imposed on the methodology.

## Validate

Run from the repository root with Python 3.10+:

```sh
python skills/reverse-engineering-investigator/scripts/validate_package.py skills/reverse-engineering-investigator
python skills/reverse-engineering-investigator/scripts/test_state.py
python skills/reverse-engineering-investigator/scripts/test_hosts.py
```

Release checks: 39 state tests, 20 portability tests (17 host/scope layouts), and three fresh-agent source/state continuation cases passed. Installed-product discovery, automatic compaction and native session lifecycle were not run on the named hosts. See [validation results](skills/reverse-engineering-investigator/VALIDATION-RESULTS.md) and [cross-host evaluation](skills/reverse-engineering-investigator/evals/cross-host-tests.md).

See [PUBLISHING.md](PUBLISHING.md) for uploading these source files to your GitHub repository.

## License

Copyright (c) 2026 xxmisaoxx.

T-REX is licensed under the GNU General Public License, version 3 only
(`GPL-3.0-only`). See [LICENSE](LICENSE) for the complete terms.

You may use, modify and redistribute this project, including commercially,
under those terms. When conveying covered modified works, preserve the
required notices and provide the corresponding source under GPLv3.

This project is distributed without any warranty; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
