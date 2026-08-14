# Writing equations, reference planes and direction axes into a donor-backed part

Read-only analysis of a licensed SOLIDWORKS 2025 install. No SOLIDWORKS binary was modified.
Everything below is reproduced by `.rescratch/sw/author_meta_donor.py`,
`.rescratch/sw/emit_meta_donor.py`, `.rescratch/verify_meta.py`,
`.rescratch/probe_axis_bindings.py` and `.rescratch/sw/confirm_meta.py`, whose raw output is
`.rescratch/sw/out/author_meta_donor.json`, `.rescratch/out/verify_meta.json`,
`.rescratch/out/probe_axis_bindings.json` and `.rescratch/sw/out/confirm_meta.json`.

This document is the write-side companion to `records/Equations.md`. It records how the three
capabilities `expressions`, `support_planes` and `selections` become native for a document that
selects a donor, without inserting a single object into any load-critical stream.

---

## 1. The route: author the metadata into the donor, then rewrite lengths-agnostic fields

`records/Equations.md` §4 establishes that inserting a `moRelation_c` shifts every later
`su_CArchive` map index in `Contents/Config-0`, and `archive/Multistream.md` §4 records that
`Contents/Config-0` is load-critical. The same argument applies to inserting a `moRefPlane_c` into
`Contents/Config-0-ResolvedFeatures`.

So nothing is inserted. A donor is authored through COM that already contains the records, and the
writer rewrites only fields whose edit cannot move a map index:

| record | field rewritten | why the edit is safe |
|---|---|---|
| `moRelation_c` | the `su_CArchive` serialized string holding the equation source | `su_CArchive` stores no absolute offsets, so a different length moves no index and invalidates no token (`Equations.md` §4) |
| `moRefPlane_c` | the 121-byte frame block | fixed size, so the stream length is unchanged |

The relation count `u16` at the `moRelMgr_c` body `+0` is left exactly as authored, because the
number of relations does not change.

## 2. The authored donor

`arcboss_cut_cut_cut_through_rev_meta` is `arcboss_cut_cut_cut_through_rev` re-authored by
`.rescratch/sw/author_revolve.py::case_arcboss_cut_cut_cut_through_rev`, plus

* **4 reference planes**, each `FeatureManager.InsertRefPlane(swRefPlaneReferenceConstraint_Coincident, 0.0, 0, 0.0, 0, 0.0)`
  against `Top Plane`;
* **24 global-variable equations** `"KitVar01"= 1` … `"KitVar24"= 24`, added with
  `EquationMgr.Add2(-1, text, True)`.

Geometry is unchanged: volume `591409.401648088` mm³ and 2 bodies before and after the additions,
and `resolved.locate_features` returns a byte-for-byte identical feature description
(name, kind, feature id, sketch id, sketch name, point/arc/swept-arc counts, depth presence,
reverse flag, end-condition code, angle) to the base donor for all five features.

### API notes

* `EquationMgr.Add3(index, text, solve, whichConfigurations, configNames)` returns `-1` for
  `whichConfigurations` of `0`, `1` (`swThisConfiguration`) and `2` (`swAllConfiguration`) on a
  freshly created part. `Add2(-1, text, True)` and `Add(-1, text)` both succeed. Use `Add2`.
* `swRefPlaneReferenceConstraint_Coincident` is `4` and `_Distance` is `8`
  (`.rescratch/sw/out/refplane_enums.txt`).
* `ModelDoc2.CreatePlaneFixed(p1, p2, p3, useGlobal)` returns `False` and creates nothing when
  called without a selection context, so a fixed plane is not reachable that way.

## 3. Which reference planes persist a frame

Four planes were authored coincident/offset-zero against each principal plane and the resolved
stream decoded with `native._decode_planes`:

| authored against | constraint | 121-byte frame present |
|---|---|---|
| `Top Plane` | coincident | yes |
| `Right Plane` | distance 0 | yes |
| `Front Plane` | coincident | no |
| `Front Plane` | distance 0 | no |

A plane whose rotation relative to the sketch-space basis is the identity does not persist a
matrix; the decoder reports `reference plane frames unavailable for 33:Plane1, 35:Plane2` for the
two Front-Plane cases. `native._minimal_frame` is meant to cover that shape but rejects the
zero-offset instance, because it compares `struct.pack("<d", tail[1])` against
`struct.pack("<d", -origin[2])` and `0.0` does not pack the same as `-0.0`.

The donor therefore authors all four spare planes against `Top Plane`, which always yields the
matrix form, and the writer overwrites the matrix with whatever frame the document declares —
including the identity frame, which is then decoded by `_matrix_frame` rather than `_minimal_frame`.

### The 121-byte frame block

`native._matrix_frame` already inverted this layout; `native._plane_frame_block` now writes it.

```
+0    3 × float64   origin, metres
+24   3 × float64   normal
+48   u8            1, the "a rotation matrix follows" flag
+49   3 × float64   matrix row 0  = (x_axis[0], y_axis[0], z_axis[0])
+73   3 × float64   matrix row 1  = (x_axis[1], y_axis[1], z_axis[1])
+97   3 × float64   matrix row 2  = (x_axis[2], y_axis[2], z_axis[2])
```

so the matrix is stored column-major over the frame axes, and `z_axis` appears twice — once at
`+24` and once as the third column. `_matrix_frame` requires the two to agree to within `1e-9`,
requires all four vectors to be unit and mutually orthogonal to within `1e-9`, and snaps any
component with `abs(value) <= 1e-12` to `0.0`. That snap is why a frame comparison in the writer
must be made at the decoder's precision rather than against the raw source doubles: FreeCAD's
`XZ_Plane` carries `y = (0, -2.220446049250313e-16, 1)`, which the decoder reports as `(0, 0, 1)`.

Overwriting the block of a coincident plane is not a wrong derived cache. Coincidence fixes only
the plane's point set; the in-plane basis and the normal sign are free, and the block is the only
place they live. Every frame the writer emits is coincident with a principal plane through the
origin, so it stays inside the freedom the authored constraint leaves open.

## 4. Equation encoding

`native.expression_equation_texts` renders a document's expression bindings as SOLIDWORKS
global-variable equations. It declines, leaving the capability a carrier, unless every
expression-bearing parameter's source is a single reference name and every parameter's value is a
finite length or number.

For each distinct referenced name, one equation carries its value; for each driven parameter, one
equation binds it to that name. Names are sanitised to `Kit_` plus the source with every
non-alphanumeric run replaced by `_`, disambiguated with a numeric suffix on collision. Unused
spares are rewritten to `"KitReserved<nn>"= 0`, which references nothing, so no spare is left
pointing at a renamed dimension.

For `PartDesignExample.FCStd` the 9 bindings become 7 + 9 = 16 equations, confirmed present in the
reopened part through `EquationMgr.Equation(i)`:

```
"Kit_Attributes002_Diameter"= 5mm
"Kit_Attributes002_Length"= 50mm
"Kit_Attributes002_ShankDiameter"= 3mm
"Kit_Attributes002_CuttingEdgeHeight"= 30mm
"Kit_SetupSheet_HorizRapid"= 0
"Kit_HorizFeed"= 0
"Kit_SetupSheet_VertRapid"= 0
"Kit_Sketch004_9"= "Kit_Attributes002_Diameter"
"Kit_Sketch004_10"= "Kit_Attributes002_Length"
"Kit_Sketch004_16"= "Kit_Attributes002_ShankDiameter"
"Kit_Sketch004_18"= "Kit_Attributes002_CuttingEdgeHeight"
"Kit_TC_5mm_Endmill_HorizRapid"= "Kit_SetupSheet_HorizRapid"
"Kit_TC_5mm_Endmill_LeadInFeed"= "Kit_HorizFeed"
"Kit_TC_5mm_Endmill_LeadOutFeed"= "Kit_HorizFeed"
"Kit_TC_5mm_Endmill_RampFeed"= "Kit_HorizFeed"
"Kit_TC_5mm_Endmill_VertRapid"= "Kit_SetupSheet_VertRapid"
```

The global-variable chain `moRelGlobalVar_c` → `moGlobalVarRefWrapper_c` → `moCompGlobalVar_c`
carries its left-hand side in the string itself (`Equations.md` §3), so retargeting needs no handle
and `moSkDimHandleValG2_c` never has to be decoded.

### The scattered-duplicate risk from `Equations.md` §5 does not apply here

`Camshaft` holds each equation string at several offsets because `Contents/Config-0` also carries
`moPMarkRecord_c` undo snapshots. The authored donor has no undo history: each of the 24 spare
strings appears **exactly once** in its `Contents/Config-0`, checked by
`.rescratch/sw/emit_meta_donor.py` before the offsets are recorded and re-checked by the writer,
which raises if a spare's serialized string is not unique.

## 5. Direction-axis selections

The five `ReferenceAxis` selections `PartDesignExample.FCStd` carries are direction references onto
a sketch axis, which is a different shape from the 38-byte edge/face selection entries
`native._edge_selections` decodes. They need no new record, because the native records already
determine them:

* an extrusion with no explicit direction spec extrudes along its profile sketch's normal, so the
  binding is `(operation, profile sketch, N_Axis)`. `Serialize.md` §1 item 1 records
  `moDirectionSpec_c` at `moEndSpec_c + 0x138` as null throughout the corpus, which is exactly the
  "no explicit direction reference" state;
* a revolution's axis is the single `profile_role == 2` line marker in its profile sketch. Its two
  `endpoint_indices` are positional indices into the sketch's marker list — the same convention
  `native._structural_rectangle_profiles` uses — so the axis direction in sketch coordinates is the
  difference of the two referenced markers' `coordinates_mm`. A vertical direction is `V_Axis`, a
  horizontal one `H_Axis`, anything else is not expressible.

`native.operation_axis_subelement` decodes this and `adapter._direction_axis_selections` emits it,
so the capability is native in both directions rather than only on the write side. For
`PartDesignExample` the decoded bindings are

```
(32, 26, N_Axis)  (40, 33, N_Axis)  (47, 41, N_Axis)  (54, 48, N_Axis)  (60, 55, V_Axis)
```

which is exactly the set the document declares once its feature and sketch ids are mapped through
the donor.

`revolution_axis_direction` falls back to the profile sketch's construction line only when
`NativeOperation.axis_source_kind` is `None`. `resolved.locate_features` leaves `axis_kind` null for
this donor even though the axis is a centreline in the profile sketch, so without the fallback the
revolve reports no axis at all.

## 6. Is `XZ_Plane` the same plane as Top Plane?

It is the same point set and a different oriented frame, and it gets its own record. FreeCAD's
`XZ_Plane` is `x = (1,0,0)`, `y = (0,-2.22e-16,1)`, `z = (0,-1,-2.22e-16)`; Top Plane is
`u = (1,0,0)`, `v = (0,0,-1)`, `n = (0,1,0)`. The normal is negated and `v` with it.

Three reasons not to collapse it onto object 3:

1. `Sketch002` sits on `XZ_Plane` and `Sketch004` on `XZ_Plane001`. A sketch reads its 2D
   coordinates in its plane's basis, so asserting Top Plane's `v` would mirror anything rebuilt
   from the frame.
2. `XZ_Plane` and `XZ_Plane001` are two distinct objects with the same frame. A frame-keyed or
   positional collapse cannot represent both, so the plane set would stop being a bijection and
   could not be proved as a set at all.
3. Replacing the frame comparison with a plane-equivalence test would certify the point set only,
   and stop certifying the basis.

Measured either way: with all four records present and object 3 left unclaimed, the written part
opens in SOLIDWORKS with 2 bodies at `584449.7323019444` mm³, `4.56e-9` relative to the FreeCAD
ground truth, and `Plane1`–`Plane4` appear as `RefPlane` features beside the three principal ones.

## 7. What is measured

| claim | evidence |
|---|---|
| the authored donor's geometry is unchanged | volume and body count identical before and after the additions; `locate_features` identical to the base donor |
| the written part still opens | `OpenDoc6` with `errors=0`, 2 bodies, `584449.732301944` mm³, control part measured identically before and after the batch |
| the equations exist | `EquationMgr.GetCount()` is 24 and `Equation(i)` returns the 16 encoded equations plus 8 reserved placeholders |
| the reference planes exist | the feature walk reports `RefPlane` for `Front Plane`, `Top Plane`, `Right Plane`, `Plane1`, `Plane2`, `Plane3`, `Plane4` |
| the selections resolve | every named feature is present with its profile sketch as a sub-feature, each profile sketch is selectable as `SKETCH`, and the revolve's axis is selectable as `Line1@Sketch5` / `EXTSKETCHSEGMENT` |

`IFeature.GetDefinition` is not reachable through late-bound dispatch — every call returns
`Member not found` — so the extrusion direction reference was not read back through
`IExtrudeFeatureData2.GetDirectionReference`. The profile-sketch binding that `N_Axis` asserts is
confirmed instead from the sub-feature list and from the decoded native records.
