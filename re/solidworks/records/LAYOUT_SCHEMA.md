# `class_layouts.json` — the machine-readable layout contract

The static segmenter and the constructive writer both consume `re/data/class_layouts.json`. This
file defines its schema so the reverse-engineering side and the implementation side can be worked
on independently.

Static segmentation is the keystone. A stream can only be segmented without a runtime trace if,
for every class, the serialized body length is computable from the bytes at hand. That is what
this file records: per class, the ordered child slots, the constant byte runs between them, and
the rule for any run that is not constant.

## Provenance of the run lengths

`re/tooling/ghidra/solve_runs.py` solves the constant runs directly from the nine traced
segmentations in `re/data/segments/`. Against those traces it resolves **303 run keys** and leaves
**27 variable** across **12 classes**. Those twelve are the ones that need a decompiled layout,
because their bodies carry a string, a count-driven array, or a conditional field:

`sgLineHandle`, `sgArcHandle`, `sgEntHandle`, `sgLLDist`, `sgSketch`, `sgPointHandle`,
`moSketchChain_c`, `moSketchRegion_c`, `moSketchExtRef_w`, `moExtrusion_c`, `moICE_c`,
`moFeatureDimHandle_c`, `moDisplayDistanceDim_c`, `moDefaultRefPlnData_c`.

Everything else is a fixed run and needs no further work.

## Run keys

A class body is a sequence of constant byte runs separated by child objects, in the order
`su_CArchive` reads them:

```
<lead run> <child 0> <run 0> <child 1> <run 1> ... <child n-1> <run n-1>
```

A class with no children has a single run, keyed `leaf`.

| key | meaning |
|---|---|
| `lead` | bytes from the end of the object's own tag to the start of child 0 |
| `<i>` | bytes from the end of child `i` to the start of child `i+1`, or to the end of the body for the last child |
| `leaf` | the whole body, for a class that never has children |

## Schema

```json
{
  "version": 1,
  "source": "re/data/segments + sldmodu_serialize.c",
  "classes": {
    "moExtrusion_c": {
      "confidence": "confirmed",
      "child_slots": ["moEndSpec_c", "moFromEndSpec_c", "*"],
      "runs": { "lead": 14, "0": 8, "1": 0 },
      "variable_runs": [
        {
          "slot": "5",
          "rule": "string",
          "at": 0,
          "note": "ff fe ff <u8 units> then units UTF-16LE code units"
        }
      ],
      "fields": [
        {
          "run": "lead",
          "offset": 0,
          "width": 4,
          "type": "u32",
          "name": "getType",
          "role": "authored",
          "confidence": "confirmed"
        }
      ]
    }
  }
}
```

### `confidence`

The vocabulary of `SERIALIZE.md`, unchanged: **confirmed** = read out of the decompiled
`Serialize` *and* the byte arithmetic reproduces a real traced span, a real corpus record or a
measured volume; **partial** = read out of the decompiler but nothing available exercises it;
**not found** = not recovered.

A class is `confirmed` only when its layout segments every instance of it across all nine traced
segmentations with zero residual.

### `child_slots`

The class name expected in each slot, in read order. `"*"` means the slot is polymorphic and the
tag at that position decides. A trailing `"..."` entry means the slot repeats, and `repeat_count`
must then name the field holding the count.

#### A concrete slot name binds an external class by identity

A class-reference token whose index is **below** the stream's `base` names a class some earlier
stream of the same document defined. `re/solidworks/archive/EXTERNAL_CLASSES.md` §2 shows that
index is document-specific and is **not** a function of `base`: `moUnitComponent_c` is 43 in eight
traced parts and 45 in `COJINETE INFERIOR`, `suObList` moves over 82–85, `moPMarkRecord_c` over
102–106, and two donor fixtures reference `moUnitComponent_c` at 42. So the table cannot enumerate
the indices, and `external#<index>` aliases only cover the ones a trace happened to record.

The binding therefore runs off the slot, not the index. `gen_class_layouts.py` rewrites any slot
whose traced occupant resolves to one of those classes so it carries the **class name** rather than
the alias — `moCompFeature_c.child_slots` is `["moUnitComponent_c"]`, not `["*"]` or
`["external#43"]`. When `segment()` meets a class reference below `base` that no
`external#<index>` entry names, it takes the layout of the class the slot declares. That is the
class the parent's decompiled `Serialize` is recorded to read at that position, so the resolution
is by identity and holds at any index.

Three constraints keep it sound:

* A slot is bound only when **every** traced occupant of it resolves to the same class. A slot with
  two different resolved occupants stays `"*"`.
* A slot at or past a repeated template is left alone, because rewriting it would move
  `template_slot` and change the child count arithmetic.
* A `"*"` slot binds nothing. An unknown below-base index in a polymorphic slot is still refused
  with `no layout entry recorded for this class`, because nothing names what it holds.

## Deriving the map base

`base` is the `su_CArchive` map counter `Contents/Config-0-ResolvedFeatures` starts at, which is
the final counter of `Contents/Config-0`. It is not in the stream. `109 + feature_count - 1` fits
the traced `boss1..boss4` family but is **refuted** as a rule: a revolve feature adds one counter
unit to `Config-0` (`boss_disjoint_revolve`, `boss_revcut` and `arcboss_cut_cut_cut_through_rev`
sit one above it), a mid-plane end condition removes one (`boss_midplane` sits one below), and the
extra document metadata of `arcboss_cut_cut_cut_through_rev_meta` puts its base at **337**.

`resolve_base()` in `src/convert/adapters/solidworks/archive.py` therefore treats that expression
as a **seed** and refines it against the stream. When the walk stops on a class reference at or
above the trial base that no definition has produced, the counter offset of every definition
already reached is known, so `reference index - offset` enumerates the bases that would resolve
that reference. Each is walked in turn and the base reaching the most objects wins;
`BaseResolution` records the seed, the candidates tried, the candidates the refinement implied, and
whether the winner came from the seed or from a refinement.

Only class-reference failures feed the refinement. An object-reference index at or above the base
is, in these streams, a payload word a mis-parse walked into — the `18000` generation word and the
tree ids — and it yields no candidate that any fixture needs.

### `runs`

Constant run lengths in bytes, keyed as above. Copy these from `solve_runs.py` output rather than
re-deriving them by hand.

### `runs_by_version`

Some runs are constant within one document generation and a different constant in another,
because `Serialize` gates a field on the document version that `su_CArchive` carries for the whole
stream. `runs_by_version` records that:

```json
"moCompFeature_c": {
  "confidence": "confirmed",
  "child_slots": ["*"],
  "runs": { "lead": 0 },
  "runs_by_version": { "0": { "0": 85 }, "18000": { "0": 89 } }
}
```

Each key is a **minimum document version**, written as a decimal string, and each value is a run
map keyed exactly like `runs`. For a stream of version `V` the applicable gate is the one with the
greatest key `<= V`; the keys that gate names override `runs`, and every other key falls through to
`runs`. A `"0"` gate is therefore the default, because every document version is non-negative. When
no gate is `<= V`, only `runs` applies, and a run that neither `runs` nor the selected gate names is
refused with the version in the message rather than guessed.

Gates must be non-negative, unique and non-empty, and may only name keys the class actually has.
`runs` stays the place for a length that does not depend on the generation, so a class normally
carries both.

The version is a property of the stream, not of the bytes inside a run, and that is the point. A
positional `conditional` rule cannot express a length difference that sits inside the run whose
length is being computed, because the predicate's own offset would depend on the answer. The
document version is uniform per stream and known before segmentation starts, so it is the only
sound discriminator for this shape.

#### Where the version comes from

`document_version()` in `src/convert/adapters/solidworks/archive.py` reads it from the container's
storage names: a `.SLDPRT` carries `_MO_VERSION_<n>/Biography`, `_MO_VERSION_<n>/History` and
friends, and `<n>` is the modelling-object serialization generation. The highest `<n>` present
wins. That is preferred over `swXmlContents/Features` `swVersion`, which agrees on all nine traced
parts but is an optional XML side-car rather than part of the container's own structure. When no
`_MO_VERSION_*` storage is present the caller's `default` applies, and the shipped default is
`DEFAULT_DOCUMENT_VERSION = 18000`, the generation Kit itself authors.

`segment()`, `verify()` and `build_model()` all take `version` as a keyword with that default, and
`VerifyReport.version` records which one a report was produced with.

### `variable_runs`

One entry per run that is not a constant. `rule` is one of:

| rule | body |
|---|---|
| `string` | `ff fe ff <u8 units>` then `units` UTF-16LE code units, or `ff fe ff ff <u16 units>` for `units >= 255` |
| `count` | a `u16`/`u32` at `at`, then `stride` bytes per element |
| `conditional` | present only when the field named by `predicate` holds one of `values` |
| `opaque` | length known only from a trace; the segmenter must refuse rather than guess |

`opaque` is legitimate and must be used rather than a guess. A wrong length silently mis-segments
the whole remainder of the stream.

### `fields`

Only fields that are actually needed to author or to decode. Each carries a `role`:

| role | meaning | writer behaviour |
|---|---|---|
| `authored` | a real user parameter | write it |
| `derived` | a cache recomputed by the reader | leave stale or absent, **never** synthesise |
| `constant` | the same in every observed instance | write the recorded literal |
| `uninitialised` | vendor memory the application serialises without setting | write the recorded literal, and say so |

The `derived` and `uninitialised` roles are load-bearing. `re/solidworks/README.md` records that
writing derived depth copies with a plausible-but-wrong sign rule produced zero bodies, a crash,
and one silently wrong volume; and that `getCapEnd(0)` reads `1348739666` and `getDelInitFace()`
`1168530297` out of uninitialised memory.

## Acceptance

`class_layouts.json` is correct when the static segmenter, driven by it alone, segments every one
of the recorded `.SLDPRT` resolved-features streams so that the segmentation tiles with zero gaps
and the symbolic model re-emits each stream **byte-identically**. That is the same acceptance test
`re/solidworks/archive/SEGMENTATION.md` used for the runtime segmentation, and it is the only
check that matters — a layout that decodes without tiling is not evidence.
