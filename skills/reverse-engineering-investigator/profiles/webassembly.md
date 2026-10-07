# Profile: WebAssembly

Record module hash, version, sections, imports, exports, memories, tables, globals, data segments, element segments, custom/name sections, and embedding context.

Prefer stable identities such as module hash + function index/export name. Raw host addresses are runtime implementation details and should not be primary identities.

High-value pivots:
- exported functions;
- imported host functions;
- indirect-call tables;
- memory/data layout;
- initialization/start function;
- JS/native embedding boundary;
- custom/name/source-map metadata when verified.

For an application using WASM, map host -> import/export -> WASM function/table/memory -> downstream host effects explicitly.
