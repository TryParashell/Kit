<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

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

| donor          | source part                                                                                                                                  | topology key                                                                                                | what to measure                                                                                                                                                                                     |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `revolve_full` | `.rescratch/donors/parts/revolve_full.SLDPRT`, lane 12 135 B, `Revolve1` id 31 / `Sketch1` id 26                                             | `(("revolve-boss", "rectangle", "sketch-axis", "full-revolution"),)`                                        | patch the profile rectangle to `(9, −8) … (21, 8)` mm and keep 360°; expect an annulus of `π(21² − 9²)·16 = 18 095.57 mm³`                                                                          |
| `boss_revcut`  | `.rescratch/donors/parts/boss_revcut.SLDPRT`, lane 17 713 B, `Boss-Extrude1` id 32 / `Sketch1` id 26, `Cut-Revolve1` id 39 / `Sketch2` id 33 | `(("boss", "rectangle", "front", "blind"), ("revolve-cut", "rectangle", "sketch-axis", "full-revolution"))` | patch the boss to `(−23, −12) … (23, 12)` mm × 12 mm blind and the revolved cut to `(−28, 0) … (28, 4)` mm about the sketch X axis; expect `46·24·12 − π·4²·46 = 13 248 − 2 312.21 = 10 935.79 mm³` |

`.rescratch/donors/check_revolve.py` writes exactly those two patched streams and re-reads them, so
the streams to measure can be produced without touching `src/`.

### Two things the measurement has to confirm, beyond the volume

1. **The boss in `boss_revcut` is declared `blind` but the donor stream holds a mid-plane boss**
   (end condition code 6). The donor key says `blind` on purpose, because `donor_key()` folds a
   mid-plane target onto a blind key and a `mid-plane` donor key is unreachable. Patching writes
   code 0 over code 6. Grammar.md §5.3 measured blind → mid-plane; mid-plane → blind is the same
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

- **Reference-axis revolves.** `REFERENCE_AXIS_SUPPORT` exists as a key value but no donor carries
  it. The only corpus candidates derive their axis from a cylindrical face, which is opaque, and the
  smallest is 574 kB of base85 for one untargetable topology. `_revolve_edit` rejects a target whose
  support is not the donor's, so the constant cannot be selected by accident.
- **Axis repointing.** The donor's axis construction line is a `class = 1` coordinate record, which
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

| removed stream                        | result                                              |
| ------------------------------------- | --------------------------------------------------- |
| `Contents/CMgr`                       | crash                                               |
| `Contents/Config-0`                   | crash                                               |
| `Contents/Config-0-ResolvedFeatures`  | opens, but 0 components, 0 mates, 0 bodies, no mass |
| `Contents/Definition`                 | crash                                               |
| `Contents/Config-0-LWDATA`            | opens, unchanged                                    |
| `Contents/DisplayLists`               | opens, unchanged                                    |
| `Contents/User Units Table`           | opens, unchanged                                    |
| `SwDocContentMgr/SwDocContentMgrInfo` | opens, unchanged                                    |
| `docProps/ISolidWorksInformation.xml` | opens, unchanged                                    |
| `swXmlContents/KeyWords`              | opens, unchanged                                    |

So of the ten streams `sldasm.unexpressed_native_records` enumerates, four are load-critical and six
are cosmetic.

Substituting one Kit-generated record at a time into the vendor file:

| swapped stream                        | result             |
| ------------------------------------- | ------------------ |
| `Contents/Config-0-ModelHeader`       | crash              |
| `Header2`                             | opens, unchanged   |
| `Contents/CMgrHdr2`                   | opens, unchanged   |
| `Contents/CnfgObjs` (empty, 12 bytes) | opens, unchanged   |
| `Contents/Config-0-MatesList`         | opens, **0 mates** |
| `swXmlContents/COMPINSTANCETREE`      | opens, unchanged   |

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

## Donor-carried `.SLDASM` writes, measured in SOLIDWORKS 2025 (rev 33.5.0)

Follow-up to the section above. Numbers live in `.rescratch/sw/out/measure_asmdonor_*.json`, one
fresh SOLIDWORKS process per file, `corpus/parts/BASELINE_40x20x10.SLDPRT` measured before and after
every batch (`8000.000000000001` mm³, 1 body, zero load errors — healthy in all four batches).

### The write path already carries the donor; nobody had opened the result

The crash measured earlier was the **source-less** assembly path (`.rescratch/gen_sldasm2.py` strips
`solidworks_source_*` from the document metadata before writing). When a `.SLDASM` is read and
written back, `_source_template` returns the vendor bytes and `_generated_streams` hands them to
`_patch_native_template`, which starts from the complete vendor stream set. All six recipe streams —
`Contents/CMgr`, `Contents/Config-0`, `Contents/Config-0-ResolvedFeatures`, `Contents/Definition`,
`Contents/Config-0-ModelHeader`, `Header2` — come through byte-identical, and Kit's rejected
synthesised model header is never written.

`write_document(read_sldprt("examples/Random/Pistons/Piston.SLDASM"), out)` produces a 45-stream file
that differs from the vendor original in exactly three streams: `Kit/Interchange`, `Kit/Native`,
`swXmlContents/COMPINSTANCETREE`.

| file                             | opened | load errors | load warnings | components | states           | mates | rebuilt | bodies | volume mm³          | centre mm                                                               |
| -------------------------------- | ------ | ----------- | ------------- | ---------- | ---------------- | ----- | ------- | ------ | ------------------- | ----------------------------------------------------------------------- |
| Kit-written `Piston.SLDASM` (b1) | yes    | none        | none          | 4          | 4 fully-resolved | 6     | true    | 4      | `94147.19377093749` | `(0.0003789180878327792, 32.304601496316025, -0.000206795236149518)`    |
| Kit-written `Piston.SLDASM` (b3) | yes    | none        | none          | 4          | 4 fully-resolved | 6     | true    | 4      | `94147.19377093748` | `(0.00037891808783261424, 32.30460149631602, -0.00020679523614970235)`  |
| vendor `Piston.SLDASM` (b3)      | yes    | none        | none          | 4          | 4 fully-resolved | 6     | true    | 4      | `94147.19377093746` | `(0.00037891808783228843, 32.304601496316025, -0.00020679523614969687)` |

Volume and centre of mass agree with the vendor original to ~1e-16 relative. Six mates, not the zero
the synthesised `Contents/Config-0-MatesList` yields — the donor mate records come through intact.

### SOLIDWORKS ignores `COMPINSTANCETREE` placement

This is the correctness hazard, and it was shipping. `_patch_assembly_instances` rewrites component
placement **only** in `swXmlContents/COMPINSTANCETREE`; the load-critical binary streams are carried
verbatim. Kit's own reader reads placement back out of `COMPINSTANCETREE`, so every decode-based
proxy agreed and the writer reported `vendor_loadable = True`, `native-template`.

Shifting `Piston_shaft-1` (5089.380098815458 mm³ of 94147.19377093749 mm³) by +50 mm in Y should move
the assembly centre of mass in Y by 2.703 mm, to ≈35.008.

| file                  | opened                           | components | states           | mates | bodies | volume mm³          | centre mm                                                               |
| --------------------- | -------------------------------- | ---------- | ---------------- | ----- | ------ | ------------------- | ----------------------------------------------------------------------- |
| shaft moved +50 mm Y  | yes                              | 4          | 4 fully-resolved | 6     | 4      | `94147.19377093749` | `(0.000378918087832499, 32.304601496316025, -0.00020679523614945986)`   |
| one instance removed  | yes                              | 4          | 4 fully-resolved | 6     | 4      | `94147.19377093746` | `(0.00037891808783270574, 32.304601496316025, -0.00020679523614959046)` |
| source-less generated | **no** — crash during `OpenDoc6` | —          | —                | —     | —      | —                   | —                                                                       |

The moved file's centre of mass is the donor's, unchanged, to the last digit. The reader takes
placement from `Contents/Config-0-ResolvedFeatures` and never consults the patched XML. The
three-instance document likewise still shows four components. So a verbatim donor carry ships the
**donor's** assembly, and any document that diverges from the donor must be declined — patching
`COMPINSTANCETREE` is not a way to express an edit to the vendor reader.

### The gate that now applies

`vendor_loadable` on the donor assembly path requires all of:

- the four load-critical streams present, and every donor stream byte-identical in the output except
  `Kit/Interchange`, `Kit/Native`, `Kit/ResolvedFeatures` and `swXmlContents/COMPINSTANCETREE`;
- the document's root definition, definition list, instance list and per-instance values (transform,
  configuration, suppression, visibility, BOM flags, order) equal to those decoded from the
  **unpatched** donor;
- no mate record rewritten in a donor stream.

Anything else emits `sldasm.vendor_reader_rejects` naming the gap, and reports
`vendor_loadable = False` with compatibility `native-source-with-kit-neutral`. Measured outcomes:
`donor_instance_diverged:sldasm:instance:11` for the moved shaft,
`donor_instance_order_diverged, donor_instance_diverged:sldasm:instance:11` for the removed instance,
and the four `absent_vendor_stream:` entries plus
`vendor_rejected_record:Contents/Config-0-ModelHeader` for the source-less case.

### `V8_engine.SLDASM`

`examples/Random/V8_engine.SLDASM` writes a 52-stream donor-carried file with 53 sibling parts. It
declines for two independent reasons: 14 components are Toolbox parts with no reachable source, so
the bundle is incomplete and the write downgrades to a carrier; and the output **adds**
`Contents/Config-0-Partition`, a stream the vendor assembly does not have, which the gate reports as
`donor_stream_added:Contents/Config-0-Partition`.

Measured anyway, since a declined file that opens is worth knowing about:

| file | opened | load errors | load warnings | components | states | mates | rebuilt | bodies | volume mm³ | centre mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vendor `V8_engine.SLDASM` | yes | none | `read-only` | 358 | 358 fully-resolved | 619 | true | 391 | `30996938.730483357` | `(20.270257724271392, 171.02270374521262, 3.648910118394005)` |
| Kit-written `V8_engine.SLDASM` | yes | none | `read-only`, `drawing-sheet-in-viewonly` | 358 | 358 fully-resolved | 619 | true | 391 | `30996938.730483353` | `(20.270257724271357, 171.02270374521115, 3.648910118404377)` |

It opens, and matches the vendor to ~1e-16 relative — the added partition stream did no harm here,
and this machine's SOLIDWORKS resolved the Toolbox components from its own library. Neither fact is
a licence to claim `vendor_loadable`: the shipped bundle is not self-contained, so the file only
resolves on a machine that already has the Toolbox parts. The added-partition allowance is left
gated on purpose; relaxing it needs measurements on more than one file.
