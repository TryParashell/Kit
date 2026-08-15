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
import java.util.ArrayList;
import java.util.List;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;

public class DumpDecomp extends GhidraScript {

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length < 2) {
            println("DumpDecomp <outputFile> <patternFile> [timeoutSeconds]");
            return;
        }
        File outputFile = new File(args[0]);
        List<String> patterns = Files.readAllLines(Paths.get(args[1]));
        List<String> wanted = new ArrayList<>();
        for (String raw : patterns) {
            String text = raw.trim();
            if (!text.isEmpty() && !text.startsWith(";") && !text.startsWith("#")) {
                wanted.add(text);
            }
        }
        int timeout = args.length > 2 ? Integer.parseInt(args[2]) : 120;

        DecompInterface decompiler = new DecompInterface();
        DecompileOptions options = new DecompileOptions();
        options.setMaxWidth(160);
        decompiler.setOptions(options);
        decompiler.toggleCCode(true);
        decompiler.toggleSyntaxTree(true);
        decompiler.setSimplificationStyle("decompile");
        if (!decompiler.openProgram(currentProgram)) {
            println("FAILED to open program in decompiler: " + decompiler.getLastMessage());
            return;
        }

        outputFile.getParentFile().mkdirs();
        PrintWriter writer = new PrintWriter(new BufferedWriter(new FileWriter(outputFile)));
        writer.println("PROGRAM " + currentProgram.getName());
        int matched = 0;
        int decompiled = 0;
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            if (monitor.isCancelled()) {
                break;
            }
            Function function = functions.next();
            String name = function.getName(true);
            String match = null;
            for (String pattern : wanted) {
                if (name.contains(pattern)) {
                    match = pattern;
                    break;
                }
            }
            if (match == null) {
                continue;
            }
            matched++;
            writer.println();
            writer.println("=== FUNCTION " + name);
            writer.println("=== ADDRESS " + function.getEntryPoint());
            writer.println("=== SIGNATURE " + function.getPrototypeString(true, false));
            writer.println("=== MATCHED " + match);
            DecompileResults results = decompiler.decompileFunction(function, timeout, monitor);
            if (results != null && results.decompileCompleted()
                    && results.getDecompiledFunction() != null) {
                writer.println(results.getDecompiledFunction().getC());
                decompiled++;
            } else {
                String message = results == null ? "null results" : results.getErrorMessage();
                writer.println("=== DECOMPILE FAILED " + message);
            }
            writer.flush();
        }
        writer.println();
        writer.println("=== SUMMARY matched=" + matched + " decompiled=" + decompiled);
        writer.close();
        decompiler.dispose();
        println("DumpDecomp matched=" + matched + " decompiled=" + decompiled
                + " -> " + outputFile.getAbsolutePath());
    }
}
