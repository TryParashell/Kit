<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Reversed dimensioned circular boss

Status: **confirmed and vendor measured** for an origin-centred diameter-driven circle followed by
a blind boss in the reverse direction. Both required streams are emitted entirely from typed field
programs. No saved stream, encoded payload, opaque interval, or CAD runtime dependency is present.

## Controlled oracle

The source control is `.rescratch/circle_autodim_r5_h10_reverse.SLDPRT`, authored by changing the
direction of the already controlled 5 mm radius by 10 mm circular boss. SOLIDWORKS was used only as
an isolated reverse-engineering oracle. Production code neither starts nor automates it.

Four bounded debugger runs captured the object and primitive readers independently:

| stream                      | raw bytes | traced objects | traced definitions | field operations | owners | missing |
| --------------------------- | --------: | -------------: | -----------------: | ---------------: | -----: | ------: |
| `Config-0-ResolvedFeatures` |    12,700 |            338 |                 49 |            2,873 |    538 |       0 |
| `Config-0`                  |    25,190 |            128 |                 39 |            4,345 |  1,058 |       0 |

Both object traces tile their streams without gaps, overlaps, trailing bytes, counter mismatches,
or disagreement with the statically scanned class definitions. Primitive fields retain the native
reader type and serializer callsite. Class definitions, class references, object references,
strings, and confirmed direct arrays retain their structural encoding.

`Config-0` also starts with one root `moPart_c` class definition read directly through
`ReadClass`, before the 128 nested `ReadObject` events. The emitted program therefore owns 129
structural operations and 40 class definitions. This is expected and reconciles the object trace
with complete wire ownership.

The raw replay digests before metadata normalization were:

| stream        | sha256                                                             |
| ------------- | ------------------------------------------------------------------ |
| resolved      | `2bec536665be79b93ed1bfb8562e4c225ec1831189aa4eb8533170741754c4ce` |
| configuration | `91c0d487f0936b6248efc13887c26cbce03ae5a055a2f11394418ba93421a085` |

Each raw program reproduced its oracle stream byte for byte before canonicalization.

## The apparent stream growth was saved metadata

The earlier conclusion that reverse direction added 186 resolved bytes and 32 configuration bytes
was refuted by the field trace. The object count, definition count, operation count, and owners are
unchanged.

The complete 186-byte resolved difference is two variable-width strings:

| field               | raw width | canonical value | canonical width | removed |
| ------------------- | --------: | --------------- | --------------: | ------: |
| saved absolute path |       158 | empty           |               4 |     154 |
| saved document name |        46 | `Part2`         |              14 |      32 |

The complete 32-byte configuration difference is the same long document name replacing `Part1`.
Those strings describe the oracle workstation and filename, not the model or format grammar. They
are therefore canonicalized out of production. The production programs are 12,514 and 25,158 bytes
and contain neither the source path nor source filename.

Canonical program digests are:

| stream        | sha256                                                             |
| ------------- | ------------------------------------------------------------------ |
| resolved      | `b9735d3134c944dc8e66e64d62aa84c117edcf06a17e5d69601e552b9150655d` |
| configuration | `fc1cb072c15c9f334bab288234353e3dc27db5aa83abd61c6fdd95364ac276a8` |

## Reversed resolved fields

After removing saved metadata, the reversed and normal resolved programs share all 2,873 operation
boundaries. Nineteen typed values differ. Their conservative names below are the owning native
reader rather than guessed field names.

| offset | normal       | reversed     | owner                                         |
| -----: | ------------ | ------------ | --------------------------------------------- |
|   4068 | `-0.0005`    | `-0.0105`    | `mgPoint_c::restore+0x4f`                     |
|   4309 | `0.005`      | `-0.005`     | `mgPoint_c::restore+0x4f`                     |
|   4638 | `0.0105`     | `0.0005`     | `mgPoint_c::restore+0x4f`                     |
|   4879 | `0.005`      | `-0.005`     | `mgPoint_c::restore+0x4f`                     |
|   5884 | `0x40000000` | `0xc0000000` | `moNode_c::SerializeLWData+0x297`             |
|   9497 | `0x40000140` | `0xc0000140` | `moNode_c::SerializeLWData+0x297`             |
|   9535 | `119`        | `125`        | `moFeature_c::Serialize+0x5e2`                |
|   9556 | `0.0`        | `0.016`      | `moFeature_c::Serialize+0x832`                |
|   9620 | `31271357`   | `31271366`   | `moFeature_c::Serialize+0xf1d`                |
|   9624 | `1770759943` | `212936623`  | `moFeature_c::Serialize+0xf2b`                |
|   9893 | `0`          | `8`          | `MO_GET_MODELNAME_FROM_PATH+0xc54`            |
|  10449 | `7`          | `10`         | `su_CArchive::ReadObject+0x172`               |
|  10542 | `0`          | `1`          | `moDimPatternRegenStatus_c::Serialize+0x1162` |
|  11415 | `0.01`       | `-0.01`      | `mgPoint_c::restore+0x4f`                     |
|  11465 | `1.0`        | `-1.0`       | `Dimension_c::Serialize+0xab80`               |
|  11741 | `-0.01`      | `0.01`       | `mgPoint_c::restore+0x36`                     |
|  11765 | `-0.01`      | `0.01`       | `mgPoint_c::restore+0x36`                     |
|  11831 | `-1.0`       | `1.0`        | `mgVector_c::restore+0x29`                    |
|  11879 | `0x80000427` | `0x82000427` | `Dimension_c::Serialize+0x62f2`               |

The two node flag changes are necessary but not sufficient on their own. The measured direction is
carried by the complete typed set, including dimension orientation, points, vector, feature state,
and regenerated cache identities.

## Coupled configuration fields

Against the normal 5 mm by 10 mm circle specialization, eleven typed configuration values differ:

| offset | normal  | reversed    | owner                                          |
| -----: | ------- | ----------- | ---------------------------------------------- |
|     14 | `2822`  | `2854`      | `moVisualOverlayObject_c::GetThisClass+0x1b40` |
|    222 | `4`     | `6`         | `uoRVAppearanceProperties::restore+0x2e`       |
|   2392 | `0.005` | `-0.005`    | `mgBBox_c::restore+0x50`                       |
|   2416 | `0.01`  | `0.0`       | `mgBBox_c::restore+0x9b`                       |
|   2440 | `0.0`   | `-0.01`     | `mgBBox_c::restore+0xe6`                       |
|   2596 | `103`   | `106`       | `moView_c::Serialize+0x3c19`                   |
|   2942 | `600`   | `493`       | `moAtom_c::GetRuntimeClass+0x907`              |
|   2950 | `600`   | `493`       | `moAtom_c::GetRuntimeClass+0x932`              |
|  24095 | `0`     | `1`         | `moNode_c::SerializeLWData+0x25a`              |
|  25082 | `0`     | `31271366`  | `moFeature_c::Serialize+0xf1d`                 |
|  25086 | `0`     | `186891454` | `moFeature_c::Serialize+0xf2b`                 |

The bounding box is `z ∈ [-depth, 0]`. Geometry overrides must therefore keep offset 2392 at
`-depth / 2`, offset 2416 at zero, and offset 2440 at `-depth`. Radius, x and y bounds, and the
bounding sphere keep the same units and equations as the normal circle specialization.

## Live application proof

The canonicalized streams were substituted into the controlled envelope only after being generated
without the oracle. SOLIDWORKS opened and rebuilt the result with no load errors or warnings:

| measurement     | result                        |
| --------------- | ----------------------------- |
| bodies          | `1`                           |
| feature tree    | `Sketch1`, `Boss-Extrude1`    |
| sketch diameter | `10 mm`                       |
| boss depth      | `10 mm`                       |
| volume          | `785.3981633974485 mm³`       |
| surface area    | `471.238898038469 mm²`        |
| centre of mass  | approximately `(0, 0, -5) mm` |

Driving `D1@Sketch1` to 16 mm rebuilt one body at `2010.619298297468 mm³` with centre z = -5 mm.
Driving `D1@Boss-Extrude1` to 12 mm rebuilt one body at `942.477796076938 mm³` with centre z =
-6 mm. The controls before and after both measured `8000.000000000001 mm³`.

This proves the canonical metadata removal is safe and the reversed history remains live,
dimension-driven, and geometrically reversed.
