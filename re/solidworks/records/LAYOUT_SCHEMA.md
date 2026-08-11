<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

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
because their bodies carry a string, a count-driven array, a conditional field, or a chain of
counted loops:

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

| key            | meaning                                                                                                                                                          |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lead`         | bytes from the end of the object's own tag to the start of child 0                                                                                               |
| `<i>`          | bytes from the end of child `i` to the start of child `i+1`, or to the end of the body for the last child                                                        |
| `leaf`         | the whole body, for a class that never has children                                                                                                              |
| `tail`         | bytes from the end of the last child the segmenter is allowed to walk to whatever follows it, for a class whose child count is not resolved; see `repeat_prefix` |
| `<group name>` | the run key a class driven by `groups` reports, naming the group that failed rather than a slot index; see `groups`                                              |

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
`Serialize` _and_ the byte arithmetic reproduces a real traced span, a real corpus record or a
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

- A slot is bound only when **every** traced occupant of it resolves to the same class. A slot with
  two different resolved occupants stays `"*"`.
- A slot at or past a repeated template is left alone, because rewriting it would move
  `template_slot` and change the child count arithmetic.
- A `"*"` slot binds nothing. An unknown below-base index in a polymorphic slot is still refused
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

### `repeat_count` and `repeat_prefix`

A trailing `"..."` in `child_slots` says the child count varies across the traced instances.
`repeat_count` closes it when a field holding the count has been recovered:

```json
"suObList": {
  "child_slots": ["*", "..."],
  "runs": { "lead": 2, "0": 0 },
  "repeat_count": { "run": "lead", "at": 0, "width": 2 }
}
```

`repeat_count` is `null` when no such field has been found. The segmenter never guesses the count,
but refusing the whole class is more pessimistic than the evidence requires: the leading child
slots that **every** traced instance fills are known, and so are the runs between them. That is
what `repeat_prefix` records.

```json
"moFaceRef_c": {
  "child_slots": ["*", "*", "*", "*", "*", "*", "*", "..."],
  "runs": { "lead": 36, "0": 0, "1": 0, "2": 0 },
  "repeat_count": null,
  "repeat_prefix": 4,
  "variable_runs": [{ "slot": "tail", "rule": "opaque", "note": "..." }]
}
```

`repeat_prefix` is the smallest child count any traced instance of the class holds, so slots `0`
through `repeat_prefix - 1` are present in every instance and the runs `0` through
`repeat_prefix - 2` are solved from every instance rather than from a subset. The segmenter walks
exactly that prefix, then asks for the `tail` run instead of the run key the slot index would
name. `tail` is normally absent or `opaque`, so the walk stops there with the class and its own
offset in the error, and the objects before the prefix ends are reached instead of lost. The
generator derives `repeat_prefix` for every class it leaves with a null `repeat_count`, and drops
any `variable_runs` entry for a slot past the prefix because those runs are never consulted.

`repeat_prefix` is a floor on the arity of the class, not a claim about it. It is only sound
because the run after the last prefix child is refused: the class is never asserted to end there,
and a document whose instance is shorter than every traced one is the one case it does not cover,
which is why the tail is refused rather than measured.

`repeat_prefix` must be `0` for a class whose child count is already resolved, and must not exceed
the number of declared child slots.

### `groups`

`child_slots` plus `repeat_count` covers a class whose body is a fixed slot list, optionally with
**one** repeated template at the end. It cannot express a body that is a _chain_ of independent
counted loops, each with its own count, its own multi-child element and its own trailing filler.
`sgSketch` is that shape, and `groups` records it.

```json
"sgSketch": {
  "child_slots": [],
  "runs": { "lead": 49 },
  "groups": [
    {
      "name": "entity",
      "count": { "back": 49, "width": 2 },
      "slots": ["*", "*", "*", "*"],
      "element": [8, 39, 0, 87],
      "trailer": 4
    },
    {
      "name": "relation",
      "count": { "back": 6, "width": 2 },
      "slots": ["*", "*", "*", "*"],
      "element": [0, 16, 17, 4],
      "element_by_version": { "14000": [0, 16, 16, 4], "18000": [0, 16, 17, 4] },
      "trailer": 2
    },
    {
      "name": "lists",
      "repeat": 1,
      "slots": ["suObList", "suObList"],
      "element": [170, 38],
      "trailer": 0
    }
  ]
}
```

A class with `groups` has no `child_slots`, no `repeat_count` and no `repeat_prefix`: the group
chain is the whole child list. It still carries a `lead` run, because the lead is read before the
first group opens and is often where the first count sits.

| key                  | meaning                                                                                                                                 |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `name`               | the group's identifier; it is the run key the segmenter reports when a group fails                                                      |
| `element`            | one run length per child of a single iteration, in read order; the run is the bytes from the end of that child to the start of the next |
| `slots`              | the class expected in each element child, exactly as `child_slots` does it, one entry per `element` entry; `"*"` for a polymorphic slot |
| `count`              | `back` bytes ahead of the group's first element sits a `width` byte little-endian count of iterations                                   |
| `repeat`             | a constant iteration count, for a group whose children are unconditional rather than counted                                            |
| `trailer`            | bytes consumed after the last iteration, before the next group's first element                                                          |
| `element_by_version` | per document version `element` overrides, keyed exactly like `runs_by_version`                                                          |

The walk is:

```
cursor = end of the lead run
for each group:
    count = repeat, or the width byte scalar at cursor - back
    repeat count times:
        for each element run:
            read the tag at cursor, walk that child, then skip the run
    cursor += trailer
the object ends at cursor when every group is exhausted
```

Two consequences of that order are load-bearing.

`count` is read **backwards** from the group's own start, not forwards from a run of the parent.
That is the only expressible form, because the count physically precedes the loop it drives and the
number of bytes between them is fixed while the bytes ahead of it are not: they belong to the
previous group, whose length depends on its own count. `back` must therefore be at least `width`.

`trailer` is consumed **unconditionally**, including for a group whose count is zero. A group with
a zero count contributes no child and no tag, only its trailer, so the trailers of a run of empty
groups accumulate into the run that follows the last child actually read. That is exactly what the
traces show: the origin sketch of every traced part carries one entity and no points, and the run
after its last entity child measures `87 + 4 + 13` — the entity element's own run, the entity
group's trailer, and the empty point group's trailer.

Because a group with a zero count leaves no tag behind, a count field is only _witnessed_ by the
instances whose count is non-zero. `sgSketch` has six groups and the traces exercise two distinct
counts for four of them, so those four `back` offsets are pinned by a real difference; the values
themselves are recorded in each group's `note`.

`element_by_version` uses the same exact-version keying as `runs_by_version` and is only declared
for a group whose element is observed to differ between generations. `sgSketch.relation` is: its
third child carries 17 bytes at document version 18000 and 16 at 14000. `sgSketch.constraint` has
the same shape but only 18000 ever gives it a non-zero count, so it is left ungated rather than
gated by inference.

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

| rule          | body                                                                                                    |
| ------------- | ------------------------------------------------------------------------------------------------------- |
| `string`      | `ff fe ff <u8 units>` then `units` UTF-16LE code units, or `ff fe ff ff <u16 units>` for `units >= 255` |
| `count`       | a `u16`/`u32` at `at`, then `stride` bytes per element                                                  |
| `conditional` | present only when the field named by `predicate` holds one of `values`                                  |
| `opaque`      | length known only from a trace; the segmenter must refuse rather than guess                             |

`opaque` is legitimate and must be used rather than a guess. A wrong length silently mis-segments
the whole remainder of the stream.

### `fields`

Only fields that are actually needed to author or to decode. Each carries a `role`:

| role            | meaning                                                  | writer behaviour                            |
| --------------- | -------------------------------------------------------- | ------------------------------------------- |
| `authored`      | a real user parameter                                    | write it                                    |
| `derived`       | a cache recomputed by the reader                         | leave stale or absent, **never** synthesise |
| `constant`      | the same in every observed instance                      | write the recorded literal                  |
| `uninitialised` | vendor memory the application serialises without setting | write the recorded literal, and say so      |

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
