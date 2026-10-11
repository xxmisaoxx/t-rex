// Export bounded, address-bearing Ghidra observations for T-REX.
// @category T-REX
import ghidra.app.util.headless.HeadlessScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.MemoryBlock;
import ghidra.program.model.symbol.*;
import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

public class TrexExport extends HeadlessScript {
    private final Gson gson = new GsonBuilder().disableHtmlEscaping().create();
    private JsonObject request;
    private Path output;
    private int maxItems, maxFunctions, maxInstructions, maxRefs;
    private JsonObject collections = new JsonObject();

    private String addressText(Address address) {
        return address.getAddressSpace().equals(currentProgram.getAddressFactory().getDefaultAddressSpace()) ?
            "0x" + address.toString() : address.toString();
    }

    private JsonObject row(String kind, Address address) {
        JsonObject o = new JsonObject();
        o.addProperty("evidence_id", request.get("run_id").getAsString() + ":" + kind + ":" + address);
        o.addProperty("address", addressText(address));
        o.addProperty("address_space", address.getAddressSpace().getName());
        if (address.getAddressSpace().equals(currentProgram.getImageBase().getAddressSpace()))
            o.addProperty("rva", "0x" + Long.toHexString(address.subtract(currentProgram.getImageBase())));
        return o;
    }

    private void coverage(String kind, int exported, int total, boolean complete) {
        JsonObject o = new JsonObject();
        o.addProperty("exported", exported);
        o.addProperty("total_in_database", total);
        o.addProperty("coverage", complete ? "complete" : "partial");
        collections.add(kind, o);
    }

    private BufferedWriter writer(String name) throws IOException {
        return Files.newBufferedWriter(output.resolve(name + ".jsonl"), StandardCharsets.UTF_8,
                                       StandardOpenOption.CREATE_NEW);
    }

    private void emit(BufferedWriter w, JsonObject o) throws IOException {
        w.write(gson.toJson(o));
        w.newLine();
    }

    private JsonObject functionRow(Function f) {
        JsonObject o = row("function", f.getEntryPoint());
        o.addProperty("name", f.getName());
        o.addProperty("qualified_name", f.getName(true));
        o.addProperty("signature", f.getSignature().toString());
        o.addProperty("body_size", f.getBody().getNumAddresses());
        o.addProperty("external", f.isExternal());
        o.addProperty("thunk", f.isThunk());
        return o;
    }

    private void inventory() throws Exception {
        int total = 0, count = 0;
        try (BufferedWriter w = writer("functions")) {
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext()) {
                monitor.checkCancelled();
                Function f = it.next(); total++;
                if (count < maxItems) { emit(w, functionRow(f)); count++; }
            }
        }
        coverage("functions", count, total, count == total);
        total = 0; count = 0; boolean stringsComplete = true;
        try (BufferedWriter w = writer("strings")) {
            DataIterator it = currentProgram.getListing().getDefinedData(true);
            while (it.hasNext()) {
                monitor.checkCancelled();
                Data d = it.next();
                Object value = d.getValue();
                if (!(value instanceof String)) continue;
                total++;
                if (count < maxItems) {
                    JsonObject o = row("string", d.getAddress());
                    String text = (String)value;
                    int limit = request.get("max_text_chars").getAsInt();
                    boolean truncated = text.length() > limit;
                    o.addProperty("value", truncated ? text.substring(0, limit) : text);
                    o.addProperty("value_truncated", truncated);
                    o.addProperty("value_length_chars", text.length());
                    if (truncated) stringsComplete = false;
                    o.addProperty("length_bytes", d.getLength());
                    o.addProperty("data_type", d.getDataType().getName());
                    emit(w, o); count++;
                }
            }
        }
        coverage("strings", count, total, count == total && stringsComplete);
        total = 0; count = 0;
        try (BufferedWriter w = writer("symbols")) {
            SymbolIterator it = currentProgram.getSymbolTable().getAllSymbols(true);
            while (it.hasNext()) {
                monitor.checkCancelled();
                Symbol s = it.next(); total++;
                if (count < maxItems) {
                    JsonObject o = row("symbol", s.getAddress());
                    o.addProperty("name", s.getName(true));
                    o.addProperty("evidence_id", o.get("evidence_id").getAsString() + ":" + s.getName(true) + ":" + s.getSymbolType());
                    o.addProperty("type", s.getSymbolType().toString());
                    o.addProperty("source", s.getSource().toString());
                    o.addProperty("external", s.isExternal());
                    emit(w, o); count++;
                }
            }
        }
        coverage("symbols", count, total, count == total);
        total = 0; count = 0;
        try (BufferedWriter w = writer("segments")) {
            for (MemoryBlock b : currentProgram.getMemory().getBlocks()) {
                total++;
                if (count >= maxItems) continue;
                JsonObject o = row("segment", b.getStart());
                o.addProperty("name", b.getName());
                o.addProperty("end", addressText(b.getEnd()));
                o.addProperty("size", b.getSize());
                o.addProperty("read", b.isRead()); o.addProperty("write", b.isWrite());
                o.addProperty("execute", b.isExecute()); o.addProperty("initialized", b.isInitialized());
                emit(w, o); count++;
            }
        }
        coverage("segments", count, total, count == total);
    }

    private JsonObject reference(Reference r) {
        JsonObject o = row("reference", r.getFromAddress());
        o.addProperty("evidence_id", o.get("evidence_id").getAsString() + ":" + r.getToAddress() + ":" + r.getOperandIndex() + ":" + r.getReferenceType());
        o.addProperty("from", addressText(r.getFromAddress()));
        o.addProperty("to", addressText(r.getToAddress()));
        o.addProperty("from_space", r.getFromAddress().getAddressSpace().getName());
        o.addProperty("to_space", r.getToAddress().getAddressSpace().getName());
        o.addProperty("type", r.getReferenceType().toString());
        o.addProperty("source", r.getSource().toString());
        o.addProperty("operand", r.getOperandIndex());
        return o;
    }

    private JsonObject detail(Function f, DecompInterface dec) throws Exception {
        JsonObject o = functionRow(f);
        JsonArray instructions = new JsonArray(); int instructionTotal = 0;
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        JsonArray outgoing = new JsonArray(); int outgoingTotal = 0;
        while (it.hasNext()) {
            monitor.checkCancelled();
            Instruction ins = it.next(); instructionTotal++;
            if (instructions.size() < maxInstructions) {
                JsonObject i = row("instruction", ins.getAddress());
                i.addProperty("text", ins.toString());
                StringBuilder bytes = new StringBuilder();
                for (byte b : ins.getBytes()) bytes.append(String.format("%02x", b & 0xff));
                i.addProperty("bytes", bytes.toString()); instructions.add(i);
            }
            for (Reference r : ins.getReferencesFrom()) {
                outgoingTotal++;
                if (outgoing.size() < maxRefs) outgoing.add(reference(r));
            }
        }
        o.add("instructions", instructions);
        o.addProperty("instruction_count", instructionTotal);
        o.addProperty("instructions_coverage", instructions.size() == instructionTotal ? "complete" : "partial");
        o.add("outgoing_references", outgoing);
        o.addProperty("outgoing_count", outgoingTotal);
        JsonArray incoming = new JsonArray(); int incomingTotal = 0;
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint());
        while (refs.hasNext()) {
            monitor.checkCancelled();
            Reference r = refs.next(); incomingTotal++;
            if (incoming.size() < maxRefs) incoming.add(reference(r));
        }
        o.add("incoming_references", incoming);
        o.addProperty("incoming_scope", "function entry only; not all addresses in its body");
        o.addProperty("incoming_count", incomingTotal);
        o.addProperty("references_coverage", incoming.size() == incomingTotal && outgoing.size() == outgoingTotal ? "complete" : "partial");
        DecompileResults result = dec.decompileFunction(f, request.get("decompile_timeout").getAsInt(), monitor);
        boolean ok = result.decompileCompleted() && result.getDecompiledFunction() != null;
        o.addProperty("decompile_status", ok ? "success" : "failed");
        o.addProperty("decompile_error", result.getErrorMessage());
        boolean codeTruncated = false;
        if (ok) {
            String code = result.getDecompiledFunction().getC();
            int limit = request.get("max_pseudocode_chars").getAsInt();
            codeTruncated = code.length() > limit;
            o.addProperty("pseudocode", codeTruncated ? code.substring(0, limit) : code);
            o.addProperty("pseudocode_length_chars", code.length());
        }
        o.addProperty("pseudocode_truncated", codeTruncated);
        o.addProperty("coverage", ok && !codeTruncated && instructions.size() == instructionTotal &&
                      incoming.size() == incomingTotal && outgoing.size() == outgoingTotal ? "complete" : "partial");
        return o;
    }

    private void details() throws Exception {
        LinkedHashMap<Address, Function> selected = new LinkedHashMap<>();
        JsonArray unresolved = new JsonArray();
        JsonArray selectors = request.getAsJsonArray("selectors");
        if (selectors.size() == 0) {
            FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
            while (it.hasNext() && selected.size() < maxFunctions) {
                Function f = it.next();
                if (!f.isExternal()) selected.put(f.getEntryPoint(), f);
            }
        } else {
            for (JsonElement selector : selectors) {
                String text = selector.getAsString(); int matched = 0;
                if (text.startsWith("0x")) {
                    Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(text.substring(2));
                    Function f = currentProgram.getFunctionManager().getFunctionAt(a);
                    if (f != null) { selected.put(f.getEntryPoint(), f); matched++; }
                } else {
                    FunctionIterator it = currentProgram.getFunctionManager().getFunctions(true);
                    while (it.hasNext()) {
                        monitor.checkCancelled();
                        Function f = it.next();
                        if (f.getName().equals(text) || f.getName(true).equals(text)) {
                            selected.put(f.getEntryPoint(), f); matched++;
                        }
                    }
                }
                if (matched == 0) unresolved.add(text);
            }
        }
        DecompInterface dec = new DecompInterface(); int exported = 0; boolean complete = unresolved.size() == 0;
        try (BufferedWriter w = writer("details")) {
            if (!dec.openProgram(currentProgram)) throw new IOException("Cannot open decompiler: " + dec.getLastMessage());
            for (Function f : selected.values()) {
                monitor.checkCancelled();
                if (exported >= maxFunctions) { complete = false; break; }
                JsonObject d = detail(f, dec);
                if (!d.get("coverage").getAsString().equals("complete")) complete = false;
                emit(w, d); exported++;
            }
        } finally { dec.dispose(); }
        coverage("details", exported, selected.size(), complete);
        collections.getAsJsonObject("details").add("unresolved_selectors", unresolved);
        collections.getAsJsonObject("details").addProperty("scope", selectors.size() == 0 ?
            "first bounded sample of discovered functions; not all functions" : "requested function names/entry addresses");
    }

    @Override public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2 || currentProgram == null) throw new IOException("Expected request JSON and output directory with a loaded program");
        request = JsonParser.parseString(Files.readString(Path.of(args[0]), StandardCharsets.UTF_8)).getAsJsonObject();
        output = Path.of(args[1]);
        String actualSha = currentProgram.getExecutableSHA256();
        if (actualSha == null || !actualSha.equalsIgnoreCase(request.get("expected_sha256").getAsString()))
            throw new IOException("Program SHA256 does not match the requested artifact");
        maxItems = request.get("max_items").getAsInt(); maxFunctions = request.get("max_functions").getAsInt();
        maxInstructions = request.get("max_instructions").getAsInt(); maxRefs = request.get("max_refs").getAsInt();
        if (request.get("inventory").getAsBoolean()) inventory();
        details();
        JsonObject metadata = new JsonObject();
        metadata.addProperty("schema_version", "1.0");
        metadata.addProperty("run_id", request.get("run_id").getAsString());
        metadata.addProperty("program", currentProgram.getName());
        metadata.addProperty("program_sha256", actualSha);
        metadata.addProperty("format", currentProgram.getExecutableFormat());
        metadata.addProperty("language", currentProgram.getLanguageID().toString());
        metadata.addProperty("compiler", currentProgram.getCompilerSpec().getCompilerSpecID().toString());
        metadata.addProperty("image_base", "0x" + currentProgram.getImageBase());
        metadata.addProperty("analysis_timed_out", analysisTimeoutOccurred());
        metadata.addProperty("coverage_meaning", "Export coverage of Ghidra database/requested slices, not proof that every function, string or behavior was recovered");
        metadata.add("collections", collections);
        Files.writeString(output.resolve("metadata.json"), gson.toJson(metadata), StandardCharsets.UTF_8,
                          StandardOpenOption.CREATE_NEW);
        println("T-REX export complete: " + output);
    }
}
