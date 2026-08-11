<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Six-line blind pad ResolvedFeatures closure

## Scope

The 12,283-byte `Contents/Config-0-ResolvedFeatures` family for one closed,
simple, six-line sketch on the Front Plane followed by one blind boss extrusion
is closed. The production program is
`src/convert/adapters/solidworks/resolved_polyline6_program.py`.

The program contains no recorded byte span. It emits archive definitions,
class references, object references, nulls, strings, primitive fields, and
direct counted arrays from typed values. Runtime conversion does not read the
controlled files or invoke SOLIDWORKS, COM, FreeCAD, or any vendor library.

## Controlled inputs

Three independently authored streams have the same 12,283-byte topology:

| Input                       | Polygon vertices in millimetres                   | Depth | SHA-256                                                            |
| --------------------------- | ------------------------------------------------- | ----: | ------------------------------------------------------------------ |
| `gate_polyline6.SLDPRT`     | `(-20,-20) (20,-20) (20,0) (0,0) (0,20) (-20,20)` | 10 mm | `b973bd5326bbdb65b8e8b5e8345e0bdbdef20d345bf70d9f7562e5a74077bfb4` |
| `poly6_boss/resolved.bin`   | `(0,0) (40,0) (40,10) (15,10) (15,25) (0,25)`     |  8 mm | `15aae63fc17f217b64fc8d71e31548fbebdb6fc9e9fa4cae6212336bc194603b` |
| patched `poly6_boss.SLDPRT` | the preceding polygon scaled by 1.1               | 11 mm | `e8d6da539be20ac805cb0b840f74d1a2473e7a0fc5b93883df3ce7a5e2644ef3` |

The original and patched donor differential changes only the unique vertex
coordinates and the extrusion depth. The gate differential independently
changes every coordinate lane.

## Native-reader traces

The guarded primitive trace was restricted to a stream span of 12,283 bytes
and produced 3,567 native archive reads. The independent `ReadObject` trace
produced these structural totals:

| Measurement        | Result |
| ------------------ | -----: |
| Stream bytes       | 12,283 |
| Objects            |    380 |
| Class definitions  |     45 |
| Initial map index  |    109 |
| Counter mismatches |      0 |
| Gaps               |      0 |
| Overlaps           |      0 |
| Trailing bytes     |      0 |

Combining the traces yields 3,022 typed operations owned by 516 distinct
serializer callsites. Generation reports zero missing bytes. `EncodeProgram()`
reproduces the gate stream byte for byte, while `PadFieldMap()` plus the donor
polygon and 8 mm depth reproduces the independently tracked donor stream byte
for byte.

## Semantic fields

Coordinates are IEEE-754 doubles in metres written by
`sldmgu!mgPoint_c::restore2D`. Each vertex appears once because the closed
chain links the sixth endpoint back to the first handle.

| Meaning     | Byte offset |
| ----------- | ----------: |
| vertex 1 x  |        6119 |
| vertex 1 y  |        6127 |
| vertex 2 x  |        6297 |
| vertex 2 y  |        6305 |
| vertex 3 x  |        6924 |
| vertex 3 y  |        6932 |
| vertex 4 x  |        7086 |
| vertex 4 y  |        7094 |
| vertex 5 x  |        7248 |
| vertex 5 y  |        7256 |
| vertex 6 x  |        7410 |
| vertex 6 y  |        7418 |
| blind depth |       11090 |

The depth is an IEEE-754 double in metres written by
`SLDMODU!moVectorParameter_c::GetThisClass+0x7c8`. `PadFieldMap()` rejects a
non-six-line profile, non-finite coordinates, repeated vertices, intersecting
edges, zero area, and a non-positive depth before emitting target bytes.

## Live SOLIDWORKS proof

The typed stream was combined with the existing fully first-principles native
single-pad envelope, with `DisplayLists` and `Config-0-Partition` omitted. No
stream came from the polyline oracle. The resulting file opened in SOLIDWORKS
33.5.0 with no load errors or warnings and rebuilt successfully.

| Check             | Result                                                        |
| ----------------- | ------------------------------------------------------------- |
| Bodies            | 1                                                             |
| Volume            | 12,000.000000000004 mm³                                       |
| Surface area      | 4,000.0 mm²                                                   |
| Centre of mass    | `(-3.3333333333333326, -3.3333333333333326, 5.0)` mm          |
| Parametric nodes  | `Sketch1` as `ProfileFeature`; `Boss-Extrude1` as `Extrusion` |
| Driving dimension | `D1@Boss-Extrude1 = 10.0 mm`                                  |

The same first-principles file was opened again and its live
`D1@Boss-Extrude1` dimension was changed to 14 mm. The rebuild succeeded with
one body, volume 16,800.0 mm³, and centre of mass
`(-3.3333333333333335, -3.3333333333333335, 7.0)` mm. A directly emitted 12 mm
depth variant also opened and rebuilt to 14,400.000000000004 mm³ with its
driving dimension reported as 12 mm.

The feature tree also retained the standard folders, Front Plane, Top Plane,
Right Plane, Origin, Sketch1, and Boss-Extrude1. All CAD processes were closed
after the isolated oracle run.

## Production integration

The first-principles writer now recognizes one `PartDesign::Pad` whose profile
is exactly six connected line segments forming a closed simple polygon on the
canonical XY/Front Plane. It preserves source vertex order, passes the six
millimetre pairs and positive blind length through `PadFieldMap()`, and emits
the resulting typed program with the existing native single-pad envelope.

The reader reconstructs the six-edge graph as an ordered `polyline` profile,
so the normal write proof verifies every source vertex, the pad dependency,
feature ids 26 and 32, direction, termination, and driving depth before adding
parametric-history, editable-sketch, body-structure, and parameter
capabilities. The public FCStd writer test locks the 12,283-byte resolved hash
and confirms vendor-loadable, application-usable, near-lossless output.

Arcs, circles, open wires, intersecting wires, other segment counts, non-blind
end conditions, noncanonical support planes, reversal, and placement
transforms remain fail-closed until their own typed families are recovered.
No vendor stream or runtime CAD fallback is used.
