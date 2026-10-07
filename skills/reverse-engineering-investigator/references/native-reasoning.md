# Native Reasoning Core

Use with an OS-specific native profile.

## Address domains
Never mix file offset, RVA/image-relative address, preferred VA, rebased runtime VA, or section/segment-relative offset. Record conversions explicitly.

## Function identity
Boundaries may come from unwind/exception metadata, symbols, exports, provider analysis, CFG reconstruction, or heuristics. Record confidence and authority.

## Register/value provenance
At a sink: identify exact use; find local reaching definition; cross blocks via CFG/dominance; account for call clobbers and aliases; distinguish unique from path-dependent provenance; trace callers only when needed.

## Stack provenance
Establish frame state first. Account for stack-pointer deltas, frame-pointer use, reused slots, incoming stack args, and exception/unwind effects when relevant.

## Global/object provenance
Identify storage, enumerate reads/writes, locate constructors/initializers/registrations, distinguish file-backed from runtime initialization, and consider indirect stores or loader/thread initialization. "No static write found" is not "never initialized".

## Indirect dispatch
Consider function pointers, vtables, import thunks, callback registries, jump tables, interface/selector dispatch, and dynamically resolved APIs. State whether indirect coverage was attempted before claiming caller completeness.

## Branch reasoning
Recover condition/flag provenance; distinguish syntactic from feasible paths; account for exception edges; use runtime observation if feasibility remains unresolved.

## Preconditions and failure cases
Use half-open ranges and validate arithmetic, file bounds, architecture/endian and decoding mode. A linear sweep can decode data as instructions; an xref database can be incomplete. A dominating definition is not automatically the unique reaching definition: account for later writes, branch merges, aliasing, calls and exceptional edges. Distinguish address calculation from dereference, zero-initialized storage from a later runtime value, and a pointer's storage location from its pointee.

Treat jump tables as control-flow dispatch unless a callable target is established. Include tail transfers, callbacks, address-taken uses, vtable construction/registration and loader/TLS/global initialization when relevant; do not enumerate all indirect calls without a narrowing clue.

Authority is claim-specific. Current file bytes establish stored representation; current runtime memory establishes observed loaded/generated representation. Decode only with validated architecture/mode/mapping. Parser output, CFG databases and pseudocode are fallible interpretations. Preserve both providers' reports, then choose a discriminating byte/metadata/path check; no provider quorum is required.
