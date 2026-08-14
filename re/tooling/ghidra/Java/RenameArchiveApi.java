import java.util.ArrayList;
import java.util.List;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.data.DataType;
import ghidra.program.model.data.Pointer;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.listing.Parameter;
import ghidra.program.model.symbol.SourceType;

public class RenameArchiveApi extends GhidraScript {

    @Override
    public void run() throws Exception {
        List<Function> targets = new ArrayList<>();
        FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
        while (functions.hasNext()) {
            Function function = functions.next();
            if (isArchiveOperator(function.getName(true))) {
                targets.add(function);
            }
        }
        FunctionIterator externals = currentProgram.getFunctionManager().getExternalFunctions();
        while (externals.hasNext()) {
            Function function = externals.next();
            if (isArchiveOperator(function.getName(true))) {
                targets.add(function);
            }
        }
        int renamed = 0;
        for (Function function : targets) {
            String label = classify(function);
            if (label == null) {
                println("unclassified " + function.getName(true) + " @ "
                        + function.getEntryPoint() + " params=" + function.getParameterCount()
                        + " proto=" + function.getPrototypeString(true, false));
                continue;
            }
            try {
                function.setName(label, SourceType.USER_DEFINED);
                renamed++;
            } catch (Exception problem) {
                println("rename failed " + function.getEntryPoint() + " " + problem.getMessage());
            }
        }
        println("RenameArchiveApi targets=" + targets.size() + " renamed=" + renamed);
    }

    private boolean isArchiveOperator(String name) {
        if (!name.contains("operator>>") && !name.contains("operator<<")) {
            return false;
        }
        return name.contains("su_CArchive") || name.contains("su_CDBArchive");
    }

    private String classify(Function function) {
        boolean read = function.getName(true).contains("operator>>");
        Function source = function;
        Function thunked = function.getThunkedFunction(true);
        if (thunked != null && thunked.getParameterCount() > source.getParameterCount()) {
            source = thunked;
        }
        String base = null;
        for (Parameter parameter : source.getParameters()) {
            DataType type = parameter.getDataType();
            String name = type.getName();
            if (name.contains("su_CArchive") || name.contains("su_CDBArchive")) {
                continue;
            }
            if (type instanceof Pointer) {
                DataType inner = ((Pointer) type).getDataType();
                base = inner == null ? "voidp" : inner.getName();
            } else {
                base = name;
            }
            break;
        }
        if (base == null) {
            return null;
        }
        base = base.replaceAll("[^A-Za-z0-9_]", "_");
        String kind = function.getName(true).contains("su_CDBArchive") ? "DB" : "AR";
        return kind + (read ? "_get_" : "_put_") + base;
    }
}
