// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashSet;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;

public class DumpRefs extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 3) {
            println("DumpRefs <outputFile> <startHex> <endHex> [timeout]");
            return;
        }
        File outputFile = new File(args[0]);
        long start = Long.parseLong(args[1], 16);
        long end = Long.parseLong(args[2], 16);
        int timeout = args.length > 3 ? Integer.parseInt(args[3]) : 240;
        Address from = currentProgram.getAddressFactory().getDefaultAddressSpace()
                .getAddress(start);
        Address to = currentProgram.getAddressFactory().getDefaultAddressSpace()
                .getAddress(end);
        outputFile.getParentFile().mkdirs();
        PrintWriter writer = new PrintWriter(new BufferedWriter(new FileWriter(outputFile)));
        writer.println("PROGRAM " + currentProgram.getName());
        writer.println("RANGE " + from + " .. " + to);
        Set<Function> functions = new LinkedHashSet<>();
        Address cursor = from;
        while (cursor.compareTo(to) <= 0) {
            if (monitor.isCancelled()) {
                break;
            }
            ReferenceIterator refs = currentProgram.getReferenceManager()
                    .getReferencesTo(cursor);
            while (refs.hasNext()) {
                Reference reference = refs.next();
                writer.println("REF " + reference.getFromAddress() + " -> "
                        + reference.getToAddress() + " " + reference.getReferenceType());
                Function function = getFunctionContaining(reference.getFromAddress());
                if (function != null) {
                    functions.add(function);
                }
            }
            cursor = cursor.add(4);
        }
        writer.println("FUNCTIONS " + functions.size());
        DecompInterface decompiler = new DecompInterface();
        DecompileOptions options = new DecompileOptions();
        options.setMaxWidth(160);
        decompiler.setOptions(options);
        decompiler.toggleCCode(true);
        decompiler.setSimplificationStyle("decompile");
        decompiler.openProgram(currentProgram);
        for (Function function : functions) {
            if (monitor.isCancelled()) {
                break;
            }
            writer.println();
            writer.println("=== FUNCTION " + function.getName(true));
            writer.println("=== ADDRESS " + function.getEntryPoint());
            writer.println("=== SIGNATURE " + function.getPrototypeString(true, false));
            DecompileResults results = decompiler.decompileFunction(function, timeout, monitor);
            if (results != null && results.decompileCompleted()
                    && results.getDecompiledFunction() != null) {
                writer.println(results.getDecompiledFunction().getC());
            } else {
                writer.println("=== DECOMPILE FAILED");
            }
            writer.flush();
        }
        writer.close();
        decompiler.dispose();
        println("DumpRefs functions=" + functions.size() + " -> " + outputFile.getAbsolutePath());
    }
}
