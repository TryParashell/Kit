# `re/` — reverse-engineering workspace

Everything durable that came out of reverse-engineering the SOLIDWORKS part format, organised so a
new agent can pick it up, trust the right parts, and repeat the exercise on a different CAD format.

`Methodology.md` is the reusable playbook — read it first if your target is AutoCAD, CATIA, NX or
Creo. Everything else in this directory is the SOLIDWORKS worked example that the playbook was
distilled from.

## Size

| part | size |
|---|---|
| `re/` excluding binaries | **~6.9 MB** |
| the four vendor DLLs in `re/binaries/` | **~52.6 MB** |
| `re/` total, all tracked | **~59.5 MB** |

The DLLs are **tracked**, deliberately, so that a cloud agent with no SOLIDWORKS install can run
Ghidra against them. Read `binaries/README.md` for the licensing position before this repository is
shared with anyone outside Parashell — they are unmodified proprietary Dassault Systèmes binaries
from a licensed local install, and `binaries/Fetch.ps1` reproduces them from that install if you
would rather not carry them.

The bulk of the tracked bytes is machine-readable evidence: `re/data/` (~4.6 MB, dominated by the
static container census and the traced object segmentations) and `re/solidworks/measurements/`
(~1.1 MB of volume measurements). The prose is about 380 KB.

## Layout

| directory | what is in it |
|---|---|
| `binaries/` | the four SOLIDWORKS DLLs every finding was derived from, plus `Manifest.json` (SHA-256 and version of each) and `Fetch.ps1` (re-copies them from a local install). Tracked. Read `binaries/README.md` first. |
| `solidworks/` | the findings. Layered: `container/` (file framing + the signature table), `archive/` (the `su_CArchive` grammar, the reader's identity, object segmentation), `records/` (per-class field layouts), `features/` (extrude, revolve, sketch, arc, bodies), `corpus/` (what corpora exist and what each proves), `measurements/` (every volume measurement, with controls). |
| `tooling/` | how the work was done and how to redo it: `ghidra/` (headless decompilation), `windbg/` (the cdb runtime trace), `harness/` (the COM measurement loop). |
| `data/` | the extracted tables and traced artefacts the findings cite: the 1000-entry signature table, the 2607-class `Serialize` map, the object segmentations, the class vocabulary. |

## How to navigate by question

| you want to know | start at |
|---|---|
| how a `.SLDPRT` file is framed, and how to write a valid header | `solidworks/container/README.md` |
| how objects are tagged inside a stream, and why byte edits renumber | `solidworks/archive/Grammar.md` §2, then `archive/Segmentation.md` |
| what class owns a given byte | `solidworks/records/Serialize.md`, then `data/SerializeMap.json` |
| whether a specific field is trustworthy | the confidence column of the table that declares it — see below |
| what has been *measured* rather than inferred | `solidworks/measurements/README.md` |
| what does not work, and the traps | `solidworks/README.md` "Negative results and traps" |
| how to reproduce the decompilation | `tooling/ghidra/Setup.md` |
| how to reproduce the runtime trace | `tooling/windbg/README.md` |

## Confidence vocabulary

Every field table in `re/solidworks/` labels each row. The vocabulary is defined in
`solidworks/records/Serialize.md` and used consistently everywhere:

* **confirmed** — read out of the decompiled `Serialize` *and* the byte arithmetic reproduces a real
  traced object span, a real corpus record, or a measured volume exactly.
* **partial** — read out of the decompiled `Serialize`, but nothing available exercises the field:
  its value is constant across the corpus, or the branch is never taken, so nothing independent
  checks it.
* **not found** (spelled **unresolved** in the oldest tables) — not recovered.

Treat the distinction as load-bearing. A **partial** offset is a hypothesis with an address, not a
fact; several of them turned out to be uninitialised memory rather than parameters.

## Reproducing

Everything here was produced on Windows with PowerShell, `uv` for Python, a licensed SOLIDWORKS 2025
install, Ghidra 12.1.2 headless, and `cdbX64.exe` from the WinDbg MSIX package.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File re\binaries\Fetch.ps1
uv run python re\tooling\ghidra\Sigtable.py
uv run python re\tooling\ghidra\Generation\SerializeMap.py
uv run python re\tooling\ghidra\Validation\VerifyLayout.py
```

The first re-fetches and verifies the binaries. The other three re-derive `data/SignatureTable.json`,
`data/SerializeMap.json` and `data/VerifyLayout.json` from the binaries plus the traced
segmentations, and they rewrite those files in place — a clean `git diff` after running them is the
cheapest end-to-end check that the recorded tables really do come out of the recorded bytes.

`tooling/README.md` states, per script, what still needs inputs that live in the gitignored
`.rescratch/` working directory (the `.SLDPRT` corpora and the multi-megabyte Ghidra dumps).

## What is deliberately not here

* The Ghidra 12.1.2 distribution (3.4 GB) and its release zip (573 MB). `tooling/ghidra/Setup.md`
  has the download URL, the exact filename and its byte size.
* The portable FreeCAD used to author `.FCStd` inputs (2.2 GB).
* The `.SLDPRT` / `.SLDASM` corpora. The real-world corpus already lives in the repository at
  `examples/`; the authored corpora live in `.rescratch/{corpus,corpus2,trace,donors,arc,grammar}/parts`
  and are referenced by path, not copied. `solidworks/corpus/README.md` maps every corpus to its
  location and to what it proves.
* Raw cdb logs (~3.4 MB) and the decompiled C dumps (~24 MB). The `cdb` scripts that generate the
  logs are in `tooling/windbg/`; the spec files and wrappers that generate the dumps are in
  `tooling/ghidra/`. The *conclusions* are in `re/solidworks/` and the *segmentations* in
  `re/data/segments/`.
* Ghidra project databases, `__pycache__`, and any generated `.SLDPRT`.

## Scope honesty

This work reads and *patches* SOLIDWORKS streams. It does not serialise one from nothing. The
container framing is fully inverted (any of 1000 file ids can be written with no donor); stream
content still comes from a donor part of the right feature topology. `solidworks/README.md` states
exactly where that line falls.
