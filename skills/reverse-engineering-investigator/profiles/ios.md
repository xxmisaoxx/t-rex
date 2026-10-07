# Profile: iOS IPA / App

Treat the IPA/app as a bundle containing Mach-O binaries, frameworks, extensions, resources, entitlements, and configuration.

Record bundle identifier/version, executable identity, architecture slices, embedded frameworks/extensions, Info.plist, entitlements, resources, and signature metadata when relevant.

Use `profiles/macos-macho.md` for native Mach-O reasoning, with extra pivots through Objective-C selectors/classes, Swift metadata, URL schemes, app/scene delegates, extensions, XPC/services where present, and framework boundaries.

Normalize runtime native addresses to image + unslid relative identity. Keep bundle/resource identity separate from Mach-O address identity.

For mixed UI/native behavior, use `references/cross-layer-tracing.md`.
