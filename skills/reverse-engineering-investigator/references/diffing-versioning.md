# Diffing and Version Analysis

Bind both sides by hash, size, format/architecture, profile, and package/section inventory. Never compare offsets from different artifacts as though they share identity.

Compare in layers:
1. container/package inventory
2. section/segment structure
3. dependencies/imports/exports
4. strings/names/metadata
5. function/method identity
6. calls/references
7. normalized CFG/instruction structure
8. pseudocode/source-level representation
9. runtime behavior

Normalize before comparing. Prefer symbols, tokens/signatures, selectors, content hashes, normalized CFGs, reference neighborhoods, and module-relative identities over raw addresses.

"Bytes differ" or "decompiler text differs" does not automatically mean behavior changed. A semantic-change claim should identify a changed control/data dependency, constant/condition, call/dispatch, side effect, or observed runtime behavior.

For patch attribution, verify exact pre/post bytes, record uncontrolled environmental/version differences, and avoid causal claims when other differences remain.

## Revision lifecycle
Record parent revision, change reason and exact pre/post spans for controlled patches; replacement is not necessarily a patch. Revalidate bytes, affected decoding/CFG/xrefs/metadata and runtime mappings as appropriate. Preserve old artifacts/readouts as historical. Reuse unchanged claims only after checking dependency closure, including layout, relocations, callers and environment. Similar normalized functions across builds are candidate matches with ambiguity, not identical IDs.
