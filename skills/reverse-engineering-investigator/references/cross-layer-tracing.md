# Cross-Layer Tracing

Use this when behavior crosses runtimes, modules, processes, or packaging layers.

## 1. Keep identities separate
Each layer keeps its own stable identity:
- JS module/member + location;
- managed assembly/type/method/token;
- JVM class/method descriptor;
- native module + RVA/symbol;
- process/service/component identity;
- protocol/message/schema identity.

Do not collapse them into one address/name namespace.

## 2. Find the bridge
Typical bridges:
- Electron IPC / preload APIs;
- Node native addons;
- P/Invoke / COM / native hosting;
- JNI;
- Objective-C/Swift runtime boundaries;
- sockets/HTTP/RPC;
- files/databases/shared memory;
- command line/environment/configuration;
- serialization/deserialization boundaries.

## 3. Record bridge evidence
For every bridge, record:
- producer;
- consumer;
- operation/channel;
- payload identity or shape;
- registration/binding evidence;
- runtime confirmation when available.

## 4. Avoid semantic leakage
A string or name shared across layers is a clue, not proof of a bridge. Establish an actual call, registration, message, file, or protocol relationship.

## 5. Trace directionally
Prefer a bounded chain:
`source event -> bridge -> handler -> downstream effect`

Stop when the user's question is answered instead of mapping the entire application graph.
