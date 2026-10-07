# Pi adapter

Project: `.agents/skills/reverse-engineering-investigator/SKILL.md`.
Personal: `~/.agents/skills/reverse-engineering-investigator/SKILL.md`.

Use /skill:reverse-engineering-investigator followed by the task. Inspect startup diagnostics; /reload refreshes skills after editing in an active session.

This adapter uses Pi's documented shared Agent Skills locations. Preserve the directory form and relative supporting files. Name collisions keep the first discovered skill, so remove duplicate visible versions. Subagents/extensions are optional host capabilities, not prerequisites of this skill.

Read [host-portability](../references/host-portability.md) on a host/session/model switch or capability mismatch. Preserve the investigation workspace and canonical schema 3.0; recover NEXT, verify relevant artifact identity and clear stale context measurements. Resolve this adapter's supporting resources from the installed skill directory.

Documentation checked 2026-10-07: [official skill documentation](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md). Paths describe the documented release; actual discovery must be checked on the installed host.
