# Architecture-Aware Reasoning

Architecture rules refine provenance; they do not replace artifact-specific reasoning.

## x86-64
Track partial-register semantics carefully: writes to 32-bit GPRs zero-extend into the corresponding 64-bit register, while 8/16-bit writes do not. Account for flags, LEA-as-arithmetic, stack-pointer movement, red-zone differences by ABI, and caller/callee-saved conventions.

### Windows x64
Arguments normally begin RCX, RDX, R8, R9; return in RAX. Shadow space exists. Do not interpret stack arguments without the current stack delta.

### System V AMD64
Integer/pointer arguments normally begin RDI, RSI, RDX, RCX, R8, R9; return in RAX. Account for the ABI's caller/callee-saved set and red zone where applicable.

## ARM64 / AArch64
Integer/pointer arguments normally begin X0-X7; return in X0. Track Wn/Xn aliasing: writes to Wn zero the upper 32 bits of Xn. ADR/ADRP plus ADD/LDR sequences often construct addresses; trace the pair, relocations, and page-relative semantics together.

Watch for:
- BL/BLR direct vs indirect calls;
- X30/LR and tail calls;
- stack-frame pairs such as STP/LDP;
- literal pools;
- GOT/PLT or platform-specific stubs;
- PAC-related instructions on Apple platforms when relevant.

## General rule
Never force an ABI interpretation when compiler optimization, thunks, hand-written assembly, or interop boundaries provide contrary evidence. Trace the actual data flow.

## Windows x64 exact coordinates
For the ordinary ABI, integer/pointer positional slots 1–4 use RCX/RDX/R8/R9; floating slots use XMM0–XMM3 by argument position, not a separate compacted counter. FP/vector returns use XMM0 where applicable; scalar integer/pointer returns use RAX. Hidden structure-result pointers, member functions, varargs and vectorcall require the actual convention/prototype. RCX alone does not establish `this`.

At ordinary callee entry, [entry_RSP] is return address, [entry_RSP+8..+0x27] is 32-byte home/shadow space, fifth argument begins [entry_RSP+0x28]. Relate current RSP/RBP to entry_RSP before naming stack slots. Home space is not proof that a value was spilled. Windows has no System V red zone. Track volatile GPRs RAX/RCX/RDX/R8–R11 and XMM0–XMM5 across calls; preserved registers can still change via explicit writes in the current function.

For System V, integer summaries omit SSE/vector/aggregate classification and possible hidden result pointers. Use the relevant psABI when those types matter. Exception/funclet frames and hand-written thunks require their own frame evidence.
