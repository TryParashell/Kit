<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Disjoint boss and full revolution closure record

Status: **source semantics and oracle acceptance target confirmed; first-principles stream
programs not yet recovered**. This record does not claim production support, vendor loadability,
or lossless translation for the family. No CAD application, COM automation, or debugger was
started while producing this static record.

## Exact FreeCAD source contract

The controlled source is `.rescratch/sw/fcstd/kit_boss_disjoint_revolve.FCStd`. Static inspection
of `Document.xml` proves two independent `PartDesign::Body` histories in document order:

1. `Body` contains `Sketch` and `Pad`; its tip is `Pad` and its `BaseFeature` is empty.
2. `Body001` contains `Sketch001` and `Revolution`; its tip is `Revolution` and its `BaseFeature`
   is empty.

The first sketch is attached to `XY_Plane` and contains the closed four-line rectangle
`(-30,-20) -> (30,-20) -> (30,20) -> (-30,20)` millimetres. `Pad` is a 10 mm, type-zero blind,
non-mid-plane, non-reversed extrusion in the positive Z direction.

The second sketch is attached to `XZ_Plane` and contains the closed six-line profile
`(0,170) -> (0,120) -> (2.5,120) -> (2.5,150) -> (1.5,149.99) -> (1.5,170)` millimetres.
`Revolution` is a type-zero additive 360-degree, non-mid-plane, non-reversed sweep. Its profile is
`Sketch001`, its reference is `Sketch001.V_Axis`, and its stored axis is approximately `(0,0,1)`
after the Top-plane attachment transform.

The body split is semantic, not an optimization. The pad occupies Z from 0 through 10 mm while the
revolution occupies Z from 120 through 170 mm, so the minimum axial gap is 110 mm. A writer must
retain two independent body-producing operations and must not merge, reorder across bodies, or
turn the second operation into a cut.

## Independent geometry check

The pad volume is exactly `60 * 40 * 10 = 24,000 mm3`. The revolution profile has area
`104.995 mm2` and radial centroid `1.10710827499722 mm`. Pappus's centroid theorem therefore gives
`2 * pi * 104.995 * 1.10710827499722 = 730.362696094311 mm3`. The required total is
`24,730.36269609431 mm3` with exactly two solid bodies.

The existing oracle report measured `24,730.362696094307 mm3` and two bodies after SOLIDWORKS
rebuilt the controlled part. That measurement is acceptance evidence only; production cannot read
or copy any oracle part or stream.

## Recorded stream family

The fixture below is reverse-engineering and test evidence. Its bytes are prohibited from every
production path. Static hashes agree with `tests/fixtures/solidworks/donors/manifest.json`.

| Stream                                      | Bytes  | SHA-256                                                            |
| ------------------------------------------- | -----: | ------------------------------------------------------------------ |
| `Contents/Config-0-ResolvedFeatures`        | 17,474 | `6894ccb75d456dc86322ad539c84d116651c0c6873bdaddc47719bf5211da997` |
| `Contents/Config-0`                         | 25,246 | `2139eccd2cf58fdc9da51942ee0bea54755db3cff59e4575e7d84cc46f128f57` |
| `Contents/Config-0-ModelHeader`             |  2,461 | `71ee946aaefaccd7288abcb6f9a1f148590ae1a1e1df9ea13136756ef0ea6bbb` |
| `Header2`                                   |  2,461 | `71ee946aaefaccd7288abcb6f9a1f148590ae1a1e1df9ea13136756ef0ea6bbb` |
| `Contents/Definition`                       |  3,810 | `9ef7791e99859010fb2f1568181284d79c06d27dc95109b759ff654574ba6494` |
| `Contents/CMgr`                             |  2,019 | `1876165797a42f027b02a7f1133d7a4e09817e32b1cb940f252c580ffc20e45a` |

The resolved metadata identifies sketches 26 and 33, features 32 and 39, names `Sketch1`,
`Boss-Extrude1`, `Sketch2`, and `Revolve1`, four and six profile points, and revolution axis
direction `(0,1)` in sketch coordinates. The resolved map base is 111, not the feature-count seed
110; a revolution contributes one additional `Config-0` counter unit for this family.

## Why existing typed programs cannot be combined

`resolved_revolve_pin_program.py` owns a 12,337-byte one-body Top-plane revolution graph.
`config0_revolve_pin_program.py` owns a 24,902-byte one-body configuration. Prefixing a pad program
or concatenating those programs cannot create the missing body chooser, action identity, object
references, map-counter state, feature stamps, bounding data, or two-body configuration graph.

`resolved_bossrevcut_program.py` is also structurally different despite having two features. It
contains `moRevCut_c`, a four-line Front-plane cut profile, sketch-axis direction `(1,0)`, and a
single subtractive body history. This source requires `moRevolution_c`, a six-line Top-plane
additive profile, direction `(0,1)`, and two independent body histories. Reusing that program would
silently change both topology and boolean semantics.

These are record-graph differences. They cannot be repaired by changing coordinates, feature
names, or operation flags in an existing stream program.

## Strict source gate for the recovered family

The eventual production selector must accept only a part document satisfying every condition
below and must fail closed on the first mismatch:

- exactly two `PartDesign::Body` objects in source order, with disjoint feature membership;
- body one is exactly one line-only, closed, four-edge rectangular sketch on the principal Front
  plane followed by one positive, blind, non-reversed, non-mid-plane pad;
- body two is exactly one line-only, closed, simple six-edge sketch on the principal Top plane
  followed by one additive, 360-degree, non-reversed, non-mid-plane revolution;
- the revolution references its own sketch `V_Axis`; the profile lies on one side of that axis,
  closes on it, and encloses positive area;
- both body placements are identity, neither feature has a base feature, and no feature is shared
  across the two bodies;
- source-space bounds prove the two generated solids are disjoint rather than relying only on body
  names or timeline order;
- the document requires no unsupported expression, selection, support-plane, surface, thin,
  offset, two-direction, or partial-angle semantics.

Within that gate, rectangle extents, pad depth, and all six revolution vertices remain authored
parameters. A correct serializer must derive every affected sketch coordinate, dimension,
bounding box, body chooser, feature stamp, and configuration field from those inputs. The
controlled coordinates above are an exact vector, not permission to hard-code geometry.

## Static reverse-engineering boundary

The latest general static walk refines the stream base from 110 to 111 and reaches 401 objects,
then stops at byte offset 13,942 when a supposed class reference 32,512 has no definition. It does
not tile or reproduce the 17,474-byte stream. An earlier layout-table attempt stopped at offset
5,889 inside an unresolved `moCompRefPlane_c` run. The current class scan still lacks closed
layouts for `AngleDim_c`, `moAngleParameter_c`, `moDisplayAngularDim_c`, `moLineRef_w`,
`moRevEndSpec_c`, and `moRevolution_c`, alongside sixteen partial shared classes.

There is no complete primitive field trace for this exact stream. The existing multi-revolution
debugger script records object and class reads for selected lengths only, and the full pin trace
targets 12,135 or 12,337 bytes rather than this 17,474-byte graph. Consequently, generating a
serializer now would require either copying the fixture or inventing unowned byte spans. Both are
forbidden.

## Bounded closure sequence after oracle-lane handoff

The following work is required before this family can be enabled:

1. Capture isolated object/class and primitive traces for resolved length `0x4442` and
   configuration length `0x629e`, with the normal clean-process controls.
2. Produce complete segment files and require zero gaps, overlaps, trailing bytes, map-counter
   mismatches, and static/runtime class disagreements.
3. Generate dedicated typed resolved and configuration programs. Every byte must be owned by an
   archive primitive, tagged object, string, or named direct field; coverage must report zero
   opaque bytes.
4. Add a dedicated envelope that derives both header copies, feature identities, stamps, combined
   bounds, and two-body configuration data. Development fixtures may be used only for byte-exact
   test comparison.
5. Add CAD-free tests for exact typed coverage, fixture equality, absence of paths and vendor
   payloads, strict-gate rejection, source-parameter propagation, decoded feature order, sketch
   axes, operation kinds, and two-body ownership.
6. Only after the programs pass those tests, integrate the strict selector and run the exclusive
   vendor gate: clean open, no warnings, successful forced rebuild, editable `Sketch1`,
   `Boss-Extrude1`, `Sketch2`, and `Revolve1`, exactly two bodies, and the analytic volume above.
7. Drive the boss depth, revolution angle, and at least one profile coordinate independently,
   rebuild after each edit, and verify both body count and analytic geometry. Restore the source
   values and require an exact return to the controlled measurement.

Until all seven steps pass, the correct production behavior is the existing explicit
`no_typed_native_feature_program` refusal. A flattened B-rep, copied oracle stream, runtime fixture
lookup, CAD launch, or COM call is not an acceptable fallback.
