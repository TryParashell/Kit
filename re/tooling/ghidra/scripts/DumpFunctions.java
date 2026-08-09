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
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DumpFunctions extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            println("DumpFunctions <outputFile> <specFile> [depth] [timeoutSeconds]");
            return;
        }
        File outputFile = new File(args[0]);
        int depth = args.length > 2 ? Integer.parseInt(args[2]) : 1;
        int timeout = args.length > 3 ? Integer.parseInt(args[3]) : 180;

        List<String> specs = new ArrayList<>();
        for (String raw : Files.readAllLines(Paths.get(args[1]))) {
            String text = raw.trim();
            if (!text.isEmpty() && !text.startsWith(";") && !text.startsWith("#")) {
                specs.add(text);
            }
        }

        Map<Address, Function> roots = new LinkedHashMap<>();
        for (String spec : specs) {
            if (spec.startsWith("0x") || spec.startsWith("@")) {
                String hex = spec.startsWith("@") ? spec.substring(1) : spec.substring(2);
                Address address = currentProgram.getAddressFactory()
                        .getDefaultAddressSpace().getAddress(Long.parseLong(hex, 16));
                Function function = getFunctionAt(address);
                if (function == null) {
                    function = getFunctionContaining(address);
                }
                if (function != null) {
                    roots.put(function.getEntryPoint(), function);
                } else {
                    println("NO FUNCTION for " + spec);
                }
            } else {
                FunctionIterator functions =
                        currentProgram.getFunctionManager().getFunctions(true);
                while (functions.hasNext()) {
                    Function function = functions.next();
                    if (function.getName(true).contains(spec)) {
                        roots.put(function.getEntryPoint(), function);
                    }
                }
            }
        }
        println("roots=" + roots.size());

        Map<Address, Integer> plan = new LinkedHashMap<>();
        Deque<Function> queue = new ArrayDeque<>();
        for (Function function : roots.values()) {
            plan.put(function.getEntryPoint(), 0);
            queue.add(function);
        }
        while (!queue.isEmpty()) {
            Function function = queue.poll();
            int level = plan.get(function.getEntryPoint());
            if (level >= depth) {
                continue;
            }
            Set<Function> called = function.getCalledFunctions(monitor);
            for (Function callee : called) {
                if (callee.isThunk() || callee.isExternal()) {
                    continue;
                }
                if (!plan.containsKey(callee.getEntryPoint())) {
                    plan.put(callee.getEntryPoint(), level + 1);
                    queue.add(callee);
                }
            }
        }
        println("total=" + plan.size());

        DecompInterface decompiler = new DecompInterface();
        DecompileOptions options = new DecompileOptions();
        options.setMaxWidth(160);
        decompiler.setOptions(options);
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        decompiler.setSimplificationStyle("decompile");
        if (!decompiler.openProgram(currentProgram)) {
            println("FAILED to open program: " + decompiler.getLastMessage());
            return;
        }

        outputFile.getParentFile().mkdirs();
        PrintWriter writer = new PrintWriter(new BufferedWriter(new FileWriter(outputFile)));
        writer.println("PROGRAM " + currentProgram.getName());
        writer.println("IMAGEBASE " + currentProgram.getImageBase());
        int done = 0;
        Set<Address> seen = new HashSet<>();
        for (Map.Entry<Address, Integer> entry : plan.entrySet()) {
            if (monitor.isCancelled()) {
                break;
            }
            if (!seen.add(entry.getKey())) {
                continue;
            }
            Function function = getFunctionAt(entry.getKey());
            if (function == null) {
                continue;
            }
            writer.println();
            writer.println("=== FUNCTION " + function.getName(true));
            writer.println("=== ADDRESS " + function.getEntryPoint());
            writer.println("=== DEPTH " + entry.getValue());
            writer.println("=== SIGNATURE " + function.getPrototypeString(true, false));
            DecompileResults results = decompiler.decompileFunction(function, timeout, monitor);
            if (results != null && results.decompileCompleted()
                    && results.getDecompiledFunction() != null) {
                writer.println(results.getDecompiledFunction().getC());
                done++;
            } else {
                writer.println("=== DECOMPILE FAILED "
                        + (results == null ? "null" : results.getErrorMessage()));
            }
            writer.flush();
        }
        writer.println();
        writer.println("=== SUMMARY planned=" + plan.size() + " decompiled=" + done);
        writer.close();
        decompiler.dispose();
        println("DumpFunctions decompiled=" + done + " -> " + outputFile.getAbsolutePath());
    }
}
