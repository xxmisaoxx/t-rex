# Profile: Linux ELF

Record ELF class/endian, architecture, PIE/fixed status, program headers, section headers when present, interpreter, dynamic section, DT_NEEDED dependencies, symbol tables, relocations, init/fini arrays, and build-id when present.

Distinguish file offset, ELF virtual address, and module-relative runtime address. Normalize PIE/ASLR observations to module + relative address.

High-value pivots: `_start`, libc/loader startup, `.init_array`, `.fini_array`, PLT/GOT, relocation targets, exported symbols, constructors, unwind metadata, and stripped-symbol recovery through references/strings/call structure.

For dynamic dispatch consider PLT/GOT indirection, dynamic loading/resolution, callbacks, vtables, and resolver behavior when relevant.

## Mapping contract
Use PT_LOAD program headers for loaded-image mapping; section headers may be absent. For ELF VA V in a file-backed load segment, raw=p_offset+(V-p_vaddr), requiring 0<=V-p_vaddr<p_filesz and raw<file_size. The remainder up to p_memsz is memory-only zero-fill before runtime writes. Runtime VA=load_bias+ELF_VA; state how load_bias is established from mappings and p_vaddr alignment. A module-relative offset must name its chosen base, not silently assume ELF VA equals RVA. TLS instances differ by thread; relocations/IFUNC/resolvers can change loaded targets.
