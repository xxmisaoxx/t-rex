# Contributing to T-REX

Useful contributions include reproducible investigations, host discovery fixes, clearer profile guidance and state-handling bugs.

Before changing the skill, read [SKILL.md](skills/reverse-engineering-investigator/SKILL.md) and keep project-specific findings outside the reusable package. Preserve canonical state ownership and the relative resource tree.

## Report a problem

Include the agent and version, installation method, target format, expected result and actual result. A short trace or small fixture helps. Remove credentials and private target data before sharing a report.

For an investigation showcase, include the question, method, evidence and unresolved points. Label examples and simulations. Report measured results only with the comparison procedure.

## Submit a change

Explain the user-visible problem, the resulting behavior and how you checked it. Documentation changes need working links and runnable commands. Host changes should cite the host's official documentation and distinguish packaging checks from actual product invocation.

Run from the repository root with Python 3.10+:

```sh
python skills/reverse-engineering-investigator/scripts/validate_package.py skills/reverse-engineering-investigator
python skills/reverse-engineering-investigator/scripts/test_state.py
python skills/reverse-engineering-investigator/scripts/test_hosts.py
python skills/reverse-engineering-investigator/scripts/test_tools.py
python skills/reverse-engineering-investigator/scripts/test_rizin_mcp.py
```

For real Ghidra integration tests, set `GHIDRA_HOME` and `JAVA_HOME` to a compatible installation, then run `test_tools.py -v`. Without Ghidra, its three live cases are explicitly skipped. CI also runs real headless integration on Ubuntu and Windows; ELF compiler cases run on Unix only.

For real Rizin and MCP tests, install `scripts/requirements-mcp.txt` in a virtual environment, set `RIZIN_PATH` to the Rizin executable, and run `test_rizin_mcp.py -v`. Without these optional dependencies, their live cases are explicitly skipped. The Rizin/MCP CI matrix uses pinned Rizin archives and the official MCP SDK on Ubuntu and Windows.

If you modify packaged files, refresh their size and SHA-256 entries in `MANIFEST.json` before validation. The manifest excludes itself.

The existing validation results apply to their stated scopes. New native/runtime or host-lifecycle claims need corresponding traces.

Contributions are distributed under the project's [GPL-3.0-only license](LICENSE).
