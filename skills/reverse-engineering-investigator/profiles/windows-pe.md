# Profile: Windows PE / Native

## Core identity
Record machine architecture, image base, section table, entry point, file/section alignment, imports/delay imports, exports, exception directory, relocations, TLS callbacks, load config, resources, debug directory, and signature metadata when relevant.

## Address conversion
For an RVA inside a file-backed section:
`raw = PointerToRawData + (RVA - VirtualAddress)`

Preferred VA:
`VA = ImageBase + RVA`

Do not assume zero-filled virtual tails have file bytes.

## x64 specifics
`.pdata`/unwind metadata can strengthen function-boundary confidence. Baseline Windows x64 arguments are RCX, RDX, R8, R9, then stack; return in RAX. Trace actual reaching definitions; ABI labels alone do not prove provenance.

## Initialization pivots
Entry point, CRT startup, TLS callbacks, static/global constructors, loader callbacks, DLL/service initialization, and dynamically resolved imports.

## Patch freshness
After patching verify current bytes, refresh affected analysis when possible, record the new hash, and keep pre/post artifact identities distinct.

## Bounded mapping and unwind details
For a section candidate let d=RVA-VirtualAddress. Require d>=0, d<SizeOfRawData and PointerToRawData+d<file_size before treating it as file-backed; also establish section membership using the actual image layout (raw alignment padding and VirtualSize can differ). If the RVA is in a mapped virtual tail without raw backing, it has no raw byte. Header RVAs below SizeOfHeaders may map directly when file-backed. Overlapping/malformed sections require explicit ambiguity. The certificate/security directory uses a file offset, unlike ordinary RVA directories. Runtime_VA=actual_loaded_base+RVA; preferred VA uses the declared ImageBase. Relocations can change pointer bytes after loading.

For ordinary x64 UNWIND_INFO parse byte0 as version=byte0&7, flags=byte0>>3. CountOfCodes counts 2-byte slots, including extra operand slots. Optional data follows the code array aligned to 4 bytes. Distinguish CHAININFO's trailing RUNTIME_FUNCTION from handler RVA/data; do not combine incompatible flags or parse unsupported versions as known. Runtime-function BeginAddress/EndAddress describe half-open ranges. Leaf functions may have no record; chained records, funclets, hot/cold splits and tail thunks are not necessarily distinct source functions. Validate against current prologue bytes before trusting stack reconstruction.
