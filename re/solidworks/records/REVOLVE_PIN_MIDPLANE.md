<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Canonical Top-plane midplane stepped-pin revolution

## Source contract

The focused source is
`.rescratch/sw/fcstd/kit_revolve_pin_top_midplane.FCStd`, SHA-256
`67bfacf984e8a758133d7a45c7b04e4652f64c73627f5f058cc42c1f7b097663`.
It contains one `PartDesign::Revolution` and one closed six-segment sketch on
FreeCAD's XZ principal plane, which maps to the SOLIDWORKS Top Plane. The
canonical SOLIDWORKS profile coordinates are:

```text
(0, -50), (0, 0), (2.5, 0), (2.5, -30), (1.5, -29.99), (1.5, -50)
```

The selected axis is the sketch vertical axis. The strict revolution property
set is `Angle = 360 deg`, `Angle2 = 0 deg`, `Midplane = true`,
`Reversed = false`, `Type = 0`, `AllowMultiFace = true`, `Refine = true`,
`FuseOrder = 0`, `FuzzyTolerance = -1`, `Suppressed = false`, and
`Visibility = true`, with the source label strings and every inactive default
preserved. Expressions, configuration overrides, additional features, or a
different profile fall outside this fixed family.

## Recovered midplane structure

The authored one-variable slab corpus isolates the native midplane structure:

| Case                         | ResolvedFeatures bytes | `moRevEndSpec_c` `SingleEnd` | Angular dimensions        |
| ---------------------------- | ---------------------: | ---------------------------: | ------------------------- |
| one-direction 90 degrees     |                 12,247 |                            1 | `D1 = pi/2`               |
| midplane 90 degrees          |                 13,975 |                            0 | `D1 = pi/2`, `D2 = 0`     |
| two-direction 90 plus 45 deg |                 13,975 |                            0 | `D1 = pi/2`, `D2 = pi/4`  |

For all three files, the `moRevEndSpec_c` class definition starts at offset
10,327 and its payload starts at 10,347. The first payload `u32` is the
load-authoritative `getSingleEnd()` value. The following two end-condition
fields remain zero in all three controlled files. The two 0.01-metre offset
distance defaults and both offset-reverse flags are also unchanged.

The midplane stream adds 1,728 bytes after the one-direction topology. Its
first angular value remains at offset 11,191, while the second live angular
parameter is at offset 12,943 and stores zero. A true two-direction part has
the identical record shape but stores its independently editable second angle
at that offset. Therefore a midplane revolution is a two-end native structure;
it is not an extrusion-style end-condition code and cannot be represented by
patching the one-direction angle.

The paired authored Config-0 streams are both 24,970 bytes. Their thirteen
differing bytes are object-count, identity, and action-stamp consequences of
the additional angular chain rather than a standalone midplane flag. The
model-header streams likewise differ only in their coupled identities and
stamps for this equal-bounds slab comparison. The new ResolvedFeatures
structure remains the semantic authority.

## Fail-closed baseline

`.rescratch/sw/sldprt/kit_revolve_pin_top_midplane.SLDPRT` is not a native
oracle. Its 5,556-byte ResolvedFeatures stream contains no native revolution
operation and the file retains a `Kit/ResolvedFeatures` fallback stream. The
public writer invoked with `allow_carrier=False` rejects the FCStd source with
`ApplicationUsabilityError` and the flags `application_unusable`,
`vendor_unloadable`, and `unimplemented_translation`. This is the required
behavior until the exact midplane pin streams pass the target-application
gate.

## Oracle boundary

The exact SOLIDWORKS comparison document is authored only in the isolated
oracle lane from the controlled Top-plane pin profile, a 360-degree total
angle, and the midplane end selection. Its ResolvedFeatures and Config-0
streams then receive complete object and primitive read traces. Production
modules may contain only the resulting typed archive operations and derived
header fields; they may not read or retain the oracle file or any recorded
vendor bytes.

Acceptance requires a freshly generated donor-free part to open without
errors or warnings, rebuild with one body and the exact stepped-pin mass
properties, expose `Sketch1`, `Revolve1`, and both native angular structures,
and respond to an independent `D1@Revolve1` edit while preserving the symmetric
two-end state. CAD software and COM automation remain oracle-only and never
participate in runtime conversion.

## Current verification state

The isolated oracle trace completed through the approved test boundary. The
authored part saved with zero errors and warnings, rebuilt with one body, and
reported volume `730.3626960943111 mm3`, surface area
`699.0992415061602 mm2`, and centre of mass
`(-9.963833449046765e-18, -8.766927659836491e-34, 19.83790861645004) mm`.
Its feature tree contains `Sketch1` and `Revolve1`.

The 14,065-byte ResolvedFeatures trace contains 373 archive objects, 43 class
definitions, base map index 109, and 3,951 primitive markers. The 24,902-byte
Config-0 trace contains 123 archive objects, 39 class definitions, base map
index 4, and 6,300 primitive markers. Both streams tile from byte zero to their
exact ends with no gaps, overlaps, trailing bytes, or counter mismatches. Their
decoded object models re-emit byte identically.

The generated typed programs account for all 14,065 ResolvedFeatures bytes in
3,374 operations owned by 506 traced native call sites, and all 24,902 Config-0
bytes in 4,297 operations owned by 1,058 call sites. Their SHA-256 digests are
`bffc7d98b6ed899d79deff6b71772454cb94c1c45d8ace10a167022f154f179e` and
`f2dc3d440fb6ac956155e5d300c15e83a8574311c9e58802b514af486d448341`
respectively. The family model header is 2,305 bytes with SHA-256
`4cb455532120074010565342eab6df3b83df1bf45ad0c25bf391664790de07ca`.
All three typed emissions are byte identical to the authored oracle streams.

The exact family stream stores `SingleEnd = 0` at offset 10,437. The synchronized
`D1 = 2*pi` values are at offsets 11,281, 11,795, and 11,819; the synchronized
`D2 = 0` values are at 13,033, 13,547, and 13,571. The model-header identity is
`(1786487434, 106, 103, 1786487442)`, with sketch action stamps
`(1786487441, 1786487442)` and revolution action stamp `1786487442`.

The new serializers and coupled envelope contain no oracle path, donor block,
or opaque byte range. The public writer remains deliberately fail-closed until
the production dispatcher consumes this family and a freshly generated file
passes the independent in-application `D1@Revolve1` edit and restore gate. The
trace harness completed its final sweep, and an independent process query found
no SOLIDWORKS, cdb, crash-handler, or helper process.
