# Profile: Android APK / DEX

Record APK hash, manifest, signing/certificate metadata when relevant, DEX files, resources, native `lib/<abi>/*.so`, assets, and embedded configs.

Stable identities:
- managed: package + class + method descriptor
- native: library + module-relative address/symbol
- resources: resource id + package/member identity

High-value pivots: manifest components, application class, activities/services/receivers/providers, intent filters, permissions, exported components, DEX references, JNI registrations, native libraries, WebView/JS bridges, and serialization/network/storage boundaries.

For JNI map Java/Kotlin declaration -> registration/binding -> native function -> native behavior. Static presence does not prove execution in a scenario.

## Packaging and JNI composition
Include split APKs/dynamic features and relevant classes*.dex; bind declaring DEX and selected ABI library independently. Class-loader/overload descriptors distinguish Java methods. JNI binding may use exports or RegisterNatives tables (name, descriptor, pointer), often via JNI_OnLoad. A missing exported Java_ symbol is not evidence of a missing native method. Compose Android with ELF for the selected library and JVM-style loader/descriptor reasoning where relevant. APK signature/resource IDs are version-scoped, not stable universal IDs.
