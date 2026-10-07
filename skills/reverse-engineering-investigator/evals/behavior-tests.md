# Behavioral eval suite

Run each fixture in scenarios.json as an agent task with the skill and minimal raw task context. Keep expected/failure rubrics hidden from the solver. Score actions and claims, including which files/profiles/probes are read. Do not score merely by matching words.

Each case: PASS when all expected decision criteria hold; FAIL when a listed failure occurs; PARTIAL when correct but needed evidence/actions missing; NOT RUN without an actual trace. Record model, host, skill manifest hash, fixture hash, output path, evaluator and limitations. Structural checks and helper tests are separate levels.

## S01 — Windows PE x64

Input: PE x64, ImageBase=0x140000000; section VA=0x1000 raw=0x400 raw_size=0x200 virtual_size=0x500. Sink RVA=0x1100; another value RVA=0x1300. Caller loads RDX from a zero-backed global before a call.

Expected behavior: Map sink to raw 0x500; recognize RVA 0x1300 lacks file backing; trace RDX and runtime writers without assuming null forever.

Failure: Read virtual tail as file bytes or infer RCX=this.

## S02 — Linux ELF

Input: PIE ELF without section headers; PT_LOAD p_vaddr=0x2000 p_offset=0x1000 p_filesz=0x300 p_memsz=0x800; runtime address 0x702180, load_bias=0x700000.

Expected behavior: Normalize to ELF VA 0x2180 and raw 0x1180; use program headers; keep zero tail distinct.

Failure: Require section headers or equate first executable map with load bias.

## S03 — .NET

Input: Two assemblies have the same names/signatures but different hashes and MVIDs; method uses DllImport with an entry-point alias.

Expected behavior: Bind IL to hash/MVID/token and resolve actual P/Invoke native module and marshaling before assigning target.

Failure: Treat token or assembly name as cross-version unique, or native address as primary IL identity.

## S04 — Electron plus addon

Input: main.js requires a package whose loader resolves app.asar.unpacked/native.node; renderer sends an IPC message.

Expected behavior: Load JS plus format-specific native profile only as bridge is reached; trace IPC registration, require resolution and addon export wrapper.

Failure: Infer bridge from matching string or map every renderer module.

## S05 — Android plus JNI

Input: APK contains classes2.dex, two ABI libraries and a RegisterNatives table for an overloaded method; no Java_ export.

Expected behavior: Bind DEX descriptor and selected ABI ELF separately; trace registration table name/signature/pointer.

Failure: Claim no JNI handler because exported symbol is absent.

## S06 — Packaged Python plus extension

Input: Launcher contains a PyInstaller PYZ and codec.pyd; alternate build is Nuitka compiled with no .pyc.

Expected behavior: Identify representation/version, trace import and PyInit/method-table boundary; use native profile for pyd.

Failure: Insist on bytecode decompilation for Nuitka or use mismatched bytecode decoder.

## S07 — Artifact replaced

Input: NEXT references R1 at a saved RVA; same path now hashes R2, same size.

Expected behavior: Preserve R1 history, bind R2, mark dependent active claims pending, remap only relevant locations then resume discriminator.

Failure: Trust same path/size or invalidate unrelated artifact facts.

## S08 — Artifact patched

Input: R1→R2 changes a branch; caller list and a global absence search depend on that region; another module is unchanged.

Expected behavior: Verify exact before/after bytes and revision lineage; stale transitive/coverage claims, preserve unrelated module, refresh affected decoding/CFG.

Failure: Only invalidate claims whose own location overlaps patch, or reuse all unchanged bytes as semantic proof.

## S09 — Stale disassembly

Input: Saved decode says conditional branch; current same-location bytes represent a different instruction sequence; mode uncertain.

Expected behavior: Check revision/mapping/mode/current bytes; retain reported output as historical or disputed; re-decode narrow slice.

Failure: Promote pseudocode above current stored bytes or confuse runtime patch with file mutation.

## S10 — No direct callers

Input: Completed direct CALL scan finds none; address appears in callback registration; indirect dispatch not resolved.

Expected behavior: State bounded direct absence; trace callback registration/address-taken consumer as NEXT.

Failure: Conclude function is unreachable or scan every indirect call globally.

## S11 — Runtime initialization

Input: No file-backed value or direct store is found for a global; TLS callback exists and alias stores are not covered.

Expected behavior: Keep initialization UNKNOWN; inspect TLS/constructor/loader/alias discriminator or watch a specific runtime write.

Failure: Conclude the global is permanently zero.

## S12 — Tool hang

Input: Decompiler times out with a partial function body; prior retry unchanged; byte reads and disassembly work.

Expected behavior: Record partial/failed coverage, salvage valid slice, switch to bounded disassembly/metadata, retain retry condition.

Failure: Repair decompiler indefinitely or report zero xrefs from timeout.

## S13 — Provider disagreement

Input: Two providers disagree on a boundary; same bytes but one decoder is in wrong architecture mode.

Expected behavior: Compare input identity and mode; use current header/instruction constraints to discriminate, retaining reports separately.

Failure: Count votes or require third provider without a question.

## S14 — Resume after compact

Input: CURRENT-STATE points to checkpoint 12; JSON has Q3 and NEXT=trace store at RVA 0x2200; completed probes stored.

Expected behavior: Recover canonical question and relevant E-IDs/maps, verify revision, execute exact store probe.

Failure: Start strings/inventory or load entire ledger.

## S15 — Prompt re-pasted

Input: After compact original broad task is re-pasted; checkpoint already narrowed to Q4 and a pending binding table read.

Expected behavior: Treat original task as continuing scope; recover Q4 and exact NEXT, retaining rejected probes.

Failure: Recreate objective and rediscover architecture.

## S16 — Model switch

Input: Old model had 1M telemetry; new capacity is 64k, actual current usage unknown; same workspace/revisions.

Expected behavior: Recover state and IDs, invalidate old telemetry, use bounded NEXT and unknown pressure until actual telemetry exists.

Failure: Reuse 1M budget or compact based on invented usage.

## S17 — 1M with substantial headroom

Input: C=1000000 U=780000 N=12000 F=25000 M=20000; durable checkpoint.

Expected behavior: Continue: headroom 220000 exceeds budget 57000; checkpoint independently as findings change.

Failure: Compact merely at 78% or because usage exceeds 150k.

## S18 — Small window near limit

Input: C=32000 U=30000 N=3000 F=1000 M=2000; latest critical result unpersisted.

Expected behavior: Checkpoint first, reduce operation; compact/request host compaction if useful bounded operation cannot fit.

Failure: Run a large probe before persistence or claim a missing compaction API was called.

## S19 — Overnight low novelty

Input: Two comparable probes for Q1 repeat no new evidence; Q2 has a viable small registration-table probe; tool retries unchanged.

Expected behavior: Recognize saturation, store signature/outcome/retry condition, pivot discriminator or Q2 and continue in scope.

Failure: Stop the whole run solely because Q1 saturated or repeat unchanged probes.

## S20 — Multiple profiles

Input: An Android bundle embeds JS/WASM and invokes JNI ELF; objective concerns one serialized value crossing these layers.

Expected behavior: Load Android/JS/WASM/ELF only along demonstrated chain; keep typed namespaces and record producer/consumer bindings.

Failure: Merge all identities into one RVA namespace or load all profiles at startup.
