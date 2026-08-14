<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Native assembly closure

Status: **constructive for the typed occurrence families described below; the five recursively
audited FCStd assemblies remain blocked by unsupported component histories or mate records until a
fresh SOLIDWORKS oracle accepts their complete generated bundles.**

No production path in this work launches SOLIDWORKS, uses COM, reads a vendor document, or copies a
vendor stream. Oracle-authored assemblies and debugger traces are research inputs only. The writer
emits the recovered fields directly.

## Component transform record

The component placement inside `Contents/Config-0` is an `mgXform_c` record. The traced reader owns
the fields as follows:

| Field          | Encoding  | Meaning                                                        |
| -------------- | --------- | -------------------------------------------------------------- |
| basis marker   | `u8`      | zero for identity basis and one when nine basis doubles follow |
| optional basis | `9 × f64` | complete `mgMatrix_c` linear basis                             |
| translation    | `3 × f64` | component origin in metres                                     |
| scale          | `f64`     | one for the supported affine component records                 |
| trailing state | `u8`      | zero in every controlled assembly record                       |

The optional matrix is therefore exactly 72 bytes. Its order for a neutral row-major `Matrix4` is
`m0,m4,m8,m1,m5,m9,m2,m6,m10`. The enclosing serialized byte length at logical stream offset 18
increases by 72 for every nonidentity basis.

The prior encoder wrote only later-occurrence translations, silently discarded every rotation, and
subtracted `0.005` metres from every Z translation. The controlled assembly author inserted its
components at `(index × 0.05, 0, 0)` and the traced `mgXform_c` values contain an unmodified zero Z,
so that subtraction had no format basis. All static and recurrence encoders now write the first and
later translations directly. Mixed recurrence additionally writes the optional basis as typed
doubles; the common recurrence item carries the same basis for the other typed families.

## Logical offsets in the typed recurrence programs

These are source-program offsets. Variable strings and optional bases may change physical offsets
without changing field order.

| Family        | first marker and translation | later marker and translation                   |
| ------------- | ---------------------------- | ---------------------------------------------- |
| repeated path | `321; 322,330,338`           | `214; 215,223,231` relative to the unit record |
| distinct path | `275; 276,284,292`           | `168; 169,177,185` relative to the unit record |
| hybrid path   | `275; 276,284,292`           | `168; 169,177,185` relative to the unit record |
| mixed path    | `275; 276,284,292`           | `168; 169,177,185` relative to the unit record |

The scale and trailing-state fields immediately follow each translation. Inserting a basis does not
change the archive object map because all nine new values are primitives owned by
`mgMatrix_c::restore`.

## Representability gate

The static one-, two-, and three-occurrence programs were traced only with identity bases. They
reject a nonidentity basis rather than silently flattening it. The scalable repeated, distinct,
hybrid, and mixed programs carry complete bases.

The native binary programs also encode the controlled oracle state: every direct component is
floating, unsuppressed, visible, rigid, nonvirtual, outside zones, and included in the bill of
materials. SOLIDWORKS `Component2.IsFixed` returned false for all six occurrences in the traced
author assembly and for all four occurrences in the generated validation assembly. A source state
outside that set is rejected before native loadability can be claimed. The XML component tree
remains a semantic mirror; it is not accepted as proof because SOLIDWORKS reads placement and state
from the binary assembly history.

The first `swReference` uses `swID = 24`, but the live author assembly proves that value is an
occurrence feature sequence key rather than a fixed-state flag. Generated IDs now advance from 24
in occurrence order, and the reader no longer infers `fixed = true` from ID 24.

## Live vendor validation

SOLIDWORKS 2025 SP5.0 (`RevisionNumber = 33.5.0`) opened the generated
`RotatedMixed.SLDASM` bundle with zero load errors and rebuilt it successfully. The vendor API
reported four fully resolved, unsuppressed component references, four solid bodies, a volume of
`56000.00000000001 mm³`, and a center of mass at
`(35.0, 45.535714285714285, 5.892857142857144) mm`. Each `Transform2.ArrayData` basis and
translation matched the four requested placements exactly, including the two nonidentity bases.
The only load warning was bit 32, the known drawing-sheet/view-only warning emitted for these
non-drawing oracle opens.

The generated `BoxA.sldprt` child opened with no errors or warnings, rebuilt with one solid body,
and exposed `Sketch1` followed by editable `Boss-Extrude1`. Driving
`D1@Boss-Extrude1` from `10 mm` to `15 mm` rebuilt successfully and changed volume from
`8000.000000000001 mm³` to `11999.999999999998 mm³`; the oracle closed without saving the edit.
This proves the tested assembly family loads with exact component transforms and retains an
editable parametric component history. It does not prove the five recursively audited source
assemblies whose component histories and mates remain outside the implemented grammar.

## Recursive corpus boundary

The five assembly inputs in the 11 August 2026 recursive audit are:

1. FreeCAD `AssemblyExample.FCStd`: 13 direct part documents, 13 placed occurrences, and 16 mates.
2. `.rescratch/out.FCStd`: 25 definitions and 48 occurrences, including unsupported reference
   definitions and a nested assembly.
3. `V8_engine.FCStd`: a large nested assembly whose component documents include unsupported native
   and reference histories.
4. `Conrod_2.FCStd`: an assembly with native/reference component histories and mates.
5. `Piston_2.FCStd`: an assembly with native/reference component histories and mates.

The root assembly history can be constructive while the complete bundle is still unusable. A pass
requires every sibling `SLDPRT` or nested `SLDASM`, every source mate, every occurrence state, and
every transform to be represented, then opened and rebuilt together. Until that happens the result
must remain `vendor_loadable = false` or `application_usable = false`; a typed root alone is not a
lossless assembly translation.
