<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# FCStd to SOLIDWORKS corpus coverage

Status: **partial, measured, and fail-closed**. Kit does not yet translate every FCStd in the
repository to a fully parametric SLDPRT or SLDASM. The production writer emits native SOLIDWORKS
records for the recovered families below and explicitly rejects the other source histories instead
of reporting a neutral carrier as a lossless result.

## Reproducible audit

Run from the repository root, without FreeCAD, SOLIDWORKS, COM, or another CAD process:

```powershell
uv run python tools/audit_fcstd_solidworks.py . --require-vendor-loadable
```

The 2026-08-11 recursive result is:

| measurement              | count |
| ------------------------ | ----: |
| FCStd files              |   165 |
| parser or writer errors  |     0 |
| vendor-loadable contract |    40 |
| application-usable       |    40 |
| near-lossless            |    40 |
| vendor-only              |     0 |
| unsupported              |   125 |

The command returns nonzero because 125 sources remain unsupported. Each accepted part traverses
the public `write_document` path and the resulting compound file is read back with `SldprtArchive`.
The increase from 38 of 163 to 40 of 165 is exactly the two controlled standalone cylinder sources;
the unsupported count and unsupported-family census are unchanged.
This is a production-path structural proof, not a claim that all 40 files were individually opened
in SOLIDWORKS. Vendor-application oracle measurements remain separately recorded in
`archive/MULTISTREAM.md`.

## Recovered native part families

The accepted source histories are constructed from typed SOLIDWORKS fields with editable sketches,
dimensions, feature ordering, and body-producing operations:

- rectangular and circular pad, including blind depth, reverse direction, mid-plane, and principal
  sketch-plane variants where the recovered grammar supports them;
- exact standalone `Part::Box` solids lowered to an origin-based rectangle with independently
  editable length and width dimensions plus an editable blind-boss height;
- exact standalone origin-aligned `Part::Cylinder` solids lowered to a diameter-driven circle with
  an independently editable blind-boss height;
- blind and through-all pockets, including two- and three-pocket chains;
- pad followed by a second pad;
- full rectangular revolution and pad followed by a groove;
- pad followed by fillet, chamfer, or shell;
- pad followed by linear pattern; and
- pad followed by circular pattern, including occurrence count, total angle, and reverse direction.

The load-critical reference streams are closed for these families:

| stream family                      | reference bytes | opaque bytes |
| ---------------------------------- | --------------: | -----------: |
| `Contents/Definition`              |           3,618 |            0 |
| `Contents/CMgr`                    |           1,957 |            0 |
| `Contents/Config-0`                |   25,158–25,214 |            0 |
| assembly core field program        |          38,198 |            0 |
| family-specific `ResolvedFeatures` |   10,556–27,092 |            0 |

Those figures describe the supported reference programs. They do not imply support for an
unrecovered source feature family.

## Controlled feature campaign

Of the 25 focused FCStd inputs under `.rescratch/sw/fcstd`, 20 reach the native vendor-loadable and
application-usable path. These five fail closed:

- `.rescratch/sw/fcstd/kit_boss_disjoint_revolve.FCStd`;
- `.rescratch/sw/fcstd/kit_revolve_pin_front.FCStd`;
- `.rescratch/sw/fcstd/kit_revolve_pin_top.FCStd`;
- `.rescratch/sw/fcstd/kit_revolve_pin_top_90.FCStd`; and
- `.rescratch/sw/fcstd/kit_revolve_pin_top_midplane.FCStd`.

They require one or more unrecovered semantics: a non-rectangular six-segment pin profile, a
non-front revolution plane, a partial revolution, a mid-plane revolution, or a disjoint
pad-plus-revolution body history.

## Unsupported families in the full corpus

The audit records each type at most once per unsupported document. `native`, `reference`,
`extrusion`, and `fillet` are Kit timeline kinds used when a source object has no more specific
FreeCAD type identifier.

| source or timeline type      | documents |
| ---------------------------- | --------: |
| `App::FeaturePython`         |         3 |
| `App::GeometryPython`        |         2 |
| `Part::Box`                  |         9 |
| `Part::Compound`             |         1 |
| `Part::Cut`                  |         7 |
| `Part::Cylinder`             |         3 |
| `Part::Extrusion`            |         2 |
| `Part::Feature`              |         5 |
| `Part::FeaturePython`        |        11 |
| `Part::Line`                 |         1 |
| `Part::Mirroring`            |         2 |
| `Part::MultiCommon`          |         1 |
| `Part::MultiFuse`            |         4 |
| `Part::Offset2D`             |         1 |
| `Part::Part2DObjectPython`   |         6 |
| `Part::Plane`                |         1 |
| `Part::Sphere`               |         1 |
| `PartDesign::AdditiveBox`    |         1 |
| `PartDesign::AdditiveSphere` |         1 |
| `PartDesign::LinearPattern`  |         2 |
| `PartDesign::Pad`            |        18 |
| `PartDesign::Plane`          |         2 |
| `PartDesign::Pocket`         |        10 |
| `PartDesign::PolarPattern`   |         2 |
| `PartDesign::Revolution`     |        22 |
| `Path::FeaturePython`        |         4 |
| `extrusion`                  |        42 |
| `fillet`                     |        21 |
| `native`                     |        54 |
| `reference`                  |        54 |

`PartDesign::Pad`, `Pocket`, `Revolution`, `LinearPattern`, and `PolarPattern` in this table are
outside the exact profile, plane, termination, dependency, or operation sequences listed in the
recovered section; their type name alone is not sufficient for acceptance. The three
`Part::Cylinder` rows are likewise cylinders embedded in unrecovered multi-object histories, not
standalone primitives satisfying the exact cylinder gate.

## Assembly corpus result

All five FCStd documents detected as assemblies currently fail the portable native SLDASM contract:

- `.rescratch/out.FCStd`;
- `.rescratch/freecad/FreeCAD_1.1.3-Windows-x86_64-py311/data/examples/AssemblyExample.FCStd`;
- `examples/Random/V8_engine.FCStd`;
- `examples/Random/V8_engine/Conrod_2.FCStd`; and
- `examples/Random/V8_engine/Piston_2.FCStd`.

The assembly writer has a typed zero-opaque core, but these inputs require unsupported component
feature histories or assembly semantics. They are therefore not counted as vendor-loadable.

## Completion boundary

There is no remaining opaque-byte debt in the stream programs used by the recovered families. There
is substantial feature-semantic work left across the corpus, especially arbitrary sketch profiles,
multi-object primitive and Boolean Part histories, broader revolution modes, non-campaign pattern
histories, and the five real assemblies. A claim that nothing remains to reverse engineer would
contradict this audit.

## Native box oracle

The accepted standalone box program is not inferred from its internal decoder alone. The generated
file was opened and rebuilt in SOLIDWORKS 2025 between healthy controls with zero load errors or
warnings, one solid body, `Sketch1`, `Boss-Extrude1`, volume 1,000 mm³, surface area 600 mm², and
centre of mass `(5, 5, 5)` mm. Independent live parameter drives on that generated file produced:

| parameter          | value | volume mm³ | centre of mass mm |
| ------------------ | ----: | ---------: | ----------------- |
| `D1@Sketch1`       | 20 mm |      2,000 | `(10, 5, 5)`      |
| `D2@Sketch1`       | 15 mm |      1,500 | `(5, 7.5, 5)`     |
| `D1@Boss-Extrude1` | 12 mm |      1,200 | `(5, 5, 6)`       |

The box-specific 14,855-byte `ResolvedFeatures` program contains 3,522 typed operations, and its
25,158-byte `Config-0` program contains 4,345 typed operations. Both tile their reference streams
exactly and contain zero opaque or donor byte spans.

## Native cylinder oracle

The standalone cylinder path is backed by a separately authored, diameter-dimensioned circle
program. Its 12,514-byte `ResolvedFeatures` stream contains 338 objects, 49 class definitions,
2,873 typed operations, 538 serializer owners, zero missing fields, and zero opaque or donor spans.
The matching 25,158-byte `Config-0` stream reuses the closed 4,345-operation field program and
specializes 29 typed fields for the circle's identities, bounds, cache metadata, radius, and depth.

A generated 5 mm radius by 10 mm high cylinder opened and rebuilt in SOLIDWORKS 2025 with zero load
errors or warnings, one body, `Sketch1`, `Boss-Extrude1`, volume 785.3981633974485 mm³, surface area
471.238898038469 mm², and centre of mass `(0, 0, 5)` mm. Independent live edits produced:

| parameter          | value |         volume mm³ |  surface area mm² | centre of mass mm |
| ------------------ | ----: | -----------------: | ----------------: | ----------------- |
| `D1@Sketch1`       | 16 mm | 2,010.619298297468 | 904.7786842338604 | `(0, 0, 5)`       |
| `D1@Boss-Extrude1` | 12 mm |   942.477796076938 | 534.0707511102650 | `(0, 0, 6)`       |

An independently generated 8 mm radius by 12 mm high FCStd also opened with one body, volume
2,412.74315795696 mm³, surface area 1,005.3096491487335 mm², and centre of mass `(0, 0, 6)` mm.
An off-origin generic circle was observed rebuilding at the origin; that case still fails closed
and is not reported as lossless. A reverse-direction oracle proved that the high feature flag alone
is insufficient, then complete field tracing recovered the entire coupled history. After saved
path and document-name metadata are canonicalized, both reverse streams retain the normal 12,514-
and 25,158-byte widths with zero opaque or donor spans. The generated negative-Z body opened and
rebuilt without warnings, and independent diameter and depth edits remained parametric. Strict
origin-centred Front-plane reversed blind circles are now supported; off-origin and non-front
variants remain fail-closed.
