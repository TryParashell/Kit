<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Front-plane boss with rectangular and circular blind cuts

## Scope

This record covers the strict three-operation source family in
`.rescratch/gates/fcstd/gate_boss_cut_circle.FCStd`:

| Feature         | Profile                                 | Depth | Native direction |
| --------------- | --------------------------------------- | ----: | ---------------- |
| `Boss-Extrude1` | rectangle `(-30, -20)` to `(30, 20)` mm | 15 mm | reversed         |
| `Cut-Extrude1`  | rectangle `(-24, -4)` to `(24, 4)` mm   |  5 mm | forward          |
| `Cut-Extrude2`  | circle at `(0, 12)` mm, radius `6` mm   |  9 mm | forward          |

The sketches all lie on the Front Plane. The fixed topology uses object IDs 26/32,
33/40, and 41/47 for the three sketch/operation pairs. Geometry and depths are editable
native values; this record does not generalize the topology to arbitrary mixed-profile
chains.

## Typed ResolvedFeatures program

The recovered `Contents/Config-0-ResolvedFeatures` grammar is 21,021 bytes. Its 5,302
typed operations cover the entire stream through 520 native serializer call sites:

| Property           | Value                                                              |
| ------------------ | ------------------------------------------------------------------ |
| Stream bytes       | 21,021                                                             |
| Typed bytes        | 21,021                                                             |
| Opaque/donor bytes | 0                                                                  |
| Traced objects     | 734                                                                |
| Class definitions  | 46                                                                 |
| Counter mismatches | 0                                                                  |
| Reference SHA-256  | `ea2e72fee693b357d6ccea3aac0f9a64a428f5b851aff0d77faf422491d939a6` |

Every byte is emitted by a tagged archive operation, typed primitive, string encoder, or
named direct scalar structure. The program has no runtime file read, fixture path, encoded
vendor block, or opaque fallback. Semantic patching updates all six copies of each depth,
both rectangle corner chains, the circle centre and radius, end-condition codes, and the
three direction fields.

The source-specific direction tuple is `(true, false, false)`. This is load-critical
operation semantics, not envelope metadata: the reversed boss occupies negative Z, so both
cuts must use the opposite direction to intersect it. The initially tested
`(true, true, true)` tuple exposed all three features and dimensions but left both cuts
pointing away from the body. SOLIDWORKS consequently retained the uncut `36,000 mm3` boss,
returned a failed rebuild, and did not change geometry when either cut depth was edited.

## Envelope isolation

The first-principles generic Config-0, model-header, CMgr, Definition, and metadata
generators are sufficient for this family. A scratch-only substitution matrix replaced
Config-0, both model-header copies, and CMgr/CMgrHdr2 separately and in all combinations;
all seven candidates remained inert while the incorrect direction tuple was present.
Changing only the typed directions to `(true, false, false)` on the original donor-free
envelope produced a clean rebuild and exact geometry. No family-specific Config-0,
ModelHeader, CMgr, Partition, LWDATA, display-list, or cache stream is required.

The repository path `.rescratch/gates/sldprt/gate_boss_cut_circle.SLDPRT` is not a usable
SOLIDWORKS oracle: SOLIDWORKS 33.5 terminated its automation server while opening that file.
The alternate `.rescratch/donor_out/kit_boss_cut_circle_poly.SLDPRT` is a different
four-operation topology. Neither file is a production input. The recovered 21,021-byte
program was traced from the healthy matching three-operation archive grammar, and the exact
source result was validated from the donor-free writer output.

## SOLIDWORKS gate

SOLIDWORKS 33.5 opened the direction-corrected first-principles file with no errors or
warnings. `ForceRebuild3(False)` returned true. The tree contained editable `Sketch1`,
`Boss-Extrude1`, `Sketch2`, `Cut-Extrude1`, `Sketch3`, and `Cut-Extrude2`; the part had one
solid body with:

```text
volume = 33062.12398023691 mm3
surface area = 8699.292006587699 mm2
centre of mass = (-4.2532265688094214e-16,
                  -0.3694412447445422,
                  -7.8827227817200445) mm
```

The restored public `write_document(..., allow_carrier=False)` path emits the same 24
first-principles streams. Its vendor-critical streams are byte-identical to this live-gated
file; only the Parashell `Kit/Native` neutral metadata differs.

The volume independently equals
`60*40*15 - 48*8*5 - pi*6^2*9`. Each depth was then edited from a fresh open:

| Edit                       | Rebuilt | Bodies | Volume after edit        |
| -------------------------- | ------- | -----: | ------------------------ |
| `D1@Boss-Extrude1 = 18 mm` | yes     |      1 | `40262.12398023691 mm3`  |
| `D1@Cut-Extrude1 = 7 mm`   | yes     |      1 | `32294.123980236905 mm3` |
| `D1@Cut-Extrude2 = 12 mm`  | yes     |      1 | `32722.831973649205 mm3` |

The exact analytic change for each edit proves that both native cuts participate in the
body rather than appearing only as inert tree records or cached geometry. A known-good
control opened, rebuilt, and measured one body at `881814.3482038013 mm3` before and after
the sequence.

SOLIDWORKS, COM automation, and the debugger were used only in isolated oracle sessions.
The production converter and every emitted stream remain pure Python with no CAD software
or vendor automation at runtime. The final process sweep found no SOLIDWORKS, debugger,
crash-handler, or helper process.
