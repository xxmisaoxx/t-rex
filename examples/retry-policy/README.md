# Try T-REX on a retry policy

This small source fixture lets you check the agent's reasoning and try its continuation workflow. It is a tutorial, not a benchmark of native binary analysis.

Clone this repository and install the skill in your agent's project. Use [retry_policy.c](retry_policy.c) as the target. A source read is enough; you do not need a compiler or disassembler.

## First session

Paste this into your agent:

```text
Use the reverse-engineering-investigator skill.
Target: examples/retry-policy/retry_policy.c
Workspace: investigation-retry

Explain the initial delay and how the delay is capped when retries are enabled.
Show the source evidence and separate observations from deductions.
Leave the disabled-retry case as an open question. Save a checkpoint with
the exact NEXT for answering that question in a later session.
```

The agent should save target identity, its supporting source evidence, the open question and an actionable NEXT in the investigation workspace. Those files are created by your agent; the repository does not include a pre-solved checkpoint.

## New session

Open a fresh session in the same workspace and paste:

```text
Use the reverse-engineering-investigator skill to continue investigation-retry.
Recover the saved state, verify the relevant target identity and execute NEXT.
Answer the disabled-retry question and update the evidence and checkpoint.
```

Check whether the agent recovers the saved question and uses the source to answer it. The [validation report](../../skills/reverse-engineering-investigator/VALIDATION-RESULTS.md) describes the separately evaluated continuation cases.

## Check your answer

<details>
<summary>Expected behavior and optional compiler check</summary>

With retries enabled, attempt 0 gives 250 ms. Attempt 5 gives 1000 ms. Larger attempts are clamped to 6 before multiplication, and the returned delay is capped at 1000 ms. With retries disabled, the function returns 0 before performing that calculation.

On a system with a C compiler, from the repository root:

```sh
cc -std=c11 examples/retry-policy/retry_policy.c -o /tmp/trex-retry-example
/tmp/trex-retry-example
```

Expected output:

```text
250 1000 1000 0
```

The command above uses a Unix temporary path. On Windows, compile with your existing C toolchain and choose an executable output path appropriate to it. The compiler check verifies this fixture's output; it does not test the agent's checkpoint behavior.

</details>

After this example, choose one question about your own software and provide its path. Avoid starting with a request to explain an entire application.
