# Profile: JVM / JAR / Class

Record archive hash, class inventory, manifest/module metadata, constant pools, class/method descriptors, dependencies, and resources.

Use stable identity `package.Class#method(descriptor)`. Bytecode offsets are method-local and artifact-version-specific.

High-value pivots: main/entry points, `<clinit>`, `<init>`, interface dispatch, invokedynamic/bootstrap methods, reflection, service loaders, serialization, resource/config lookup, and JNI bridges.

When names are weak, use descriptors, constant-pool references, call structure, strings/constants, inheritance/interfaces, annotations, and runtime class loading.

## Binding and class identity
Bind class/member to archive bytes and class-loader/load instance when runtime identity matters; descriptors are not globally unique across loaders/versions. JNI may bind through name exports or RegisterNatives name+descriptor+function pointer tables, often in JNI_OnLoad; JNI_OnLoad is a pivot, not a universal requirement. Trace System.load/loadLibrary to the actual loaded native revision, then its OS profile. Include reflection/MethodHandles and runtime-generated classes only when the question reaches them.
