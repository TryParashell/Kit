<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# FCStd feature corpus closure

## Top plane stepped pin revolution

The controlled source is one `PartDesign::Revolution` on the XZ support plane. Its sketch is a
closed chain of six lines with six coincidence constraints, the vertical sketch axis is selected,
and the angle is 360 degrees. The canonical profile points in SOLIDWORKS Top-plane coordinates are
`(0,-50)`, `(0,0)`, `(2.5,0)`, `(2.5,-30)`, `(1.5,-29.99)`, and `(1.5,-50)` millimetres.

Two bounded debugger traces recovered the 12,337-byte `Config-0-ResolvedFeatures` stream. The
structural trace contains 341 object operations and 43 class definitions. The primitive trace and
structural records produce 3,014 typed operations owned by 503 recovered reader or serializer
callsites, with no gaps, overlaps, trailing bytes, donor blocks, or opaque spans. The generated
program reproduces the oracle stream exactly with SHA-256
`e8a72dfd4796bda2a408ab8b629e9f12dc4ae225c8a1e0cc08f3c09b02ff68bf`.

The resolved stream is not sufficient to advertise production support. The first-principles
writer envelope opened in SOLIDWORKS and exposed `Sketch1` and `Revolve1`, but rebuild returned
false and produced zero bodies. A controlled stream bisect established the boundary precisely:

| envelope state                                                 | rebuild | bodies | warning                    |
| -------------------------------------------------------------- | ------: | -----: | -------------------------- |
| generated 25,212-byte Config-0                                 |   false |      0 | drawing sheet in view only |
| exact 24,902-byte Config-0 only                                |   false |      0 | drawing sheet in view only |
| exact Config-0 and ModelHeader                                 |    true |      1 | drawing sheet in view only |
| exact Config-0 ModelHeader Partition GhostPartition and LWDATA |    true |      1 | none                       |

The rebuilt control volume was `730.3626960943111 mm3`, matching the source. The ModelHeader
bounding record is fully understood: centre `(0,0,0.025)`, maximum `(0.0025,0.0025,0.05)`, minimum
`(-0.0025,-0.0025,0)`, and sphere radius `0.025248762345905198`, all in metres. The remaining
24,902-byte Config-0 and zero-warning partition family still require typed first-principles
programs. Production therefore rejects this family before claiming vendor loadability. No oracle
stream is read, copied, embedded, or required at runtime.

## Reversed circular blind boss

The origin-centred Front-plane circle with reverse direction and blind termination now selects the
dedicated typed reverse resolved and Config-0 programs. The production gate requires one sketch,
one circle, one boss, native ids 26 and 33, support plane 2, direction code 1, termination code 0,
and positive finite diameter and depth. Config-0 bounds use `z` from negative depth to zero.

The canonical 5 mm radius by 10 mm depth programs remain byte exact at 12,514 resolved bytes and
25,158 configuration bytes. SOLIDWORKS previously proved one rebuilt body at
`785.3981633974485 mm3`; driving the diameter to 16 mm produced `2010.619298297468 mm3`, and driving
the depth to 12 mm produced `942.477796076938 mm3`, with no load errors or warnings. Production
does not start or automate CAD software.
