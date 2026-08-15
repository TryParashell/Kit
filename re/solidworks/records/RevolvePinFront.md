<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Canonical front-plane stepped-pin revolution

## Scope and source gate

This record covers the exact full revolution represented by
`.rescratch/sw/fcstd/kit_revolve_pin_front.FCStd`. The closed sketch has six
vertices in millimetres:

```text
(0, -50), (0, 0), (2.5, 0), (2.5, -30), (1.5, -29.99), (1.5, -50)
```

The strict native-writer gate is a two-object tree with `Sketch1` as object 26
and `Revolve1` as object 31. The sketch class is `moProfileFeature_c`, its
support-plane object is 2, it has no dimensions, and its polyline must match the
six points above exactly. The revolution class is `moRevolution_c`, its sole
dimension is `D1 = 360` degrees, and its axis is the sketch vertical axis. The
source adapter representation is `XY_Plane`, `V_Axis`, `Midplane = false`, and
`Reversed = false`. Every other plane, profile, angle, axis, direction, feature
count, object identity, or dimension shape remains outside this family.

Production selection remains fail closed until the pending SOLIDWORKS live gate
passes. The typed programs and static candidate are not dispatched by
`Native.py` yet.

## First-principles stream programs

The recovered family consists of three coupled outputs:

| Output                                        |  Bytes | Typed operations | Owners | SHA-256                                                            |
| --------------------------------------------- | -----: | ---------------: | -----: | ------------------------------------------------------------------ |
| `Contents/Config-0-ResolvedFeatures`          | 12,265 |            3,005 |    503 | `2319ad19c471780a0d0b30f9108b47d5816f23cb16d9a327224b81e6afa1ec3a` |
| `Contents/Config-0`                           | 24,976 |            4,298 |  1,058 | `692fc14d4f32dd9e171d31a70b1c778eed157f1b2b62caf78bfaeae188d344d7` |
| `Contents/Config-0-ModelHeader` and `Header2` |  2,305 |   shared grammar |    n/a | `6f7bd56fa6997638046a3013475af74469a90e115ae28ee3e338431bfb14820b` |

Every byte in both object programs is emitted through a typed archive
primitive, tagged-object operation, string encoder, or named direct scalar
structure. Neither program contains an opaque byte span, a copied vendor block,
or a runtime file dependency.

The header pair is generated through the common header grammar. Its recovered
identity is `(1785928014, 106, 103, 1785928015)` and its feature-action stamps
are `((1785928015, 1785928015), (1785928015,))`. The history log references
`Part1`, while the later external object record references `Part2`; both values
are encoded as separate semantic strings. Geometry-derived bounds are:

```text
centre = (0, -0.025, 0)
maximum = (0.0025, 0, 0.0025)
minimum = (-0.0025, -0.05, -0.0025)
sphere radius = 0.025248762345905194
```

## Plane-specific structural deltas

The proven Top-plane full pin has a 12,337-byte ResolvedFeatures stream. The
front-plane stream has the same 341 traced objects and 43 class definitions but
is 72 bytes shorter. The `moCompRefPlane_c` null branch is 116 bytes for Top and
44 bytes for Front. Front sets the branch discriminator to zero and omits a
nine-double orientation basis; everything from `moRevolution_c` onward moves
back by exactly 72 bytes. The support-plane object also changes from 3 to 2.

The six coordinate pairs remain at `(6904, 6912)`, `(7066, 7074)`,
`(7228, 7236)`, `(7390, 7398)`, `(7552, 7560)`, and `(7714, 7722)`. The three
full-angle copies are doubles at 11,209, 11,723, and 11,747.

Config-0 grows from 24,902 to 24,976 bytes. Inside `moAnnotationView_c`, the
semantic view name changes from `*Front` to `*Bottom`, adding two bytes. Its
orientation discriminator changes from zero to one and adds this explicit 3 x 3
matrix, adding 72 bytes:

```text
(1, 0, 0,
 -0, -0, -1,
 0, 1, 0)
```

All later typed fields shift forward by exactly 74 bytes. The class sequence is
unchanged, and the next definition, `moPMarkRecord_c`, moves from 24,528 to
24,602.

## Trace and static evidence

The existing front-plane oracle's ResolvedFeatures trace measured 341 objects
and 43 definitions. The trace tiles all 12,265 bytes, has no map-counter
mismatches, and agrees exactly with the independent static class scan. The saved
log and segment report are `.rescratch/trace/out/cdb_trace_revolvepinfront.log`
and `.rescratch/trace/out/segments_revolvepinfront.json`.

The primitive and Config-0 debugger passes could not be launched because the
desktop sandbox denied the child debugger process and two narrowly scoped
permission requests stalled in the approval path. Static recovery therefore
used the already proven Top-plane typed grammar, the exact traced 72-byte
ResolvedFeatures conditional, and the exact 74-byte Config-0 annotation-view
conditional. Each resulting typed program re-encodes every byte of the saved
front-plane stream exactly. The model-header grammar also reproduces both saved
header copies exactly.

The donor-free static candidate is
`.rescratch/front_revolve/revolve_pin_front.firstprinciples.static.SLDPRT`. It
was assembled from a fresh current-writer Top-plane output, replacing only
ResolvedFeatures, Config-0, and the two model-header copies with the generated
front-plane programs. No vendor stream or donor byte entered the candidate.

## Pending live gate

The candidate has not been opened in SOLIDWORKS because the required isolated
oracle launch remained blocked by the sandbox. Production selection is therefore
intentionally disabled. Before integration, the candidate must open with no
errors or warnings, rebuild successfully, expose one solid body, and match the
analytic `730.3626960943112 mm3` volume and `(0, -19.83790861645004, 0) mm`
centre of mass. An independent edit of `D1@Revolve1` to 270 degrees must rebuild
to one body and change volume to approximately `547.7720220707334 mm3`; restoring
360 degrees must restore the original geometry. Independent 40 x 20 x 10 mm
controls must remain `8000 mm3` before and after the target.

The final gate must also end with a process sweep proving no SOLIDWORKS,
debugger, crash-handler, or helper process remains. CAD software and vendor
automation are oracle-only and never enter production runtime.
