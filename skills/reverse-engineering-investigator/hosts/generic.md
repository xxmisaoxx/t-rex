# Generic and shared Agent Skills hosts

For a host documenting Agent Skills discovery, stage `shared` into `.agents/skills/reverse-engineering-investigator/` and verify that host reads this location. The shared layout is documented by OpenCode, Codex, Cursor, Pi and Antigravity; Claude Code's documented native layout is `.claude/skills/`.

For an unfamiliar agent without native discovery, stage `generic` into `skills/reverse-engineering-investigator/`. Explicitly ask it to read that SKILL.md, or merge the generated LOADER.fragment.md pointer into its supported instruction mechanism. Do not invent AGENTS.md, CLAUDE.md or another filename as a universal autoload feature. Keep the supporting tree together and resolve its paths from the actual skill directory.

Use [host-portability](../references/host-portability.md) for capability mapping and recovery. Host documentation and observed installed behavior decide commands, session recovery and context telemetry. No specific shell, provider, hook or agent orchestration API is required.
