# Profile: JavaScript / Electron / ASAR

Identify package.json, main-process entry, preload scripts, renderer bundles, ASAR members, unpacked companions, source maps, native Node addons, and resources/config.

Prefer archive/member path, content hash, module/bundle identity, and verified source-map original-source identity over unstable minified line/column positions.

High-value pivots: Electron bootstrap, BrowserWindow, preload/contextBridge, IPC registrations/senders, filesystem/network boundaries, updater/bootstrap logic, dynamic import/require, bundler module tables, and source maps.

For cross-layer questions map renderer -> preload -> IPC -> main -> native/service explicitly. Do not infer one layer's behavior from another without bridge evidence.

Bind source maps to the exact analyzed bundle before treating them as evidence.

## Native addon pivot
Trace require/import resolution to the actual `.node` file, including app.asar.unpacked companions. Bind addon architecture and Electron/Node ABI to the loaded revision; distinguish Node-API registration from V8/legacy registration and wrapper exports. A JavaScript method name alone does not identify a native function. Route `.node` by its PE/ELF/Mach-O header, connect registration/export wrapper to the native sink, then stop when the question is answered. Workers and renderer/main/preload contexts can resolve different modules.
