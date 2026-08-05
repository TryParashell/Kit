# Reverse-engineering a proprietary CAD format — the reusable playbook

Distilled from cracking the SOLIDWORKS 2025 part format well enough to write files SOLIDWORKS opens
and rebuilds to floating-point exactness. Written to be re-run against AutoCAD, CATIA, NX, Creo,
Inventor or anything else with the same shape of problem: a closed binary container, a licensed
local install, and a need for real bidirectional interoperability.

Everything else in `re/` is the SOLIDWORKS worked example. This file is the transferable part.

---

## 0. The one-paragraph summary

Do not start by staring at bytes. Start by building a **measurement oracle** — a way to ask the
vendor application "is this file correct, and what does it contain" that you can run hundreds of
times unattended. Then attack the format on three legs at once: differential analysis of a corpus
you author yourself, runtime tracing of the vendor's own reader under a debugger, and static
decompilation of the vendor's serialisation code. Each leg answers questions the other two cannot.
Believe nothing until the oracle confirms it numerically.

The single biggest force multiplier is the oracle. The single biggest time sink is trusting a
plausible byte-level inference that no measurement backed.

---

## 1. Phase order, and why this order

Cost rises and generality rises together. Do not skip forward; each phase supplies the ground truth
the next one is checked against.

| # | phase | cost | what it buys |
|---|---|---|---|
| 1 | **Container framing** | days | read/write the file envelope; enumerate the streams |
| 2 | **Measurement oracle** | days | unattended, quantitative correctness verdicts |
| 3 | **Authored differential corpus** | 1–2 weeks | field locations for everything the app can vary |
| 4 | **Runtime trace of the reader** | days, once you know the entry points | object boundaries, index arithmetic, the fields diffing cannot see |
| 5 | **Static decompilation** | 1–2 weeks | authoritative field order, types, version gates, enum branches, lookup tables |
| 6 | **Write path** | weeks | the actual product |

Phases 4 and 5 are cheap **only after** 1–3. Attempting decompilation first drowns you: the target
had 45.9 MB in one DLL and 2607 serialisable classes. The corpus tells you which forty matter.

---

## 2. Phase 1 — container framing first, always

Formats layer: an envelope, then streams, then records. Crack the envelope completely before
looking at a single record. It is the easiest layer and it gates everything.

**What worked:** the SOLIDWORKS container turned out to be a standard ZIP shifted 8 bytes, with
three 4-byte magic numbers replaced and stream names nibble-swapped. Recognising "this is ZIP with
cosmetic damage" saved weeks. Check that first: ZIP, OLE/CFBF (Microsoft Compound File — used by
older CAD formats), SQLite, a tar variant, or a custom TOC.

**The trap that cost the most:** a per-file magic-number triplet that had to match the file's own
id. A 58-file study ruled out XOR keys, affine maps over GF(2), LCGs, CRC32, rotations, bit
permutations and every named mixer, and concluded the relation was uninvertible. **It was a
1000-entry lookup table baked into a DLL.** Two parallel `.rdata` arrays, walked once by an
initialiser into a map.

> **Generalisable lesson:** when a value looks like a hash of another value and every mixer search
> fails, stop searching for arithmetic and go look for a table. Search the binaries for the known
> constants and see what references them. Ten minutes of `findstr`-equivalent beats a week of
> cryptanalysis. `re/tooling/ghidra/scan_consts.py` and `findtable.py` are that ten minutes,
> generalised.

---

## 3. Phase 2 — the oracle is the whole game

Build this before you need it. Everything downstream is measured against it.

**Requirements:**

1. **Quantitative, not boolean.** "Opens" is nearly useless. Ask for a *number* the geometry
   determines — we used solid volume in m³ and centre of mass, and matched to ≤6e-16 relative.
   Volume alone is not enough: it cannot distinguish a plane swap or a direction flip. Centre of
   mass catches both. Get at least two independent scalars.
2. **One fresh process per candidate.** A malformed file hard-crashes the application and poisons
   every later result in that session.
3. **A control before and every batch.** Take a known-good vendor-authored file, measure it at the
   start and end of each batch, and **discard the whole batch if the control fails**. This is not
   optional bookkeeping — our install silently degraded after ~25 crash-inducing launches and
   started failing to open a pristine file. Without controls we would have recorded a dozen
   phantom "crashes" as format findings.
4. **Process hygiene.** Sweep orphaned helper and crash-reporter processes between batches. Seven
   stacked crash handlers were what actually broke the install.
5. **Kill the modal dialogs.** The app showed a *"Toolbar information is inconsistent"* startup
   modal that blocked COM registration entirely. A 40-line watchdog thread that enumerates windows
   and clicks OK (`re/tooling/harness/dismiss.py`) unblocked the entire measurement programme.
6. **Absolute paths.** Relative paths silently returned a null model rather than erroring.

**Automation surface, in preference order:** the vendor's COM/.NET/scripting API → a headless CLI →
UI automation. SOLIDWORKS COM was ideal. AutoCAD has COM + ObjectARX, NX has NXOpen, Creo has
Pro/TOOLKIT and OTK, CATIA has CAA + COM. All four are richer than what we had.

**Critical constraint we imposed on ourselves, and you should too:** the vendor API is for
*verification only*. It must never be a runtime dependency of the shipped converter, or you have
built a wrapper, not a translator. Keep every line of it in a test/scratch directory that the
product cannot import.

---

## 4. Phase 3 — author the corpus, do not scavenge it

Real-world files vary in fifty ways at once and teach you almost nothing. Files you author vary in
exactly one way.

**The method:** drive the vendor API to emit families of documents differing in a single property.
Depth. Width. Plane. Direction. End condition. Feature count. Operation. Profile type. Then diff
within the family. A field that moves when exactly one input moved is located.

**Corpus design that paid off:**

- **Control pairs.** Author the *same* document twice. Diff them. Everything that differs is
  timestamps, session ids and hashes — your noise floor. Measure it before trusting any byte.
- **A same-family ladder.** 1, 2, 3, 4 … n features, identical otherwise. This is what makes the
  per-feature block fall out of a plain diff, and it is what let us grow a container from n to n+1.
- **Both directions of every boolean.** Not just "reversed on"; on *and* off, in *both* operations.
- **Also collect a real production corpus.** Ours was a 63-file engine assembly. It does not
  localise fields, but it is irreplaceable for coverage: it exposed values our authored corpus
  never produced, and it was **localised into another language**, which killed every name-based
  heuristic we had. Test against real user data early or ship a decoder that works only on your own
  output.

**The trap:** our own round-trip artifacts got mistaken for source documents. Files the converter
had written carried an embedded copy of the original, so "successful conversions" were replaying
the embedding rather than translating. **Tag generated files and refuse them as test inputs.**

---

## 5. Phase 4 — trace the vendor's reader

Differential analysis gives you field *locations*. It cannot give you object *boundaries*, and
without boundaries you cannot insert, delete or reorder anything.

**Why boundaries matter:** the format used MFC-style `CArchive` object serialisation, where a class
is defined once by name and every later instance is a 2-byte index into a running map. Insert an
object anywhere and every index after it shifts. Change a stream's length and the file crashes the
app. No amount of static diffing recovers that arithmetic; you need to watch the reader count.

**How, concretely:**

1. Install console debugging tools (`cdb`, not the GUI — it must be scriptable and unattended).
2. Find the reader's entry points **in the export tables**. This is the step to try before any
   decompilation: our target exported its entire archive API by name, so breakpoints needed no
   symbols at all. `re/tooling/ghidra/exports.py` dumps PE exports.
3. Breakpoint the object-read entry, and log the stream position and the map counter at every hit.
   Those two numbers are the entire prize: differencing consecutive positions gives every object's
   byte span, and the counter column gives the renumbering table.
4. Filter on the buffer length so you log only the stream you care about. One launch can trace
   several streams at once by matching several lengths.

**The correctness gate that makes this trustworthy:** reparse the stream into a symbolic model
where every reference is a *pointer to a node* rather than a number, then re-emit with every index
recomputed from scratch. **If the output is byte-identical to the input, your segmentation is
provably right.** We hit byte-identical on 16 parts across 4 streams. Nothing else gives you that
much confidence, and it immediately turns into the ability to grow, shrink and reorder.

**Debugger traps, all of which cost real time:**

| trap | fix |
|---|---|
| symbol lookups across 620+ modules stall the run forever | set `SYMOPT_NO_UNQUALIFIED_LOADS` first |
| script directives collapse onto one line and swallow each other | use the one-command-per-line include form |
| mangled C++ export names are rejected by the command parser | use the undecorated spelling |
| a deferred module-load breakpoint never fires | the module was already loaded before the first stop; set it at the initial break |
| the app never calls the framework function you hooked | see below |

**The finding that only runtime gives you:** we hooked the system MFC runtime's `CArchive::ReadObject`
and got **zero hits** across a full startup and a file open. The vendor had reimplemented the
archive as its own class in its own DLL. Every static conclusion survived, but every plan built on
hooking the framework would have failed silently. **Always confirm the code you are hooking is the
code that runs.**

---

## 6. Phase 5 — decompile the serialisation code

This is what turns "byte 33 changes when I change the end condition" into "`i32` field
`getType(int)` at `this+0x0c`, read after `getDirection()`, with these six enum branches, three of
which add a nested record".

**Setup, headless only.** Ghidra 12.x + JDK 21, driven by `analyzeHeadless` and scripts. Never the
GUI. Import and full analysis took 92 s for a 250 KB DLL and **50 minutes for a 45.9 MB DLL** with a
12 GB heap. Budget for that.

*Obstacle worth knowing:* the analyser rejects any path component beginning with `.`, which rules
out a dot-prefixed scratch directory. A directory junction fixes it without moving the files.

**Three techniques that made the output readable:**

1. **Rename the archive API before decompiling.** Every field read is an overloaded `operator>>`.
   Untouched, a `double` read and a `char` read look identical. A script that renames each overload
   and import thunk to `get_<type>` using the demangled parameter type makes every field width
   unambiguous at a glance. This one script is the difference between usable and useless output.
   (`re/tooling/ghidra/scripts/RenameArchiveApi.java`)
2. **Find the real virtual slot.** The reader dispatched **vtable slot 5**, the vendor's own
   `Serialize`, not the framework's slot 2. Dump every RTTI-named vftable, map class → slot-5
   address, and you get an index of 2607 classes to their serialisers. From then on, any class is
   one lookup away. (`DumpVtableSlot.java`, `serialize_map.py`)
3. **Read the *write* path to get field names.** The store branch often writes a string key
   alongside the value for a database/debug path. That is how `Value`, `EntIndex` and others got
   authoritative names instead of guesses. Exported accessors (`getFoo`) decompile to one
   instruction and bind a name to an offset — mine them wholesale.

**What decompilation uniquely delivers:**

- **Field order, width and type**, exactly. We had a byte that was actually an `i32`, and a second
  per-direction copy nobody had found.
- **Version gates.** Every read was conditional on the document's version number. This explains
  record-length differences between old and new files and is invisible to diffing if your corpus is
  all one era.
- **Which enum values add records.** Of twelve end conditions, exactly two add a nested object. You
  cannot learn this from a corpus that never uses them.
- **Reader fixups that silently overwrite you.** Two examples: one enum value forces a neighbouring
  field to 1, and an out-of-range field is clamped to 0. Write those fields naively and the reader
  changes them behind your back.
- **Defaults returned for absent data.** A "missing" angle field was not missing: the accessor
  returns 2π when its dimension pointer is null. That single line explained why every full-revolution
  record in the corpus was byte-identical and why we could not find the angle. **An absent field can
  be a meaningful value.**

**Negative results are results.** We proved by decompilation that a particular operation flag does
*not* exist in the three classes everyone assumed owned it. That converted an open question into a
closed one and stopped further searching.

---

## 7. Verification discipline — the part that makes it engineering

Reverse engineering generates plausible hypotheses far faster than it generates true ones. Nearly
every serious error in this project was a confident inference nobody measured.

**Rules that earned their place:**

1. **Three-tier confidence, on every single field.** *confirmed* = decompiled **and** reproduces a
   real traced span, corpus record or measured number. *partial* = decompiled but nothing available
   exercises it. *not found*. Enforce the vocabulary in every document. A *partial* offset is an
   address for a hypothesis, not a fact — several of ours turned out to be **uninitialised memory**
   that the app serialises without ever setting. Copy those from a donor; never synthesise them.
2. **A stale derived cache is safe; a wrong one is not.** Formats are full of redundant caches
   derived from the authored parameters. Leaving them describing the *old* geometry worked fine —
   the app recomputes. Writing them with a plausible-but-wrong rule produced zero bodies, hard
   crashes and one silently wrong volume. **Identify which fields are authored and write only
   those.** This was the highest-value single rule we found.
3. **Prove the cache is a cache by deleting it.** The Parasolid geometry cache could be removed
   entirely and the app rebuilt the identical solid from the feature records. That one experiment
   redirected the whole project: we never needed to author geometry, only history. **Early on, try
   deleting each stream and see what still works.**
4. **Round-trip your own patcher.** Patch a donor back to its own values and confirm byte identity.
   If that fails, your locator is wrong and every downstream result is noise.
5. **Never ship an unverified claim.** The converter carries explicit `vendor_loadable` /
   `application_usable` flags, and a donor cannot back real output until someone measured it. Under
   pressure to delete these flags I kept them, because they were the only thing standing between
   "works" and "writes empty files that look fine". Attestation is not bureaucracy; it is the
   mechanism that stops silent corruption.
6. **Partial output is worse than no output.** A file missing one feature has silently wrong
   geometry. If you cannot express every feature, emit a safe empty document plus a diagnostic
   naming the blocker. Wrong geometry that opens is the worst possible failure mode.

---

## 8. Orchestrating this with subagents

The work is large, and a single context cannot hold it. What actually worked:

**Split by file ownership, not by topic.** Every parallel agent gets an explicit list of files it
owns and an explicit list it must not touch. Topic-based splits collide constantly; file-based
splits do not. When an agent needs a file it does not own, it reports rather than edits.

**Serialise access to scarce physical resources.** There is one vendor install. Two agents
measuring at once is how it got corrupted. One agent holds the application and the debugger; the
others do static work. State this in the brief in capitals, because a capable agent will otherwise
reasonably decide to verify its own work.

**Write self-contained briefs, and front-load the hard-won facts.** A subagent shares none of your
history. Every brief we sent carried the same block of established facts — calibrated offsets,
known traps, which fields must be left stale, the exact debugger incantations. This is not
redundancy; it is what stops each agent rediscovering the same trap. Several briefs ran to a page
of prior findings before stating the task, and that was the correct ratio.

**Specify the acceptance criterion as a number.** "Make it work" produces a decode-only check and a
confident report. "SOLIDWORKS opens it, the tree has N features, and volume matches to ≤1e-6
relative, with control-before and control-after values quoted" produces measurements. Every brief
said *report measured numbers; a decode-only check is not acceptance.*

**Demand honest failure.** Explicitly instruct agents to report what did not work and to withhold
unverified claims. Ours did: one reported a 32000 vs 28800 mismatch and *declined to ship the
donor* rather than pass a test. That report was worth more than a success would have been.

**Keep verification for yourself.** A subagent's claim that a gate passes is not evidence. Re-run
the formatter, the suite and the measurement checks in your own context. I re-derived the
signature table and re-read the measurement JSON directly; both held, but checking was cheap and
the alternative was reporting someone else's optimism.

**Expect to lose agents.** Two died mid-task on transport errors after substantial work. Because
their briefs said to write findings to durable files as they went, almost nothing was lost. Have
agents checkpoint to disk, not just to their final message.

**Cost:** this was 6+ hours of wall time across roughly a dozen subagent invocations, on a format
where three prior sessions had already built the corpus tooling.

---

## 9. Applying this to another CAD format

**Do these five things in the first week:**

1. **Identify the container.** ZIP, OLE/CFBF, SQLite, custom TOC. Get to a stream listing.
2. **Get the automation API opening files and reporting mass properties.** Build the control loop,
   the process sweep and the dialog killer immediately.
3. **Author a control pair and a same-family ladder.** Measure your noise floor.
4. **Dump the PE exports of every module.** Search for the serialisation vocabulary — `Archive`,
   `Serialize`, `ReadObject`, `Stream`. If the API is exported by name, runtime tracing is nearly
   free and you should do it before any decompilation.
5. **Delete each stream in turn and see what still opens.** The map of load-critical vs cache is
   the cheapest high-value artefact in the whole project.

**Expect these differences:**

- **AutoCAD** — DWG is extensively documented by the Open Design Alliance and prior projects. Start
  from the published specs; the value is in the recent versions and the proprietary object classes.
  Formats with a published spec invert the phase order: read first, trace only the gaps.
- **CATIA V5** — CATPart/CATProduct are CFBF containers. The same envelope-first approach applies.
  CAA/COM automation exists for the oracle.
- **NX** — NXOpen is a strong, well-documented oracle. Parasolid-native, so the geometry layer is a
  documented format and the proprietary part is the feature history — the same split we found, where
  history mattered and geometry did not.
- **Creo** — Pro/TOOLKIT and OTK for the oracle. Expect a granite-based object store, more unlike
  MFC serialisation than SOLIDWORKS was.

**The transferable asset is `re/tooling/`, not the SOLIDWORKS findings.** The Ghidra scripts
(archive-API renaming, vtable-slot dumping, function dumping, reference dumping), the export/PE
readers, the segmentation and symbolic re-emit model, the measurement harness with its controls and
dialog killer, and the constant-to-table search. All of it is format-agnostic. Point it at a new
target and the first week gets you to where this project was after a month.

---

## 10. What still is not solved here, so you calibrate expectations

Being honest about the ceiling is part of the method.

- The container framing is **fully inverted** — any valid file id can be written with no donor.
- Object boundaries and index renumbering are **solved**, which is what makes structural edits
  possible.
- Stream *content* still comes from a **donor** document of the right feature topology. We can
  patch, grow and reorder; we cannot serialise a feature record from nothing, because the bulk of
  it comes from base classes that were never fully decompiled.
- Boss-versus-cut cannot be flipped: the operation is not a flag, it is implied by derived
  face-identity records. **Confirmed negative** — worth more than an open question.
- Roughly forty classes have recovered layouts; 2607 are indexed and unread.

That is enough to ship a real converter for a bounded, honestly-declared subset. It is not a
complete format implementation, and the documents in `re/solidworks/` are careful to say which is
which. Preserve that discipline in the next one — the value of this archive is that its claims can
be trusted.
