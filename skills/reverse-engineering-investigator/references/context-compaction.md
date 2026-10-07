# Adaptive context and compaction

Checkpoint preserves knowledge; compaction changes working context. Decide separately.

Use exposed active capacity C, used tokens U, remaining H=C-U, estimated next-operation input/output cost N, bounded future-work reserve F and uncertainty/output margin M. Use upper estimates where uncertain. Ask whether H >= N+F+M. Ratios are diagnostic hints, never independent triggers. Future reserve covers work until the next natural checkpoint, not the entire overnight investigation.

If headroom suffices, continue even at a high ratio. If it does not, persist missing critical knowledge first, reduce/paginate the planned operation, and reconsider. Compact only if a useful bounded operation still will not fit and continuation state is durable. Compaction may be controlled by the host; do not claim an unavailable API was invoked. After compaction recompute from actual telemetry; do not assume a shrink amount.

Example: C=1,000,000 U=780,000 gives H=220,000. With N=12,000 F=25,000 M=20,000, continue. With N=230,000, reduce the probe or compact after checkpointing. A smaller C=32,000 U=30,000 with N=3,000 F=1,000 M=2,000 needs persistence and reduction/compaction.

If capacity/usage is unavailable, record unknown. Use bounded slices and durable continuation, react to host pressure signals, and avoid invented precision. On host, model or session switch, clear prior capacity/usage and operation estimates, mark telemetry noncurrent, and obtain the new runtime's measurements. The optional helper's `reset-context` command does this without changing evidence or NEXT. On compaction recompute actual usage; do not assume a shrink amount. Duplicated/transient context can be removed or summarized without discarding unresolved exact bytes.

Continuation anchor: objective; checkpoint revision; active artifact revisions/profiles; active question; relevant E-IDs and maps; rejected hypotheses; probe signatures/outcomes; exact NEXT operation, parameters, discriminator and fallback; stale/provider/coverage notes. Keep a compact view, not a transcript. Loading the entire ledger after compaction defeats this design.
