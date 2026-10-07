# Profile: macOS Mach-O

Record Mach-O vs FAT/universal, selected architecture slice, load commands, segments/sections, UUID, dylib dependencies, symbol/export info, rebasing/binding/chained fixups when relevant, Objective-C/Swift metadata, and code-signature metadata when relevant.

Distinguish file offset, image-relative address, preferred VM address, and runtime slid address. Normalize runtime observations to image + unslid relative identity.

High-value pivots: entry points, initializers, Objective-C classes/selectors/methods, Swift type/protocol metadata, imported frameworks, stubs/lazy symbols, and block/callback structures.

Selectors and runtime metadata may be stronger anchors than stripped function names.

## Slice and VM mapping
Bind FAT member architecture and slice offset/hash. For a normal file-backed segment, d=unslid_VMaddr-segment.vmaddr; require 0<=d<segment.filesize and valid file bounds, then slice_raw=segment.fileoff+d and container_raw=slice_offset+slice_raw. Handle zerofill section types and special segment flags explicitly; __PAGEZERO is a reserved unmapped range, not readable zero data. Runtime VMaddr=unslid_VMaddr+slide. Image-relative offsets require a named preferred base, normally the image header/__TEXT base for an ordinary image; do not use __PAGEZERO as that base. Chained fixups/PAC affect pointer interpretation; record representation and decoder assumptions.
