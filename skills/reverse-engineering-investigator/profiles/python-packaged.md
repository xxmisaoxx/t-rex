# Profile: Packaged Python

Identify the packager from evidence: PyInstaller, Nuitka, cx_Freeze, zipapp/zipimport, embedded CPython, or custom bootstrap. Do not infer from filename alone.

Map native launcher, embedded archive, `.pyc`/bytecode, Python modules, resources/config, and native extensions.

Use outer artifact hash plus internal member path/hash and recoverable qualified module/object identity as stable anchors.

High-value pivots: bootstrap/entry module, import/module graph, embedded archive index, constants/strings, native-extension boundaries, configuration, and resource loading.

Recovered Python source from bytecode is reconstructed source; preserve bytecode/module evidence for important claims.

## Representation and native bridge
Record CPython/bytecode magic/version and extraction provenance. Use version-matched decoding; CPython bytecode is not a stable cross-version ISA. PyInstaller can contain bootloader, PYZ/other archives, bytecode and native extensions; Nuitka compiles modules and need not preserve recoverable `.pyc`. Do not force bytecode decompilation onto compiled modules. Trace import resolution, PyInit_<module> (or legacy init), method tables and C-API wrappers to `.pyd`/`.so` native identities; ctypes/cffi are other possible bridges. Preserve the original container plus extracted member hashes; a temporary extraction path alone is not identity.
