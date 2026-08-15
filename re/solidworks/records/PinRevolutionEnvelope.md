<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Stepped pin revolution envelope

## Acceptance result

The source-free top-plane stepped pin now has a complete first-principles envelope. SOLIDWORKS
2025 SP5 opened the generated part with no load errors, rebuilt it, exposed one solid body, and
reported `730.3626960943111 mm3`. The live tree contained `Sketch1` as `ProfileFeature` and
`Revolve1` as `Revolution` after the standard document folders and reference geometry.

The parametric test drove `D1@Revolve1` from 360 to 270 degrees and rebuilt successfully. The
result retained one body and changed volume to `547.7720220707334 mm3`, exactly three quarters of
the full-revolution volume. The parameter read back as `4.71238898038469` radians. Controls before
and after both rebuilt to one body and `8000.000000000001 mm3`.

No CAD application, COM API, debugger, vendor SDK, or oracle artifact participates in runtime
conversion. The oracle was invoked only after the output bytes already existed.

## Why the 24,902-byte stream differed

The earlier 25,212-byte generic `Contents/Config-0` was structurally valid but belonged to a
different one-feature history. Ordinary byte comparison hid three coupled record changes because
their shifts cancel at later offsets:

| record               | generic bytes | pin bytes | delta |
| -------------------- | ------------: | --------: | ----: |
| `moAtom_c`           |           112 |       144 |   +32 |
| `moAnnotationView_c` |           324 |       256 |   -68 |
| `moCThreadRefMgr_c`  |           332 |        58 |  -274 |
| complete stream      |        25,212 |    24,902 |  -310 |

Everything between those records retains the same typed grammar and moves by the accumulated
delta. The expanded atom moves `moRelMgr_c` and all later records forward 32 bytes. The compact
annotation moves `moPMarkRecord_c` back 68 bytes, and the compact thread manager moves
`moPrtExplViewManager_c` back another 274 bytes.

The bounded structural trace found 123 `ReadObject` calls after the root class, 40 definitions
including the root, archive map base 4, perfect stream tiling, and zero map-counter mismatches. The
bounded primitive trace recorded 6,299 reader observations. Removing overlapping aliases and
combining strings and direct compound fields produced 4,297 ordered typed operations owned by
1,058 distinct reader or serializer callsites. Their widths close exactly at byte 24,902 with no
gap, opaque span, residual span, donor block, or copied vendor bytes.

`EncodeConfig()` reproduces the controlled oracle exactly with SHA-256
`f5409831ddedb4c2c396e4b9485dc114acaf0d277e763edf35ac5daca1f0faf9`.

## ModelHeader closure

No new ModelHeader byte grammar was missing. The shared typed `_header_payload` grammar becomes
byte exact when supplied the recovered pin semantics:

- identity values `(1785928009, 106, 103, 1785928014)` for the controlled vector;
- sketch stamps `(1785928014, 1785928014)`;
- revolution stamp `(1785928014,)`;
- objects `(26, Sketch1, modified)` and `(31, Revolve1, created)`;
- next object id 32;
- the calculated ten-double bounds below.

The resulting 2,305-byte `Contents/Config-0-ModelHeader` and byte-identical `Header2` reproduce
SHA-256 `36335512255914fd6c84f47bb315368dfba48ab66dbee8b5c5195361f36f7d60`.

The bounds are calculated from the profile rather than copied from a saved file:

```text
centre  = (0, 0, 0.025)
maximum = (0.0025, 0.0025, 0.05)
minimum = (-0.0025, -0.0025, 0)
radius  = 0.025248762345905198
```

The radius is the distance from the box centre to a three-dimensional box corner, so both radial
axes contribute: `sqrt(axial_half_span^2 + 2 * radial_extent^2)`.

## Integration contract

Production integration uses `Envelope.py` as follows:

- `BuildEnvelope()` returns the coupled configuration payload, header payload, bounds, stamps, and
  creation identity as one immutable carrier;
- `EncodeConfig()` supplies `Contents/Config-0`;
- `EncodeHeader()` supplies both `Contents/Config-0-ModelHeader` and `Header2`;
- `CalcPinBounds(points_mm)` supplies `HeaderBounds` to the shared ModelHeader writer;
- `KHeaderStamps` supplies the two authored feature action histories;
- `resolved_revolve_pin_program.EncodeProgram()` supplies
  `Contents/Config-0-ResolvedFeatures`;
- the existing typed `CMgr`, `Definition`, container, and 577-byte calculated blank Partition remain
  unchanged.

The successful live candidate used `KHeaderUser = "odin"` and all four controlled identity fields
from `KHeaderIdentity`; it did not use the generic `user_name = "Kit"` header or retain generic
modified, baseline, and header identities. Consequently the existing `_VendorResolved` fields
`HeaderCreation`, `HeaderBounds`, `header_stamps`, and `Config0Payload` alone are not the measured
gate. Production now passes `BuildEnvelope().HeaderPayload` through `_VendorResolved` as an exact
typed override for both header streams. Substituting only `HeaderCreation` would be an unverified
weakening of the accepted envelope.

The public `write_document` path dispatches this program only after source validation and then
decodes the emitted profile, angle, axis binding, object identities, configuration, and both header
streams. The controlled FCStd reports `vendor_loadable`, `application_usable`, and `near_lossless`
as true with B-rep, parameters, history, editable sketches, body structure, selections, and support
planes all proven native.

The safe source gate is deliberately narrow: one closed six-line `PartDesign::Revolution` profile,
Top plane support, vertical sketch axis, a positive finite 360-degree angle, object ids 26 and 31,
and the canonical ordered points `(0,-50)`, `(0,0)`, `(2.5,0)`, `(2.5,-30)`, `(1.5,-29.99)`, and
`(1.5,-50)` millimetres. Anything outside that recovered family must remain unsupported until its
own typed program and live gate pass.

## Cache and warning boundary

The first-principles pass has one load-warning bit, `drawing-sheet-in-viewonly`. It is nonfatal:
there are no load errors, rebuild succeeds, the body and mass properties are correct, and the
driving dimension changes the body. The same bit is observed on other accepted native parts and
assemblies.

`Config-0-LWDATA`, `DisplayLists`, and `GhostPartition` are not required for load, rebuild, body
generation, feature editability, or parametric regeneration. Earlier primitive-reader ablation
recorded zero LWDATA reads. Adding saved cache streams can suppress the warning, but those bytes are
display caches rather than model authority and cannot enter production without first-principles
grammar. The accepted writer therefore emits no donor cache bytes and keeps the calculated blank
Partition; the warning boundary is explicit rather than hidden by opaque vendor data.
