# Revolve donors authored at swVersion 18000, and what the graded family pinned

This document records a SOLIDWORKS 2025 (`RevisionNumber` 33.5.0) authoring session that replaces
the corpus-derived revolve plan in `REVOLVE_DONOR_SPEC.md` §2 option 2. Every number here was
produced by a COM session or by SOLIDWORKS reopening a Kit-written file; nothing is decoded-only.

Companion data: `.rescratch/sw/author_revolve.py`, `.rescratch/sw/out/author_revolve.json`,
`.rescratch/sw/out/revolve_signature.txt`, `.rescratch/sw/out/measure_revolve_new.json`.

---

## 1. The API, enumerated from the type library before calling it

`sldworks.tlb` was walked for every member whose name starts `FeatureRevolve`. The relevant
overloads:

```
IFeatureManager.FeatureRevolve2(20) -> userdefined*
    bool SingleDir, bool IsSolid, bool IsThin, bool IsCut, bool ReverseDir,
    bool BothDirectionUpToSameEntity, long Dir1Type, long Dir2Type,
    double Dir1Angle, double Dir2Angle, bool OffsetReverse1, bool OffsetReverse2,
    double OffsetDistance1, double OffsetDistance2, long ThinType,
    double ThinThickness1, double ThinThickness2, bool Merge,
    bool UseFeatScope, bool UseAutoSelect

IFeatureManager.FeatureRevolveCut2(10) -> userdefined*
    double Angle, bool ReverseDir, double Angle2, long RevType, long Options,
    bool UseFeatScope, bool UseAutoSelect, bool AssemblyFeatureScope,
    bool AutoSelectComponents, bool PropagateFeatureToParts
```

`IFeatureManager.FeatureRevolve` (8), `FeatureRevolveThin` (10), `FeatureRevolveThinCut` (9),
`IModelDoc2.FeatureRevolve2` (5) and `IPartDoc.FeatureRevolve2` (5) also exist. The 20-argument
`IFeatureManager.FeatureRevolve2` is the one to use: it is the only boss overload that exposes both
direction types, both offsets and `Merge`.

`FeatureRevolve2` argument 18 (`Merge`) is the multi-body control. It was not needed for the donors
shipped here because the second body is disjoint from the first, and SOLIDWORKS then produces two
bodies with `Merge=True`.

### Axis selection

`Line1@SketchN` **cannot** be selected as `SKETCHSEGMENT` immediately after `InsertSketch` closes
the sketch. The working sequence is to select only the sketch:

```python
model.Extension.SelectByID2(sketch_name, "SKETCH", 0.0, 0.0, 0.0, False, 0, empty, 0)
```

SOLIDWORKS then resolves the axis from the single centreline the sketch contains. Every donor
authored this way records its axis as a sketch entity reference, exactly as the corpus revolves do.

### Sketch inference distorts the profile

`SketchManager.CreateLine` without `AddToDB` lets SOLIDWORKS infer relations, and a near-collinear
vertex pair is snapped. Authoring the profile `(2.5, -30.0) -> (1.5, -29.99)` produced
`(1.5, -30.0)` in the saved stream — a 0.01 mm move and a baked-in relation that would fight any
later coordinate patch. Setting `manager.AddToDB = True` around the polyline creation preserves the
authored coordinates byte-exactly. Always author revolve profiles with `AddToDB`.

---

## 2. What the graded family pinned

Eight parts on one rectangular profile (`6..18` in u, `-9..9` in v) with a centreline on `u = 0`,
plus two on a six-segment stepped-pin profile. Measured with `GetMassProperties` in the authoring
session.

| part | call arguments that differ | volume mm³ | `locate_features` |
|---|---|---|---|
| `revolve_slab_full` | `SingleDir=1`, `Dir1Type=0`, `Dir1Angle=2π` | 16286.016316209492 | 1 revolve, angle 360° |
| `revolve_slab_90` | `Dir1Angle=π/2` | 4071.5040790523744 | 1 revolve, angle 90° |
| `revolve_slab_270` | `Dir1Angle=3π/2` | 12214.512237157118 | 1 revolve, angle 270° |
| `revolve_slab_90_reversed` | `ReverseDir=1`, `Dir1Angle=π/2` | 4071.5040790523744 | 1 revolve, angle 90° |
| `revolve_slab_90_midplane` | `SingleDir=0`, `Dir1Type=Dir2Type=1` | 4071.5040790523744 | **0 features** |
| `revolve_slab_90_45_two_direction` | `SingleDir=0`, `Dir1Type=Dir2Type=2`, `Dir2Angle=π/4` | 6107.25611857856 | **0 features** |
| `revolve_pin_full` (Top Plane) | six-segment profile | 730.3626960943111 | 1 revolve, angle 360° |
| `revolve_pin_front_full` (Front Plane) | six-segment profile | 730.3626960943111 | 1 revolve, angle 360° |

Analytic check on the slab family: the profile is an annulus of inner radius 6, outer radius 18 and
height 18, so a full revolution is `π (18² − 6²) 18 = 16286.016316209...`. Each partial angle is
that value scaled by `angle / 360`, and the measurements agree to the last digit
(90° → ×0.25, 270° → ×0.75, 90°+45° two-direction → ×0.375).

### `getSingleEnd` and `getType(i)`

`SingleDir` is `moRevEndSpec_c` `getSingleEnd()` at `marker+20`, and `Dir1Type`/`Dir2Type` are
`getType(0)`/`getType(1)` at `marker+32`/`marker+36`. The observation that matters for Kit is
structural, not numeric:

**`revolution_end_spec_objects()` finds nothing in a `SingleDir=0` part.** The 52-byte constant it
searches for — `u32 1` followed by 24 zero bytes, two `float64 0.01` and 8 zero bytes — encodes
`getSingleEnd() == 1`. Mid-plane and two-direction revolves therefore carry a different
`moRevEndSpec_c` body and `locate_features` returns zero features for them, so the whole part is
undecodable rather than merely partly decoded. The two parts above are the reproducible cases; the
constant for `SingleDir=0` was not derived.

Consequence for the writer: a mid-plane revolution has to be **declined**, not written. Kit does
that in `_revolution_extras`. Silently writing it as one-direction would give the right volume for
a full revolution and the wrong solid for anything else.

### `getOffsetReverse(i)`

Not pinned. Every part in this family was authored with `OffsetReverse1 = OffsetReverse2 = False`
and `OffsetDistance1 = OffsetDistance2 = 0.0`, and no `SingleDir=1` part in the family varies them,
so the two `float64 0.01` values inside the 52-byte constant remain unattributed. The Kit writer
never touches them; a surface-offset revolve has no donor.

### The angle dimension chain — the trap that matters

`SERIALIZE.md` §3 records that `getAngle(i)` reads the `moDisplayDim_c*` at `+0x18+8i` and returns
literal 2π when that pointer is null. The graded family makes the consequence measurable:

| part | resolved-features stream bytes |
|---|---|
| `revolve_slab_full` (360°) | 12135 |
| `revolve_slab_90` (90°) | 12247 |
| `revolve_slab_270` (270°) | 12247 |

The 112-byte difference is the display dimension a partial angle needs and a full revolution does
not carry. `locate_features` *does* report `angle_degrees == 360.0` for the full-revolution part —
that value comes from the `moAngleParameter_c` scalar, which is present in both shapes. So the
scalar is patchable in both, but on a 360° donor **patching it changes nothing that SOLIDWORKS
reads**: with the display-dimension pointer null, `getAngle` still returns 2π and the rebuild still
sweeps a full revolution.

A 360° donor patched to 90° would therefore produce a file whose `KeyWords` and scalar say 90° and
whose geometry is 360°. `donor_library._revolve_edit` refuses that combination outright, and
`donor_match._revolution_target` only accepts a 360° target. A partial-angle revolve needs a
partial-angle donor — a different record shape, not a different number, exactly as predicted.

---

## 3. Donor topology key

`REVOLVE_DONOR_SPEC.md` §3 proposed putting the axis kind in the `support` slot. That is not
sufficient: the sketch plane also has to be in the key, because the patcher writes the target's
projected `(u, v)` coordinates straight into the donor's sketch and a donor authored on the Top
Plane cannot receive a Front Plane profile. The shipped key composes both:

```
support = f"{plane}-{axis_kind}"   # front-sketch-axis, top-sketch-axis, right-sketch-axis
```

`REVOLVE_SUPPORT_BY_PLANE` maps the principal-plane name to that value, and `REVOLVE_SUPPORTS` is
its value set. `FULL_REVOLUTION_END` stays out of `SUPPORTED_END_CONDITIONS` and
`DEPTHLESS_END_CONDITIONS`; `_revolve_edit` is the revolve's own validation branch and requires an
angle in `(0, 360]`, no depth, and no direction flag.

---

## 4. Donors shipped, and what each was measured against

Every donor below was authored fresh at 18000 in the session above, patched through the shipped
`convert()` path against a FreeCAD source document, and the result reopened and measured in
SOLIDWORKS. `control healthy: True` before and after the batch
(`BASELINE_40x20x10.SLDPRT` = 8000.000000000001 both times).

| donor | features | FreeCAD source volume mm³ | SOLIDWORKS volume mm³ | bodies |
|---|---|---|---|---|
| `revolve_full` | revolve-boss / rectangle / front-sketch-axis | 16286.01631620949 | 16286.016316209485 | 1 |
| `revolve_pin_top_full` | revolve-boss / polyline-6 / top-sketch-axis | 730.3626960943112 | 730.3626960943113 | 1 |
| `revolve_pin_front_full` | revolve-boss / polyline-6 / front-sketch-axis | 730.3626960943112 | 730.3626960943111 | 1 |
| `boss_disjoint_revolve` | boss + revolve-boss | 24730.36269609431 | 24730.362696094307 | 2 |
| `arcboss_cut_cut_cut_through_rev` | boss + 3 cuts + revolve-boss | 584449.7296355376 | 584449.7323019443 | 2 |

`revolve_pin_top_full` additionally reproduces the FreeCAD centre of mass of
`PartDesignExample`'s `Body001`: `(≈0, ≈0, 19.83790861645005)` against
`(≈0, ≈0, 19.837908616450036)`.

| `boss_revcut` | boss + revolve-cut | 6869.026644707673 | 6869.026644707676 | 1 |

`boss_revcut` (`moRevCut_c`) was driven by a `PartDesign::Groove` document. FreeCAD does not set an
`Operation` property on a groove, so the reader now maps `PartDesign::Groove` to
`BooleanOperation.CUT` the way it already maps `PartDesign::Pocket`, and gives every revolution the
same create/join/cut rule the extrusions use. Without that the groove arrives with no operation and
`_revolution_operation` refuses it in any position but the first. The re-authored part's
resolved-features stream is byte-length identical (17713) to the entry already in the library.

### The authored donor parts, measured through the harness

The eleven authored parts were also opened directly, with control before and after
(`control healthy: True`, `BASELINE_40x20x10.SLDPRT` = 8000.000000000001 both times):

| part | volume mm³ | analytic | bodies |
|---|---|---|---|
| `revolve_slab_full` | 16286.016316209494 | 16286.016316209494 | 1 |
| `revolve_slab_90` | 4071.5040790523735 | 4071.5040790523734 | 1 |
| `revolve_slab_270` | 12214.512237157118 | 12214.512237157120 | 1 |
| `revolve_slab_90_reversed` | 4071.5040790523735 | 4071.5040790523734 | 1 |
| `revolve_slab_90_midplane` | 4071.5040790523735 | 4071.5040790523734 | 1 |
| `revolve_slab_90_45_two_direction` | 6107.25611857856 | 6107.256118578603 | 1 |
| `revolve_pin_full` | 730.3626960943111 | 730.3626960943112 | 1 |
| `revolve_pin_front_full` | 730.3626960943111 | 730.3626960943112 | 1 |
| `boss_revcut_full` | 6869.0266447076765 | 6869.026644707673 | 1 |
| `boss_disjoint_revolve` | 24730.362696094307 | 24730.36269609431 | 2 |
| `arcboss_cut_cut_cut_through_rev` | 591409.401648088 | — | 2 |

The `arcboss` donor part carries the donor's own placeholder coordinates, so it has no analytic
expectation; what matters is that it rebuilds into two bodies before any patch is applied.

---

## 5. Multi-body: what the disjointness evidence supports

`donor_match` no longer declines a document because it builds more than one solid body. It groups
the solid timeline by body, in document body order, and emits each body's features in timeline
order. Two rules gate it:

1. Bodies whose feature chains **overlap** are declined —
   `body B shares F with body A, so the N bodies are not built independently`. A shared base feature
   means the bodies are not independent and the donor cannot express them.
2. A solid feature that belongs to **no** declared body is declined —
   `the document builds F outside every solid body it declares`.

The body-grouped ordering is what makes the `PartDesignExample` revolve expressible at all. In
timeline order the revolve sits between the pad and the pockets; grouped by body it moves to the
end, so every cut is applied while only the first body exists and no feature-scope record has to be
authored. The two bodies are disjoint (FreeCAD `distToShape` = 7.5 mm, `fuse` gives 2 solids), so
the reordering is geometrically equivalent.

The previous "ancillary body" rule — drop a body that a non-model native feature references — is
gone. It existed so a single-body donor could be selected while a tool body existed, and it dropped
`PartDesignExample`'s `Endmill006` silently. Both bodies are now expressed.

### Still declined, honestly

A boss in position ≥2 whose solid **overlaps** an earlier one should fuse into one body and does
not. `kit_boss_boss` measures 32000 mm³ / 2 bodies against FreeCAD's 28800 mm³ / 1 body. That is a
single-body document, so the multi-body gate never sees it; `moEndSpec_c+0x128` `getMerge()` is
already `1` in every donor, so merge is not the cause. The second feature's records carry the
resolved feature scope and that is not located. Unchanged by this work.

---

## 6. Why `application_usable` is still `False` for `PartDesignExample.FCStd`

The donor now expresses every solid feature of both bodies and SOLIDWORKS rebuilds the file to the
right geometry, but `application_usable` stays `False`. The donor is not the reason. It is decided
in `adapter._generated_streams` as

```
application_usable = part.application_usable and every required capability is
                     TransferMode.NATIVE or CarrierReason.TARGET_UNSUPPORTED
```

and this document requires three capabilities that are `CARRIER` /
`WRITER_UNIMPLEMENTED`:

| capability | why it is not native | evidence |
|---|---|---|
| `expressions` | 9 FreeCAD expression bindings, e.g. `<<Attributes002>>.Diameter`, `SetupSheet.HorizRapid`. SOLIDWORKS has equations, so the capability is not target-unsupported, but no equation writer exists. | `document.parameters` with `expression is not None` |
| `selections` | 5 `ReferenceAxis` sub-element selections (`Sketch.N_Axis`, `Sketch004.V_Axis`). `read_sldprt` recovers SOLIDWORKS selections, so the capability is genuinely supported by the target and the gap is on the write side. | `document.selections` |
| `support_planes` | The document declares 6 planes; the writer emits the 3 principal ones. `XY_Plane001` collides onto Front Plane's object id 2 and `XZ_Plane001` / `YZ_Plane001` get ids with no plane record, so `_proved_write_capabilities` cannot prove the set. | `.rescratch/pd_planes.txt` |

Compare `kit_boss_blind.FCStd`, which requires none of the three and reports
`application_usable=True` with `support_planes` native.

None of the three can be turned native by relabelling. Reclassifying any of them as
`TARGET_UNSUPPORTED` would assert that SOLIDWORKS has no equations, no selections and no reference
planes, which is false, and would silently flip `application_usable` to `True` for every document
that carries them. Reaching `True` for this document needs a native SOLIDWORKS equation writer, a
native selection writer, and `moRefPlane_c` records for non-principal support planes — three
capabilities outside the revolve and multi-body work, and none of them established anywhere in
`re/`.
