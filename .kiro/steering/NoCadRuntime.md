# CAD APPLICATIONS ARE TEST ORACLES ONLY

Production translation must be self-contained. No CAD application or vendor automation facility may participate in a runtime conversion.

## THE RULE

**Never use CAD software at runtime.** This includes, without limitation, SOLIDWORKS COM APIs, SOLIDWORKS executables, FreeCAD executables or Python modules, CATIA automation, Fusion services, vendor SDKs, command-line translators, headless CAD processes, plug-ins, RPC bridges, and proprietary CAD kernels.

Runtime includes every shipped library, CLI, API, worker, server, desktop integration, batch job, and subprocess used to read, translate, or write a customer document. A conversion must work on a clean machine with none of the source or target CAD applications installed, configured, licensed, or running.

## ORACLE-ONLY EXCEPTION

CAD software may be used only in isolated development and test workflows as an oracle to:

- author controlled differential samples;
- inspect source semantics;
- open generated output and measure loadability, bodies, mass properties, feature trees, editability, and rebuild behavior;
- collect debugger, decompiler, or runtime traces needed to reverse engineer a format.

Oracle execution must remain outside production code paths and must be explicitly invoked as testing or reverse-engineering tooling. Oracle-produced vendor bytes must never be embedded, copied, patched, packaged, or used as runtime templates. The writer must emit every byte from first-principles format knowledge under `NoDonorBlocks.md`.

## FORBIDDEN RUNTIME DEPENDENCIES

- COM, OLE automation, macros, add-ins, or document-manager automation supplied by a CAD vendor.
- Launching or attaching to a CAD executable, whether interactive, silent, headless, containerized, or remote.
- Importing CAD application modules or dynamically loading their installed libraries.
- Calling a local or hosted service that delegates conversion to CAD software.
- Requiring a CAD installation, license, registry entry, environment variable, daemon, or user session.
- Falling back to CAD software when the native parser or writer encounters an unsupported construct.

## REQUIRED ARCHITECTURE

- Parse source containers and records directly from documented format findings.
- Build a vendor-neutral in-memory model containing all parametric and assembly semantics.
- Write target containers and records directly from that model.
- Keep oracle harnesses under test or reverse-engineering tooling and prevent production modules from importing them.
- Fail explicitly on unsupported input until first-principles support is implemented; never cross the runtime boundary to a CAD application.

## VERIFICATION

Before reporting a translator complete:

1. Run its production conversion tests with CAD applications unavailable.
2. Recursively scan production code for CAD automation imports, process launches, SDK bindings, service calls, and oracle-harness dependencies.
3. Confirm installation metadata declares no CAD application, SDK, license, or service dependency.
4. Use the target CAD application only afterward, in an isolated oracle test, to validate the already-generated file.
5. Confirm the same output bytes can be generated without the oracle present.

If production conversion invokes CAD software directly or indirectly, it violates this rule and is not complete.
