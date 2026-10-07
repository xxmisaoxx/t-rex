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
```

If you modify packaged files, refresh their size and SHA-256 entries in `MANIFEST.json` before validation. The manifest excludes itself.

The existing validation results apply to their stated scopes. New native/runtime or host-lifecycle claims need corresponding traces.

Contributions are distributed under the project's [GPL-3.0-only license](LICENSE).
