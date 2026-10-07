# Artifact Router

Classify the target before selecting analysis techniques.

## Identify the outer container
Executable image, library, archive, application bundle, package, disk image, firmware/container, script/source tree, analysis database, or captured runtime artifact.

## Identify the execution model
- Native: PE/COFF, ELF, Mach-O, unknown native.
- Managed/VM: .NET CLI, JVM, Android DEX, WebAssembly, other VM formats.
- Application layer: Electron/ASAR, JavaScript bundles, packaged Python, resources/configuration.
- Mixed: Electron+native addon, .NET+native DLL, APK+JNI ELF, Python+native extension, app+helper binaries.

Route nested artifacts independently and connect evidence across layers.

## Minimal identification evidence
Prefer magic/signatures, architecture, loader metadata, manifests, section/segment tables, CLI headers, DEX/JAR metadata, archive members, and imported runtimes. Filename extensions are hints, not authority.

## Route matrix
- MZ + native PE headers -> Windows PE.
- PE + CLI header -> .NET.
- ELF header -> Linux ELF/native.
- Mach-O/FAT -> macOS Mach-O.
- JAR/class metadata -> JVM.
- APK/classes.dex -> Android.
- ASAR/Electron bootstrap -> JavaScript/Electron.
- PyInstaller/Nuitka/embedded-Python indicators -> packaged Python.

For ambiguity, record it, run the smallest identification probe, then select the profile.

If complete authoritative source is sufficient, use source analysis first. Historical or third-party source is reference evidence, not automatic authority for the current binary.

## Recovery and composition
Recover selected profiles before classifying again. Magic identifies a container, not every execution layer: PE+CLI may include native/mixed code; a packaged Python launcher is native while its members may be bytecode or compiled code. Route a nested member only when the active question crosses it. iOS is a bundle/context overlay over Mach-O; WASM may be host-embedded. Preserve member/slice identity.
