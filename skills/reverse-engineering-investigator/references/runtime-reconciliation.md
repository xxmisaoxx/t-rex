# Runtime / Static Reconciliation

Use runtime observation for a specific unresolved question: actual value, indirect target, branch outcome, writer, decoded/constructed data, or actual caller/handler.

Normalize runtime identities:
- native: module + RVA
- .NET: assembly + type + method/token where practical
- JVM: class + method signature
- JS: script/source-map identity + location
- Android: package/component + DEX/native identity

One run proves behavior only for that artifact, environment, input, and path.

When runtime and static evidence disagree:
1. verify executed artifact;
2. verify rebase/normalization;
3. verify patch/version state;
4. consider dynamic loading/decryption/generated code;
5. consider input/environment path differences;
6. check provider database freshness;
7. record both sides before resolving the mismatch.
