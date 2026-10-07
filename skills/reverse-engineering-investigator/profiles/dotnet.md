# Profile: .NET / CLI

Record PE identity plus CLI header, assembly name/version, module MVID when available, metadata streams, type/method/field definitions, references, resources, and signing metadata when relevant.

Prefer stable method identity: assembly + type + method signature; use metadata token, and MVID+token for exact artifact binding. Native addresses may be JIT/runtime-dependent and are not primary identities.

High-value pivots: entry point, constructors/static constructors, interface implementations, attributes, P/Invoke, reflection, serializers, async/iterator state machines, delegates/events, and resource/config lookup.

When names are obfuscated, pivot through tokens, signatures, call/reference structure, constants/strings, metadata relationships, and runtime behavior. Decompiled source is reconstruction, not original source.

## Mixed and runtime variants
Distinguish IL-only, mixed-mode, ReadyToRun and NativeAOT/hosted assemblies from evidence; a PE CLI header is not proof every function is IL. Bind token/MVID to exact bytes (MVID is not a content hash). At P/Invoke trace DLL name, entry point, marshaling/convention and actual resolved native module; include NativeLibrary resolution, COM vtable/interface binding and reverse callbacks when implicated. Load the native profile at that boundary. Runtime generic instantiations, JIT tiers and loaded assembly versions can map one logical method to multiple code bodies.
