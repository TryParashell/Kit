<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Canonical 90-degree stepped-pin revolution

## Scope

This record covers the exact one-direction 90-degree revolution represented by
`.rescratch/sw/fcstd/kit_revolve_pin_top_90.FCStd`. The Top Plane sketch is the closed
six-vertex profile below, expressed in millimetres after mapping FreeCAD's XZ sketch into
the SOLIDWORKS Top Plane coordinate system:

```text
(0, -50), (0, 0), (2.5, 0), (2.5, -30), (1.5, -29.99), (1.5, -50)
```

The revolution uses the sketch vertical axis and stores a single editable angular
parameter, `D1@Revolve1 = pi/2` radians. This is a fixed recovered topology family. Other
angles remain unsupported as direct writer inputs until their own topology gates pass,
although SOLIDWORKS can edit and rebuild the emitted native parameter after loading.

## First-principles stream programs

The recovered family consists of three coupled outputs:

| Output                                        |      Bytes |      Typed operations | Owners | SHA-256                                                            |
| --------------------------------------------- | ---------: | --------------------: | -----: | ------------------------------------------------------------------ |
| `Contents/Config-0-ResolvedFeatures`          |     12,537 |                 3,073 |    506 | `cd1ef9071450bacb44a54efc92b5e3b1d2a778504b5124e942e79fbfba5de8d4` |
| `Contents/Config-0`                           |     24,902 |                 4,297 |  1,058 | `4a09091e5f03e9c8f617da241f1e0a71d5e43f64f84889067a2e520ac5c91f76` |
| `Contents/Config-0-ModelHeader` and `Header2` | 2,305 each | shared header grammar |    n/a | `9d146ad95cacd429338ca34ba74acb4b725ae8bce2c4d3018e99e3fcd4873880` |

Every byte in both binary object programs is emitted through a typed archive primitive,
tagged-object operation, string encoder, or named direct scalar structure. Neither program
contains an opaque byte span, a copied vendor block, or a runtime file dependency.

The model-header copies are generated through the common header grammar. Their recovered
identity is `(1786479979, 106, 103, 1786479985)`, their feature stamps are
`((1786479985, 1786479985), (1786479985,))`, and their geometry-derived bounds are:

```text
centre = (0.00125, 0.00125, 0.025)
maximum = (0.0025, 0.0025, 0.05)
minimum = (0, 0, 0)
sphere radius = 0.025062422069704278
```

The header pair is load-critical. Pairing the partial ResolvedFeatures and Config-0
programs with the full-revolution header deserializes `Sketch1`, `Revolve1`, and `D1`, but
SOLIDWORKS refuses the rebuild and produces no body. Replacing only both header copies with
the recovered partial header makes the file rebuild. Adding partial CMgr, Partition,
ModelStamps, or Definition streams does not change that result and is unnecessary.

## ResolvedFeatures topology delta

The full stepped pin contains 12,337 ResolvedFeatures bytes, 341 traced objects, and 43
class definitions. The 90-degree pin contains 12,537 bytes, 371 traced objects, and 44
class definitions. Both traces tile their complete stream and have zero archive map-counter
mismatches.

The 200-byte increase is not a newly introduced angular dimension: both full and partial
families already contain `moDisplayAngularDim_c`, `AngleDim_c`, and
`moAngleParameter_c`. The partial topology introduces `moEndFaceSurfIdRep_c` and records
four end-face identity objects across the two `moFaceRef_c` buckets. It also expands the
from-sketch surface identities from six to ten traced objects. The downstream
`moBBoxCenterData_c`, `moRevEndSpec_c`, display dimension, angle parameter, and favorite
handle therefore move by 200 bytes.

The six editable sketch coordinate pairs begin at offsets `(6904, 6912)`, `(7066, 7074)`,
`(7228, 7236)`, `(7390, 7398)`, `(7552, 7560)`, and `(7714, 7722)`. The angular parameter
and its favorite-handle copy are doubles at offsets 11,481 and 12,019. Both store exactly
`pi/2` in the canonical program.

## Trace evidence

The authored oracle had one valid solid with volume `182.59067402357778 mm3`. The object
trace measured 371 objects and 44 definitions in ResolvedFeatures, with exact static/runtime
class agreement, complete tiling, and no counter mismatches. The primitive trace recorded
3,615 reads and left no byte uncovered.

Config-0 separately measured 123 objects and 39 definitions, complete tiling, exact object
re-emission, and no counter mismatches. Its primitive trace recorded 6,297 reads. The fixed
field partition is the already proven stepped-pin Config-0 grammar; the partial oracle
supplies its independently decoded typed values. Every operation re-encodes its source
field exactly before source generation is accepted.

Relevant research artifacts are under `.rescratch/partial_revolve/` and
`.rescratch/trace/out/segments_revolvepin90*.json`. They are oracle evidence only and are
not production inputs.

## SOLIDWORKS gate

The final test file was assembled from the repository's current first-principles full-pin
writer output, replacing only the three coupled generated outputs named above. No vendor
stream or donor byte entered the file.

SOLIDWORKS 33.5 opened it with no errors or warnings and `ForceRebuild3(False)` returned
true. The tree contained editable `Sketch1` and `Revolve1`; the part had one solid body,
volume `182.59067402357778 mm3`, surface area `384.76481037653997 mm2`, and centre of mass
`(0.9788721007929848, 0.9788721007929848, 19.83790861645004) mm`.

Driving `D1@Revolve1` in memory to 120 degrees rebuilt successfully, retained one body, and
produced volume `243.4542320314369 mm3`. Restoring 90 degrees rebuilt successfully and
returned the exact original volume and centre of mass. Independent 40 x 20 x 10 mm controls
before and after the target both rebuilt to one body and `8000.000000000001 mm3`, ruling out
session contamination.

The CAD application, COM automation, and debugger were used only for the isolated oracle
authoring, trace, and verification lane. Production emission remains pure Python with no CAD
software or vendor automation at runtime. The final process sweep found no SOLIDWORKS,
debugger, crash-handler, or helper process.
