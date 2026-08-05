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

## Generated `.SLDASM` loadability, measured in SOLIDWORKS 2025 (rev 33.5.0)

First time a Kit-generated assembly has been handed to the vendor application. The writer reported
`vendor_loadable = True`; the measurement says otherwise. Every number below is in a JSON file under
`.rescratch/sw/out/measure_sldasm_*.json`, one fresh SOLIDWORKS process per file, with
`corpus/parts/BASELINE_40x20x10.SLDPRT` measured before and after every batch (`8000.000000000001`
mm³, 1 body, zero load errors — healthy in all six batches).

### Reference: the vendor original

`examples/Random/Pistons/Piston.SLDASM` — opened, no load errors or warnings, 4 components all
`fully-resolved`, 6 mates, rebuild true, 4 bodies, volume `94147.19377093748` mm³, centre of mass
`(0.000379, 32.304601, -0.000207)` mm. The three Kit-emitted sibling parts are byte-preserved vendor
`.SLDPRT` files and each opens cleanly: `88776.64112962573`, `140.58627124813898`,
`5089.380098815458` mm³ — summing with the doubled ring to the assembly volume exactly.

### The generated assembly does not open

`Piston.SLDASM` and `Conrod.SLDASM` written through the generated assembly path both kill the
SOLIDWORKS process during `OpenDoc6`: `com_error(-2147023170, 'The remote procedure call failed.')`,
reproduced across two batches. No load-error bits are returned because the reader never gets far
enough to set them.

### Which records the vendor reader actually rejects

Stream-level bisection against the vendor file, one measurement per variant.

Container writer is exonerated: rebuilding the vendor stream set through `container.build_sldprt`
with the vendor file as template opens and measures identically to the original.

Removing one vendor stream at a time from the vendor file:

| removed stream | result |
| --- | --- |
| `Contents/CMgr` | crash |
| `Contents/Config-0` | crash |
| `Contents/Config-0-ResolvedFeatures` | opens, but 0 components, 0 mates, 0 bodies, no mass |
| `Contents/Definition` | crash |
| `Contents/Config-0-LWDATA` | opens, unchanged |
| `Contents/DisplayLists` | opens, unchanged |
| `Contents/User Units Table` | opens, unchanged |
| `SwDocContentMgr/SwDocContentMgrInfo` | opens, unchanged |
| `docProps/ISolidWorksInformation.xml` | opens, unchanged |
| `swXmlContents/KeyWords` | opens, unchanged |

So of the ten streams `sldasm.unexpressed_native_records` enumerates, four are load-critical and six
are cosmetic.

Substituting one Kit-generated record at a time into the vendor file:

| swapped stream | result |
| --- | --- |
| `Contents/Config-0-ModelHeader` | crash |
| `Header2` | opens, unchanged |
| `Contents/CMgrHdr2` | opens, unchanged |
| `Contents/CnfgObjs` (empty, 12 bytes) | opens, unchanged |
| `Contents/Config-0-MatesList` | opens, **0 mates** |
| `swXmlContents/COMPINSTANCETREE` | opens, unchanged |

`Header2` and `Contents/Config-0-ModelHeader` carry identical bytes in both files, yet only the
`Config-0-ModelHeader` substitution is fatal: the reader consumes the configuration copy and treats
`Header2` as a stamp.

### How far the generated file can be pushed

Generated streams plus the four load-critical vendor streams plus the vendor
`Contents/Config-0-ModelHeader`/`Header2` **opens**: 4 components `fully-resolved`, 4 bodies, volume
`94147.19377093748` mm³, centre of mass `(0.000379, 32.304601, -0.000207)` mm — bit-for-bit the
vendor figures. Adding the six cosmetic streams changes nothing. Keeping the generated model header
and supplying only the four streams crashes again.

That fixes the boundary exactly: Kit's generated `COMPINSTANCETREE`, `CMgrHdr2`, `CnfgObjs` and
container are all acceptable to the vendor reader. What is missing is (a) the four streams Kit never
synthesises, (b) a vendor-acceptable `Contents/Config-0-ModelHeader`, and (c) mate records the reader
consumes — in every variant that opens, Kit's `Contents/Config-0-MatesList` yields 0 mates against
the vendor's 6, so `Capability.ASSEMBLY_MATES` is claimed but not delivered.

### Why the decode-based proxies passed a file that crashes

`envelope_complete` round-trips the generated header through `decode_native_model_header`, but that
decoder cannot read the real vendor assembly header at all — it raises
`native SOLIDWORKS header layout is unexpected` on
`examples/Random/Pistons/Piston.SLDASM`'s `Contents/Config-0-ModelHeader`. The check therefore only
proves Kit round-trips its own dialect. `structure_complete` and the `COMPINSTANCETREE` re-parse
behind `Capability.ASSEMBLIES` are equally self-referential; the substitution table above shows both
of those streams are in fact fine, so neither was ever the thing at risk.

`vendor_loadable` on the generated assembly path is now gated on
`_ASSEMBLY_READER_REQUIRED_STREAMS` being present and `_VENDOR_REJECTED_ASSEMBLY_RECORDS` being
absent, and the writer emits `sldasm.vendor_reader_rejects` naming each gap. The compatibility label
still reads `native-assembly-with-kit-neutral`, because the native records are genuinely there — they
are just not yet loadable.
