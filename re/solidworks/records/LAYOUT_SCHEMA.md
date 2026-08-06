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

### `runs`

Constant run lengths in bytes, keyed as above. Copy these from `solve_runs.py` output rather than
re-deriving them by hand.

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
