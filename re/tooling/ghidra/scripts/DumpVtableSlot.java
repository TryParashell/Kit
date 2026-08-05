import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.ArrayList;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Symbol;
import ghidra.program.model.symbol.SymbolIterator;
import ghidra.program.model.symbol.SymbolTable;

public class DumpVtableSlot extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("DumpVtableSlot <outputFile> [maxSlots]");
            return;
        }
        File outputFile = new File(args[0]);
        int maxSlots = args.length > 1 ? Integer.parseInt(args[1]) : 40;
        outputFile.getParentFile().mkdirs();
        PrintWriter writer = new PrintWriter(new BufferedWriter(new FileWriter(outputFile)));
        writer.println("PROGRAM " + currentProgram.getName());

        SymbolTable table = currentProgram.getSymbolTable();
        List<Symbol> tables = new ArrayList<>();
        SymbolIterator symbols = table.getAllSymbols(true);
        while (symbols.hasNext()) {
            if (monitor.isCancelled()) {
                break;
            }
            Symbol symbol = symbols.next();
            if (symbol.getName().startsWith("vftable")) {
                tables.add(symbol);
            }
        }
        writer.println("VFTABLES " + tables.size());
        int pointerSize = currentProgram.getDefaultPointerSize();
        for (Symbol symbol : tables) {
            if (monitor.isCancelled()) {
                break;
            }
            String owner = symbol.getParentNamespace().getName(true);
            Address cursor = symbol.getAddress();
            List<String> slots = new ArrayList<>();
            for (int slot = 0; slot < maxSlots; slot++) {
                Address target = readPointerAt(cursor);
                if (target == null) {
                    break;
                }
                Function function = getFunctionAt(target);
                if (function == null) {
                    break;
                }
                slots.add(slot + "|" + target + "|" + function.getName(true));
                cursor = cursor.add(pointerSize);
            }
            if (slots.isEmpty()) {
                continue;
            }
            writer.println("VT " + owner + " @ " + symbol.getAddress() + " slots=" + slots.size());
            for (String entry : slots) {
                writer.println("  " + entry);
            }
        }
        writer.close();
        println("DumpVtableSlot tables=" + tables.size() + " -> " + outputFile.getAbsolutePath());
    }

    private Address readPointerAt(Address address) {
        try {
            long value = currentProgram.getMemory().getLong(address);
            if (value == 0) {
                return null;
            }
            Address target = currentProgram.getAddressFactory()
                    .getDefaultAddressSpace().getAddress(value);
            if (!currentProgram.getMemory().contains(target)) {
                return null;
            }
            return target;
        } catch (Exception problem) {
            return null;
        }
    }
}
