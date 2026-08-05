# Donors awaiting a SOLIDWORKS measurement

`Donor.measured` is flipped by hand only after a part written from that donor has been opened in
SOLIDWORKS, rebuilt with `Contents/Config-0-Partition` dropped, and its mass properties compared
against the analytic expectation. `donor_match` refuses to emit native records from a donor with
`measured=False`, so an unmeasured donor is inert: it declines, it never ships wrong geometry.

## The two donors added for revolve support

Both were COM-authored in SOLIDWORKS 2025 (`swVersion` 18000), so the 13000/14000 version blocker
recorded in `.rescratch/revolve/donor_spec.md` §2 does not apply to them. The corpus parts that
document names as candidate donors (`Timing_belt_roller.SLDPRT`, `Journal_bearig_crank.SLDPRT`) were
**not** used: an 18000 stream that already exists is strictly better than hosting a legacy stream in
an 18000 container, which is the thing nobody has verified.

| donor | source part | topology key | what to measure |
|---|---|---|---|
| `revolve_full` | `.rescratch/donors/parts/revolve_full.SLDPRT`, lane 12 135 B, `Revolve1` id 31 / `Sketch1` id 26 | `(("revolve-boss", "rectangle", "sketch-axis", "full-revolution"),)` | patch the profile rectangle to `(9, −8) … (21, 8)` mm and keep 360°; expect an annulus of `π(21² − 9²)·16 = 18 095.57 mm³` |
| `boss_revcut` | `.rescratch/donors/parts/boss_revcut.SLDPRT`, lane 17 713 B, `Boss-Extrude1` id 32 / `Sketch1` id 26, `Cut-Revolve1` id 39 / `Sketch2` id 33 | `(("boss", "rectangle", "front", "blind"), ("revolve-cut", "rectangle", "sketch-axis", "full-revolution"))` | patch the boss to `(−23, −12) … (23, 12)` mm × 12 mm blind and the revolved cut to `(−28, 0) … (28, 4)` mm about the sketch X axis; expect `46·24·12 − π·4²·46 = 13 248 − 2 312.21 = 10 935.79 mm³` |

`.rescratch/donors/check_revolve.py` writes exactly those two patched streams and re-reads them, so
the streams to measure can be produced without touching `src/`.

### Two things the measurement has to confirm, beyond the volume

1. **The boss in `boss_revcut` is declared `blind` but the donor stream holds a mid-plane boss**
   (end condition code 6). The donor key says `blind` on purpose, because `donor_key()` folds a
   mid-plane target onto a blind key and a `mid-plane` donor key is unreachable. Patching writes
   code 0 over code 6. GRAMMAR.md §5.3 measured blind → mid-plane; mid-plane → blind is the same
   byte in the other direction and is **not** yet measured. Confirm the boss rebuilds 12 mm one
   sided, not 6 mm either side.
2. **A partial angle.** `patch_donor` accepts any angle in `(0, 360]` and writes it as radians at
   the `D1` scalar +0 only, leaving `scalar+513` / `scalar+537` stale. Every corpus revolve is 360°,
   so a partial angle is unverified end to end: `moRevEndSpec_c` is a 52-byte constant and the
   end-condition byte for a one-direction partial revolve is not located. Measure `revolve_full`
   patched to 270° and to 90° and check the volume scales linearly. If a partial angle does **not**
   rebuild correctly, the fix is to narrow `MAXIMUM_REVOLUTION_DEGREES` handling in
   `donor_library._revolve_edit` to 360° exactly — `donor_match` already refuses anything else on
   the read side, so the exposure is limited to a direct `patch_donor` caller.

### Not attempted, and why

* **Reference-axis revolves.** `REFERENCE_AXIS_SUPPORT` exists as a key value but no donor carries
  it. The only corpus candidates derive their axis from a cylindrical face, which is opaque, and the
  smallest is 574 kB of base85 for one untargetable topology. `_revolve_edit` rejects a target whose
  support is not the donor's, so the constant cannot be selected by accident.
* **Axis repointing.** The donor's axis construction line is a `class = 1` coordinate record, which
  `sketch_points()` deliberately excludes, so the axis is inherit-only. `Donor.axis_directions`
  records the inherited direction per feature — `(0, 1)` for `revolve_full`, `(None, (1, 0))` for
  `boss_revcut` — and `_revolve_edit` refuses a target that wants a different one.

## The pre-existing unmeasured donors, unchanged

None of these were touched. Listed so the measurement session is one pass.

`boss2_front_rect_blind`, `boss3_front_rect_blind`, `boss4_front_rect_blind`, `boss_cut_boss`,
`boss_boss_cut_cut` — deliberately left unmeasured: a boss in position ≥ 2 makes a **separate body**
(measured 32 000 mm³ / 2 bodies against 28 800 expected), because merge-result lives in the opaque
`moICE_c` body. Do not flip these until that is decoded.

`boss_cut_through`, `boss_cut_midplane`, `boss_midplane`, `rect_hole_boss`, `poly6_boss`,
`poly12_cut_through`, `boss_cut_cut_blind`, `boss_cut_cut_cut_through` — never measured, no known
blocker.

Measured and shipping today: `boss1_front_rect_blind`, `boss_cut`, `boss_cut_cut`,
`boss_cut_cut_cut`, `circle_boss`, `boss_top_plane`, `boss_right_plane`.
