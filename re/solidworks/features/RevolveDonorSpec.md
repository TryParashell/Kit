<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Revolve donors for `src/convert/adapters/solidworks/donor_library.py`

Written for the implementation agent. Field evidence is in `Revolve.md`; part-level evidence is in
`inventory.md` / `inventory.json`. Nothing here was verified in SOLIDWORKS — read §2 before
committing a donor.

---

## 1. What a revolve donor can and cannot do

| parameter                                                                                | status                    | how                                                                                                                                                                                                                                                     |
| ---------------------------------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| revolve **angle**                                                                        | **PATCHABLE**             | one `float64` in radians, located by the ordinal dimension-scalar rule; the two derived copies at `scalar+513` / `scalar+537` must be **left stale**                                                                                                    |
| axis **target** (repoint to another existing reference axis or sketch in the same donor) | **PATCHABLE**, unverified | `u32` feature id at `end-spec-object − 131` (reference axis) or `− 145` (sketch)                                                                                                                                                                        |
| **profile geometry**                                                                     | **PARTIALLY PATCHABLE**   | `float64` x/y pairs in the same 18-byte-prefixed coordinate record as extrudes, but arcs are unreadable (§7.2 of `Revolve.md`) and the role/class trailer values are undecoded — treat as inherit-only unless the donor's profile is pure line segments |
| boss ↔ cut                                                                               | **INHERIT ONLY**          | changes the class set (`moRevolution_c` ↔ `moRevCut_c`) and therefore every `su_CArchive` map index after it. Separate donors, no byte flip.                                                                                                            |
| end condition (one-direction / mid-plane / two-direction)                                | **INHERIT ONLY**          | `moRevEndSpec_c` is a 52-byte constant across the whole corpus; the code byte is not located                                                                                                                                                            |
| direction / reverse                                                                      | **INHERIT ONLY**          | same reason                                                                                                                                                                                                                                             |
| thin feature                                                                             | **INHERIT ONLY**          | same reason; the two `0.01` doubles in `moRevEndSpec_c` are a guess                                                                                                                                                                                     |
| which sketch entity is the centerline                                                    | **INHERIT ONLY**          | intra-sketch entity reference, opaque                                                                                                                                                                                                                   |
| axis derived from a cylindrical face                                                     | **INHERIT ONLY**          | same opaque face reference report 2 §3/§7 established for extrudes                                                                                                                                                                                      |
| axis = temporary / principal axis                                                        | **UNSUPPORTED**           | no corpus example                                                                                                                                                                                                                                       |
| adding or removing a revolve                                                             | **UNSUPPORTED**           | Grammar.md §8 items 1–3: object segmentation and map-index renumbering are unsolved                                                                                                                                                                     |

**Consequence:** a revolve donor is essentially a _one-parameter_ donor — the angle — plus an
optional axis repoint. That is much weaker than the extrude donors, which can also author the
profile, the depth, the direction and the end condition. Do not advertise more than this.

---

## 2. Read this before adding any donor: the version problem

Every one of the 40 revolve-bearing corpus parts is `swVersion` **13000** (23 parts) or **14000**
(17 parts) — see `.rescratch/revolve/versions.txt`. The existing donor library, the skeletons in
`.rescratch/grammar/skeletons/` and the whole extrude field map are **18000** (SOLIDWORKS 2025).

The archive-layer grammar plainly still holds across those versions: every locator in `Revolve.md`
works unmodified on 13000 and 14000 documents. What is **not** established is that a 13000/14000
resolved-features stream can be dropped into the 18000 container the donor pipeline builds and
opened. SOLIDWORKS _upgrades_ a legacy document when it opens it, which rewrites the stream, and
Grammar.md §1 already records that a wrong container signature triplet hard-crashes the
application.

Two options, in order of preference:

1. **Re-save the chosen corpus parts from SOLIDWORKS 2025** (open, rebuild, Save As to a new file),
   then extract the resolved-features stream from the re-saved 18000 document and use _that_ as the
   donor payload. Re-run `probe_revolve.py` against the re-saved part first: all the offsets in
   `Revolve.md` must still resolve, the angle must still read 360°, and the end-spec signature count
   must still equal the revolve count. If any of those fail, the upgrade changed the layout and the
   field map has to be re-derived on 18000.
2. **COM-author fresh donors** in SOLIDWORKS 2025 from a sketch plus a centerline, following the
   corpus2 methodology. This is cleaner (native 18000, simple profiles, and it lets you author the
   angle/end-condition/direction family that §4 of `Revolve.md` says is missing) but it is a
   SOLIDWORKS session, not static work. Enumerate the revolve method and its exact arity from
   `sldworks.tlb` first, the way `.rescratch/corpus2/scripts/probe_cut_signature.py` does for
   `FeatureCut4` — report 2 §0 records that guessing the arity of a SOLIDWORKS feature call costs a
   whole session, and I have not verified any revolve signature here.

Option 2 is what actually unblocks the end condition and direction fields, so if a SOLIDWORKS slot
is being scheduled anyway, spend it there.

---

## 3. Topology key

The existing key is `(operation, profile, support, end_condition)` per `DonorFeature`. Revolves need
one more axis of variation — the axis kind — and the existing `support` slot is the natural place
for it, because for a revolve the thing that matters is not what plane the sketch sits on but what
the profile is swept around.

Proposed constants to add alongside the existing ones:

```python
REVOLVE_BOSS_OPERATION = "revolve-boss"
REVOLVE_CUT_OPERATION = "revolve-cut"

SKETCH_AXIS_SUPPORT = "sketch-axis"
REFERENCE_AXIS_SUPPORT = "reference-axis"

FULL_REVOLUTION_END = "full-revolution"

REVOLVE_OPERATIONS = frozenset({REVOLVE_BOSS_OPERATION, REVOLVE_CUT_OPERATION})
REVOLVE_END_CONDITIONS = frozenset({FULL_REVOLUTION_END})
```

Key semantics:

- `operation` — `revolve-boss` or `revolve-cut`. Two distinct values because they are two distinct
  class sets (`Revolve.md` §6). Do **not** reuse the existing `boss` / `cut` values: those select
  extrude donors and the patch paths are different.
- `profile` — use the existing `POLYLINE_PROFILE_PREFIX` convention with the coordinate count, e.g.
  `polyline-11`. Every corpus revolve profile is a production polyline; none is a rectangle or a
  COM-authored circle. Only claim a profile as patchable if the donor's profile has no arcs.
- `support` — `sketch-axis` or `reference-axis`, per the slot the donor's revolve actually uses
  (`inventory.md` records this per feature). This is the field the matcher needs, because the two
  cases patch at different offsets.
- `end_condition` — `full-revolution` only. Every corpus revolve is 360° one-direction. Add
  `mid-plane` / `two-direction` / `thin` values only once a SOLIDWORKS-authored donor exists for
  them; a key value with no donor behind it is worse than a missing key.

`FULL_REVOLUTION_END` must **not** be added to `SUPPORTED_END_CONDITIONS` or
`DEPTHLESS_END_CONDITIONS` — those gate the extrude depth logic in `_validate_targets`, and a
revolve carries an angle, not a depth. The revolve path needs its own validation branch:
angle present and in `(0, 2π]`, no `depth_mm`, and `reversed` rejected rather than silently ignored
(the reverse flag is not located, so accepting it would be a lie).

---

## 4. Recommended donors

Screened for: exactly one revolve; sketch geometry actually present in the resolved lane; smallest
stream. `Idle_pulley.SLDPRT` and `Power_steering_pump_pulley.SLDPRT` are the smallest single-revolve
parts in the corpus and are **rejected** — their lane holds zero sketch-coordinate records and zero
`sg*` classes (`Revolve.md` §7.3), so there is no profile to patch and nothing to verify against.

### 4.1 Primary: a revolved boss about a sketch centerline

`examples/Random/Cylinder_heads/Timing_belt_roller.SLDPRT`

- lane `Contents/Config-0-ResolvedFeatures`, **25 200 bytes** — the smallest usable revolve stream
  in the corpus by a wide margin.
- one feature: `Revolve1`, id 48, `Type="Revolve"`, 360°, tree flags `0x40000000`.
- sketch `Sketch1` id 26; **16** sketch-coordinate records; 7 `sg*` classes.
- axis: `sketch-entity`, the `u32` at `end-spec-object − 145` naming `Sketch1`.
- proposed key: `(("revolve-boss", "polyline-16", "sketch-axis", "full-revolution"),)`
- near-identical sibling for a control pair: `Timing_belt_roller_2.SLDPRT`, 25 212 bytes, same
  shape. Use it exactly as `CONTROL_A`/`CONTROL_B` were used in report 1 — diff the two to measure
  the id/hash noise floor before trusting any byte you patch.

### 4.2 Primary: a revolved cut about a sketch centerline

`examples/Random/Crank/Journal_bearig_crank.SLDPRT`

- lane **50 787 bytes**; one feature `Cut-Revolve1`, `Type="Cut-Revolve"`, 360°, flags `0x40000000`.
- 28 sketch-coordinate records, 11 `sg*` classes; profile point count attributed to the revolve: 11.
- axis: `sketch-entity`.
- class set contains `moRevCut_c` and **not** `moRevolution_c` — the clean cut-only case.
- proposed key: `(("revolve-cut", "polyline-11", "sketch-axis", "full-revolution"),)`
- two near-identical siblings for control diffs: `Journal_bearig_conrod.SLDPRT` (50 795 bytes) and
  `Journal_bearig_camshaft.SLDPRT` (51 120 bytes). `Journal_bearig_camshaft` additionally owns an
  `Axis1` reference-axis feature that its revolve does **not** use — a useful negative control for
  the slot partition in §5 of `Revolve.md`.

### 4.3 Optional: a revolved cut about a reference axis

`examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/CUBIERTA DE TURBINA 1.SLDPRT`

- lane **574 406 bytes**. This is the smallest single-revolve reference-axis part, and it is 23×
  the primary boss donor. `TAPA RECTANGULAR DE LA CUBIERTA DE LA TURBINA.SLDPRT` (594 111) and
  `CUIETA DE ENTRADA DE GASES.SLDPRT` (712 277) are the alternatives; all three carry the same
  `Eje1` id 205 and the same `Cortar-Revolución1` id 240, so they are near-duplicates of each other.
- class set: `moRevCut_c`, `moRevEndSpec_c`, `moAngleParameter_c`, `moRefAxis_c`, `moCompRefAxis_c`,
  `moSurfaceAxisData_c` — i.e. the axis is derived from a cylindrical face, which is opaque.
- proposed key: `(("revolve-cut", "polyline-10", "reference-axis", "full-revolution"),)`

**Recommendation: do not ship this donor in the first pass.** Half a megabyte of base85 in a source
file for one opaque topology is a poor trade, and the axis it inherits is a face-derived axis nobody
can retarget. Ship 4.1 and 4.2, and add a reference-axis donor only when there is a caller that
needs it — ideally a small COM-authored one rather than this.

### 4.4 Explicitly not recommended

- `Idle_pulley.SLDPRT`, `Power_steering_pump_pulley.SLDPRT` — no sketch geometry in the lane.
- `10MM …Socket Head Screw.SLDPRT`, `6MM x 12MM …Screw.SLDPRT`, `8MM x 15mm …screw.SLDPRT`,
  `Spark_plug.SLDPRT` — 0 or 1 `sg*` classes, multiple revolves, McMaster library parts.
- `Engine_Block.SLDPRT` (8 revolves, 1 096 147 bytes), `CUBIERTA.SLDPRT` (3 revolves, 746 886,
  mixed axis kinds), `Cylinder_head.SLDPRT` (3 revolves, 589 029) — far too large and too coupled.
- Anything with more than one revolve, until multi-revolve donors are actually needed. Every
  additional revolve multiplies the map-index exposure.

---

## 5. Implementation notes

### 5.1 Locating the fields, in order

1. Enumerate tree nodes as `resolved.name_records` already does; a revolve node is one whose flags
   masked with `0x7FFFFFFF` equal `0x40000000` **and** whose name matches the revolve stems, or —
   better — whose id appears in `KeyWords` with `Type` in `{Revolve, Cut-Revolve}`. Flags alone are
   not sufficient (`Revolve.md` §2).
2. Enumerate the `moRevEndSpec_c` objects by searching for the 52-byte constant
   (`u32 1` + 24 zero bytes + `float64 0.01` + `float64 0.01` + 8 zero bytes). The count must equal
   the revolve count — assert it, do not assume it. Classify each as first-instance or later by
   testing the 20 bytes in front for the literal class definition.
3. Pair revolve nodes with end-spec objects in stream order.
4. The angle is the first dimension-scalar record after the revolve's tree node, named `D1`. Assert
   `degrees(value)` equals the `KeyWords` angle before writing anything.
5. The axis slot is `token − 145` if the `u32` there is a sketch node id with a plausible `time_t`
   in the following `u32`, else `token − 131` if it is a reference-axis node id. Assert exactly one
   matches.

### 5.2 Writing the angle

Write radians, one `float64`, at the scalar offset only. Leave `scalar+513` and `scalar+537` stale.
Then update the `KeyWords` `<Dimension Name="D1">` text to the new degrees value with the `°`
suffix — `KeyWords` and the stream must agree, exactly as Grammar.md §7 requires for extrudes.
Round-trip the patched stream through the locator and re-read the angle before returning.

Reject an angle outside `(0, 2π]`. A 360° donor patched to a partial angle changes the topology of
the result (a full revolution has no start/end face pair, a partial one does), and the end-condition
byte that would have to change is not located. **Treat any angle other than 360° as unverified until
the SOLIDWORKS run confirms it**, and consider gating it behind an explicit flag the way
`Part.write_depth_copies` is gated.

### 5.3 What must not be attempted

- Do not port the extrude flag anchors `scalar−824/−818` or `scalar−721/−715`. They do not apply
  (`Revolve.md` §4.2).
- Do not write the two derived angle copies.
- Do not try to convert a `revolve-boss` donor into a `revolve-cut` or vice versa.
- Do not patch a profile that contains arcs — `resolved.sketch_arcs()` cannot see them, so a partial
  write would leave the arc geometry inconsistent with the points.

### 5.4 Prerequisite fixes in `src/` (owned by another agent)

None of this works until `resolved.feature_kind` recognises a revolve, because `locate_features`
and therefore `patch_features` and `patch_donor` currently drop every revolve
(`Revolve.md` §8 defect 1). That fix cannot be "add `0x40000000` to `FEATURE_KIND_BY_FLAGS`" —
that word is already `SKETCH_FLAGS`, so the discriminator has to come from the class set plus the
node name, not from the flags. Design that before writing the donor entries.

---

## 6. Verification to schedule in SOLIDWORKS

In priority order. Items 1–2 are what turn this specification into something safe to ship.

1. **Author the missing differential family**: 90°, 270°, 360°, a reversed 90°, a mid-plane 90°, a
   two-direction 90°/45°, and a thin-feature revolve — all on the same simple sketch with a
   centerline. Diff them. That pins the end-condition code, the
   direction flag, the second-angle field, the thin-feature thickness and the sign rule for the two
   derived copies, all of which are currently opaque because the corpus is uniformly 360°.
2. **Open `Timing_belt_roller.SLDPRT` and `Journal_bearig_crank.SLDPRT` in SOLIDWORKS 2025, rebuild,
   Save As**, then re-run `probe_revolve.py` on the re-saved parts and confirm every locator still
   resolves on an 18000 document.
3. **Patch the angle** on the primary donors to 270° and 90° and measure the volume against the
   analytic expectation, with `Contents/Config-0-Partition` dropped so the solid is a genuine
   rebuild (Grammar.md §1).
4. **Repoint the axis** `u32` on a part that owns two reference axes (`CUBIERTA DE TURBINA 1.SLDPRT`
   has `Eje1` id 205 and `Eje2` id 206) and confirm the body moves to the other axis. That converts
   the axis reference from "confirmed as a reference" to "confirmed as patchable".
5. **Author a revolve about a temporary/principal axis** and about a cylindrical face, to cover the
   two cases the corpus does not contain.
