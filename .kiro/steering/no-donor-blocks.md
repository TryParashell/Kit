# Kit: ABSOLUTE PROHIBITION ON DONOR BLOCKS — REVERSE ENGINEER THE FORMAT

This is the highest-priority rule in the Kit repository. Kit is a CAD interchange SDK. Its entire reason to exist is that it understands proprietary formats. A donor block is an admission that it does not.

## THE RULE

**No vendor bytes ship. Ever.** Not embedded, not encoded, not in a data file, not patched, not copied between documents. You reverse engineer the format until you can emit it from first principles.

A writer is finished when its output is `vendor_loadable = True` and `application_usable = True` with **zero donor bytes**, proven by opening the file in the vendor application. Nothing else counts as done.

## FORBIDDEN

- Encoded vendor streams in source. The `_BASE_*` family that used to live in `src/convert/adapters/solidworks/native.py` is the canonical example of what must never come back: 13 constants, ~90 KB of base85-of-zlib SOLIDWORKS streams. They were deleted. Do not reintroduce them in any form.
- Vendor streams as package data (`.bin`, `.dat`, `.json`) under `src/`.
- Reading a stream out of `tests/fixtures/`, `examples/`, or `.rescratch/` at runtime.
- Patching a recorded payload at known offsets and calling it generated. `patch_rectangle_pad` over a donor `Config-0-ResolvedFeatures` was this, and it is gone.
- Any constant you cannot explain field by field.

## ALLOWED

- **Declarative format vocabulary.** `src/convert/adapters/solidworks/topology.py` and the tables in `definition.py` are the precedent: class names, schema numbers, enum codes, line-style dash patterns, annotation-to-line-font bindings. Facts about the format, readable in source, each traceable to a finding in `re/`.
- **Named residual spans**, small and isolated, when the surrounding record is decoded, the owning class is in the name, the offset and length are documented in `re/`, and there is a decompiler or oracle reason it cannot yet be derived. `definition.py` carries six such spans totalling 296 bytes against 3322 declared. Report that split whenever you land a stream, and drive the opaque number down.
- **Irreducible format constants**, minimal and proven. `container.py` carries one 16-byte `(file_id, signature triplet)` row because `FUN_3cc4d270` in `sldmfcu.dll` looks the triplet up by `file_id` and `FUN_3cc528b0` / `FUN_3cc52ac0` compare it against the file, and because an exhaustive search over all 1000 pairs proved no computable relation exists. One row is a constant. The 1000-row table was a donor block, and it is gone.
- **The source document's own streams** when converting that document. SLDPRT → SLDPRT templating off the input is not a donor.

## YOU DO NOT STOP, AND YOU DO NOT ASK

Two acceptable stopping conditions, and no others:

- **A. Success** — the vendor application opens the output with the full feature tree and correct geometry, zero donor bytes, verified against a control.
- **B. Out of context.**

Missing grammar is not a stopping condition, it is the work. An undocumented stream is not a stopping condition, it is the work. Never ask whether to continue reverse engineering, never offer the user a menu of streams to attack, never present a carrier as a result. Identify the blocking stream, say you are going after it, and go.

## THE STATE OF THE WORK

Read these before starting so you do not redo solved problems:

- `re/solidworks/records/DEFINITION.md` — `Contents/Definition` is solved and an emitted one is measured opening. Contains the working method end to end: corpus differential, preamble field map, Ghidra addresses, oracle ladder, generation rule.
- `re/solidworks/records/ANSWERS.md` — the seven format questions, including the container signature closure.
- `re/solidworks/archive/MULTISTREAM.md` — per-stream segmentation and per-feature growth blocks.
- `re/solidworks/measurements/MEASURE.md` — which streams are load-critical, measured by deletion and substitution.
- `re/METHODOLOGY.md` §9 — the oracle protocol.
- `re/tooling/ghidra/SETUP.md` — how to drive headless Ghidra here.

The remaining load-critical blockers are `Contents/CMgr` and `Contents/Config-0`. Everything else on the part path is either synthesized or legitimately templated from the source document.

## THE METHOD

Ghidra on `re/binaries/*.dll` (hashes in `re/binaries/manifest.json`), WinDbg/cdb for runtime read traces, the SOLIDWORKS COM oracle via `re/tooling/harness/` for proof, corpus differentials over one-variable authored documents, and subagents in parallel with explicit file-ownership lists.

Write every finding into `re/` as you make it — addresses, measured numbers, failure modes, and refuted hypotheses. A refuted hypothesis is as valuable as a confirmed one; record it so nobody pays for it twice.

## VERIFICATION

1. Recursive scan of `src/` finds zero encoded vendor payload blobs and zero vendor stream data files.
2. Every emitted byte is derived, declared vocabulary traceable to `re/`, or a named documented residual span.
3. SOLIDWORKS opens the output with the full feature tree and correct geometry, against a control.
4. `vendor_loadable` and `application_usable` are `True`, and they are true.

If any check fails, keep working until A or B.
