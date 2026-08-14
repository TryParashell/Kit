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

public class DumpVtables extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 1) {
            println("DumpVtables <outputFile>");
            return;
        }
        File outputFile = new File(args[0]);
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
            String name = symbol.getName();
            if (name.equals("vftable") || name.startsWith("vftable")) {
                tables.add(symbol);
            }
        }
        writer.println("VFTABLES " + tables.size());

        int pointerSize = currentProgram.getDefaultPointerSize();
        for (Symbol symbol : tables) {
            if (monitor.isCancelled()) {
                break;
            }
            writer.println();
            writer.println("=== VFTABLE " + symbol.getParentNamespace().getName(true)
                    + " @ " + symbol.getAddress());
            Address cursor = symbol.getAddress();
            for (int slot = 0; slot < 256; slot++) {
                Address target;
                try {
                    target = readPointerAt(cursor);
                } catch (Exception problem) {
                    break;
                }
                if (target == null) {
                    break;
                }
                Function function = getFunctionAt(target);
                if (function == null) {
                    break;
                }
                writer.println("  " + slot + " " + target + " " + function.getName(true));
                cursor = cursor.add(pointerSize);
            }
            writer.flush();
        }
        writer.close();
        println("DumpVtables tables=" + tables.size() + " -> " + outputFile.getAbsolutePath());
    }

    private Address readPointerAt(Address address) throws Exception {
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
    }
}
