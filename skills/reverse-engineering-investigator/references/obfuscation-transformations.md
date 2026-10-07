# Obfuscation and Transformations

Treat obfuscation, minification, packing, generated code, and compiler transformations as identity/provenance problems.

## Indicators
Possible signals include weak/randomized names, encrypted/encoded constants, abnormal control flow, reflective dispatch, runtime-generated code, embedded containers, compressed resources, or bootstrap stages.

Indicators are not proof of intent or maliciousness.

## Strategy
1. bind every stage to an artifact or runtime identity;
2. find stable anchors that survive naming changes;
3. distinguish stored representation from runtime representation;
4. recover one transformation boundary at a time;
5. preserve pre/post transformation evidence;
6. avoid assuming decompiled source corresponds directly to author-written source.

Useful stable anchors include signatures/descriptors, constants, imported APIs, resource paths, call/reference neighborhoods, metadata tokens, selectors, content hashes, normalized CFG structure, and runtime observations.

For dynamically produced code/data, record the producer and the exact observation boundary rather than pretending the generated form existed statically.
