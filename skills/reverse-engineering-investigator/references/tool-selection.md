# Provider-Neutral Tool Selection

Choose a capability, not a brand: artifact identification, byte reads, sections/segments, names, strings, disassembly, decompilation, CFG, xrefs, callers/callees, metadata parsing, runtime observation, package traversal, or diffing.

For important results record artifact identity, provider/tool, version when material, operation, parameters/search boundary, and result location.

Use a second provider when function boundaries disagree, pseudocode is implausible, xrefs appear incomplete, decoding changed after patching, or a high-impact conclusion is cheap to verify independently. Do not cross-check everything by default.

If a tool hangs or becomes unreliable: record failure, decide whether it blocks the question, switch representation/provider when possible, and avoid open-ended tool debugging unless tool repair is the actual task.

Prefer bounded output: one function/range, filtered xrefs, targeted strings, or a bounded trace. Summarize large output into durable evidence and retain raw slices only when exact reasoning still needs them.

## Graceful degradation
Give expensive/unstable operations a task-appropriate time/output bound and fallback. For hangs salvage valid partial slices, record incomplete coverage and switch representation; use a cheap diagnostic once if likely decisive. For corrupt databases preserve the original and use an isolated fresh analysis of the same revision. For incomplete xrefs add byte/relocation/address-taken/registration paths rather than assert absence. For attach failures pursue static discriminators, logs or an alternate controlled observation boundary. For stripped symbols use metadata/CFG/references. For packing bind stored and unpacked/runtime stages. For architecture mismatch verify header/loader mode before decoding. Truncated output needs pagination or a smaller query; never treat it as complete.
