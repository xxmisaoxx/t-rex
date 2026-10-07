# Profile: Generic Native

Use when the native format is unknown, unsupported, or mixed.

Collect magic/format, architecture/endian, load regions, code/data boundaries, dependencies/import/export clues, entry points, relocation model, names/strings, and exception/unwind metadata when present.

Then specialize into PE, ELF, Mach-O, firmware/container, or architecture-specific reasoning as soon as evidence permits.

Use `references/native-reasoning.md` for provenance and CFG reasoning.
