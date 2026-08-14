# SOLIDWORKS measurements

Every number below is `IModelDocExtension::GetMassProperties(1, status)[3] × 1e9` (volume, mm³)
after `ForceRebuild3(False)`, read in a **fresh SOLIDWORKS subprocess per file** via
`tests/oracle/Session.py`. Every file was built with **`Contents/Config-0-Partition` deleted**, so
every volume is a genuine rebuild from `Contents/Config-0-ResolvedFeatures` +
`swXmlContents/KeyWords`, not a cached body.

Harness: `Measure.py` → `MeasureOne.py`. Raw JSON in `out/measure_*.json`.
`status` values:

* `measured` — SOLIDWORKS opened and reported mass properties
* `solidworks-crashed-on-open` — `OpenDoc6` raised
  `com_error(-2147023170, 'The remote procedure call failed.')`, i.e. the SOLIDWORKS process died
  mid-open
* `timeout` / `session-unavailable` — harness flake, no verdict on the file

**Read §4 before drawing conclusions from any `crashed-on-open` result.** Late in the session the
SOLIDWORKS installation degraded to the point where a pristine SOLIDWORKS-authored donor also
crashes on open, so crash results are only trustworthy from the runs where a control passed.

---

## 1. Capability experiments — byte edits to donors (`experiments.py`, `parts/`)

These attack what donor-patching could not do. All are same-length byte overwrites except `E10`.
Taken from `out/MeasureExperiments.json` and `out/MeasureRetryTwo.json`, both from the healthy
part of the session (adjacent cases in the same batches measured correctly).

| # | edit | donor | predicted mm³ | measured mm³ | bodies | verdict |
|---|---|---|---|---|---|---|
| E1 | feature-2 tree flags `0x400201CA` → `0x40000140` (cut → boss) | `CUTBASE_cd5` | 8500 | — | — | **crashes SOLIDWORKS** (2 independent runs) |
| E2 | feature-2 tree flags → cut **and** direction byte 0 → 1 | `TWOPAD_d5` | 7500 | — | — | **crashes SOLIDWORKS** (2 runs) |
| E3 | feature-2 end-condition byte 0 → 1 (blind → ThroughAll), dimension object left in place | `CUTBASE_cd5` | 7000 | — | — | **crashes SOLIDWORKS** (2 runs) |
| E4 | feature-2 end-condition byte 0 → 6 (blind → MidPlane) | `CUTBASE_cd5` | 7750 | **7750.000000000002** | 1 | **works** |
| E5 | sketch plane id 2 → 3 (Front → Top), id + axis only | `BASELINE_40x20x10` | 8000 | opened, **0 bodies** | 0 | see note |
| E6 | sketch plane id 2 → 4 (Front → Right), id + axis only | `BASELINE_40x20x10` | 8000 | **8000.000000000001**, centre `(5, 0, 0)` mm | 1 | **works** |
| E7 | feature-1 direction byte + `moFromEndSpec_c+29`, 0 → 1 | `BASELINE_40x20x10` | 8000 | **8000.000000000001**, centre `(0, 0, −5)` mm | 1 | **works** |
| E8 | feature-1 end-condition byte 0 → 6 (MidPlane) | `BASELINE_40x20x10` | 8000 | **8000.000000000001**, centre `(0, 0, 0)` mm | 1 | **works** |
| E9 | swap two 119-byte `moCompFeature_c` entry pairs (reorder the tree) | `THREEFEATURE_pad_cut_pad` | 7756 | **7756.0000000000055** | 1 | **works** |
| E10 | delete the last `moCompFeature_c` entry pair (−238 bytes) | `THREEFEATURE_pad_cut_pad` | 7500 | — | — | **crashes SOLIDWORKS** (2 runs) |

### What these establish

**New capability, proven.** End condition (E4, E8), direction (E7) and sketch support plane (E6)
are single-byte in-place edits that SOLIDWORKS honours exactly, verified by volume *and* by centre
of mass. None had been round-trip-tested before: report 2 §10 lists the end-condition and
direction switches as "read-back verified, switching not round-trip-tested", and lists changing a
sketch's support as needing real serialization.

**Tree order comes from `moCompFeature_c`.** E9 reordered the array; SOLIDWORKS returned the tree
in the new order with one body and the correct volume. With the 51/51 id agreement in
`Grammar.md` §3, that record is fully specified.

**boss ↔ cut is NOT the tree flags word.** E1 and E2 both kill the process. `A3` below goes
further: in the first authored batch, writing *cut* flags onto a **boss** skeleton did not
crash — SOLIDWORKS silently **ignored** it and rebuilt a boss, measuring 18000 mm³ where a cut
would have given 14800. So `0x40000140` / `0x400201CA` is a tree annotation that has to *agree*
with the operation; it does not select it. The operation lives in the `moExtrusion_c` / `moICE_c`
body, which was not decoded. `Serialize.py` now refuses an operation its skeleton does not have.
This corrects the natural reading of report 2 §7.2.

**blind → ThroughAll is not a byte flip.** E3 crashes, confirming report 2 §5.5: ThroughAll
*removes* the dimension object and the `moEndFace3IntSurfIdRep_c` class record. A ThroughAll
feature needs a ThroughAll skeleton — which `A6` uses successfully.

**Length changes need index renumbering.** E10 is the only length-changing edit and the only crash
predicted by theory: removing two objects shifts `su_CArchive`'s combined class/object map index
for every class defined later, so every `0x8000|i` class-reference token after `moCompFeature_c`
becomes wrong. This is direct experimental confirmation of `Grammar.md` §2.3 and is exactly why
feature *count* is still blocked.

**Front → Top (E5).** The bare id+axis edit opened with no body, while the same change as part of
the full authored field set worked (`A7`: 8000 mm³, centre `(0, 5, 0)`). Front is the one plane
whose 9-double basis at `moSketchChain_c + 224` is **omitted**, so a Front donor has no basis to
reorient; Right survives the bare edit (E6) and Top does not.

---

## 2. From-scratch authored parts (`Serialize.py`, `author_parts.py`, `authored/`)

`Serialize.py` takes a feature-tree description, selects a topology skeleton, and writes every
authored field: tree-node flags and ids, `moCompFeature_c` entry ids and timestamps, sketch corner
/ circle-point coordinates, the depth scalar, the direction and end-condition bytes, and the sketch
plane id + axis. `swXmlContents/KeyWords` and `swXmlContents/Features` are **generated as XML from
scratch**, not copied.

Best measurement per case, with the batch it came from:

| case | features | skeleton | predicted mm³ | measured mm³ | rel. error | bodies | run |
|---|---|---|---|---|---|---|---|
| A1 | 1 boss, rect 50×30, blind 12 | `BASELINE_40x20x10` | 18000 | **18000.0** (as `D4`, §3) | 0 | 1 | `measure_diagnose` |
| A2 | 2 bosses, rect 50×30×12 + rect 20×20×8 reversed | `PADPLANE_rev_d5` | 21200 | **21200.000000000004** | 1.7e-16 | 1 | `authored2`, `authored4` |
| A3 | boss rect 50×30×12 + **cut** rect 20×20×8 reversed | `CUTBASE_cd5` | 14800 | **14799.999999999996** | 2.7e-16 | 1 | `authored2`, `authored4` |
| A4 | 1 boss, **circle** r=15, blind 10 | `CIRCLE_r10` | 7068.583470577034 | **7068.583470577033** | 1.4e-16 | 1 | `authored` |
| A5 | boss 55×28×13 + cut 11×11×5 + face boss 7×7×4 | `THREEFEATURE_pad_cut_pad` | 19611 | **20215.999999999996** | see §2.3 | 1 | `authored4` |
| A6 | boss 45×22×9 + **ThroughAll** cut 9×9 | `CUTTHROUGH_s10` | 8181 | **8181.0** | 0 | 1 | `authored2` |
| A7 | 1 boss on the **Top plane**, rect 40×20, blind 10 | `BASELINE_40x20x10` | 8000 | **8000.000000000001**, centre `(0, 5, 0)` mm | 1.2e-16 | 1 | `authored2`, `authored4` |
| A8 | 1 boss, **MidPlane** 10 | `BASELINE_40x20x10` | 8000 | **8000.000000000001**, centre `(0, 0, 0)` mm | 1.2e-16 | 1 | `authored2`, `authored4` |
| A9 | **4** bosses on the Front plane | — | — | **refused at emit time** | | | |

A9 is the honest limit. `Serialize.py` raises

```
SerializeError: no skeleton matches shape (('boss','rectangle','plane',True) x 4);
available: … (8 skeletons, maximum 3 features)
```

rather than emitting a stream that would crash SOLIDWORKS, for exactly the reason E10 demonstrates.

### 2.1 What the passing cases prove

Seven from-scratch emissions match to floating-point exactness, and between them they exercise
every authored field:

* **circle profile** written as centre + a 17° circumference point (A4) — the radius genuinely is
  not stored and reconstructing the point is sufficient
* **two features** with independent profiles, depths and directions (A2)
* **a cut**, with the `KeyWords` document generated from scratch (A3)
* **ThroughAll**, with no dimension scalar anywhere and no `<Dimension>` element (A6)
* **a non-Front sketch plane** (A7), confirmed by centre of mass, not only volume
* **MidPlane** (A8), confirmed by centre of mass at the origin
* **the full authored XML pair** on a resized single boss (A1 via D4)

### 2.2 Bug found and fixed: writing the derived depth copies breaks the rebuild

The first authored batch wrote all six depth copies at scalar `+{0,+72,+398,+422,+560,+584}` with
the fixed sign pattern `(+,+,−,−,+,+)` that report 1 §5.1 records for a *blind forward* feature.
Measured outcome: A2 opened with 0 bodies, A5 and A8 crashed on open, A3 returned 18000 instead of
14800.

The sign pattern is **not** constant. Report 1 already notes that scalar `+72` is `+depth`
blind-forward, `−depth` reversed and `+depth/2` for MidPlane, and that `+398/+422` flip with
direction. Writing the blind-forward pattern onto a reversed or MidPlane feature writes a
self-contradictory annotation.

Restricting the writer to the depth **parameter** (`+0`) and leaving the five annotation copies
stale flipped A2, A3 and A8 from failing to exact. That is now the default
(`Part.write_depth_copies=False`), and `moBBoxCenterData_c` is likewise off by default
(`Part.write_bbox_cache=False`).

Measured rule: **a stale derived cache is safe; a wrong one is not.** Do not write the five derived
depth copies or the bbox cache unless the full end-condition- and direction-dependent sign rule is
implemented.

### 2.3 Bug found and fixed: the `KeyWords` stream prefix

The authored `swXmlContents/KeyWords` was being written with a UTF-8 BOM (`EF BB BF`) and `\n\n`
after the XML declaration. The real stream starts with a **single `0x86` tag byte** and uses
**CRLF**:

```
86 3c 3f 78 6d 6c … 3f 3e 0d 0a 3c 4b 65 79 77 6f 72 64 73
^^                                ^^^^^
0x86                              \r\n
```

`swXmlContents/Features` has no prefix byte but also uses CRLF, and both streams end with a
trailing CRLF. With that corrected, the authored `KeyWords` for A1 differs from the donor's only
in the transient session id and the depth digit:

```
--- donor
+++ authored
-<Keywords id="1785762594" Name="Part70">
+<Keywords id="1785842425" Name="Part1">
-<Dimension Name="D1">10</Dimension>
+<Dimension Name="D1">12</Dimension>
```

That is a byte-exact structural reproduction of the stream, and §3 shows it opens and measures
exactly. Before the fix, A1 crashed reproducibly on open in a clean session, three times.

### 2.4 A5: the cut direction, not the serialization

A5 measured **20215.999999999996** where 19611 was predicted. The difference is exactly
`11 × 11 × 5 = 605` mm³ — the cut. `55 × 28 × 13 + 7 × 7 × 4 = 20216`, so features 1 and 3 applied
and feature 2 removed nothing. Report 2 §0 records that a cut sketched on the Front Plane with the
material at `z > 0` needs the reversed direction; A3 sets `reversed=True` on its cut and measures
exactly, A5 did not. `author_parts.py` now sets `reversed=True` on A5's cut, which predicts 19611.
**That corrected file was built but never measured** — the environment failed first (§4). A5 is
therefore not a serialization failure but it is also not proven.

---

## 3. A1 isolation (`diagnose_a1.py`, `diagnose/`)

Built to find why A1 crashed while A7 and A8, on the same skeleton, measured exactly. Four
variants of the single-boss part, all measured after the `0x86`/CRLF fix
(`out/MeasureDiagnose.json`):

| variant | change | authored XML | predicted mm³ | measured mm³ | bodies |
|---|---|---|---|---|---|
| D1 | depth only, 10 → 12 | yes | 9600 | **9600.000000000002** | 1 |
| D2 | rectangle only, 40×20 → 50×30 | yes | 15000 | **14999.999999999998** | 1 |
| D3 | both, `KeyWords`/`Features` inherited | no | 18000 | **18000.0** | 1 |
| D4 | both, `KeyWords`/`Features` authored | yes | 18000 | **18000.0** | 1 |

`D4` is A1's exact configuration. All four exact, and `D3` vs `D4` shows the authored XML pair is
interchangeable with the donor's. This is the strongest single result in the set: a fully authored
side-stream pair plus authored resolved-stream fields, rebuilt from the feature stream with the
Parasolid cache deleted, to 0 ulp.

---

## 4. Environment failure and the control experiment

After roughly 25 SOLIDWORKS launches, most of them following a deliberate hard crash and a
`taskkill /F`, the installation stopped opening documents at all. The control:

```
CONTROL: .rescratch/corpus/parts/BASELINE_40x20x10.SLDPRT   (pristine, SOLIDWORKS-authored)
  com_error(-2147023170, 'The remote procedure call failed.')
```

repeated after a 150-second settle and a full process sweep. That donor had opened and measured
correctly many times earlier in the session. So:

* every `crashed-on-open` in `out/MeasureAuthoredThree.json` and the final single-file runs is
  **environmental** and carries no information about the files
* the crash verdicts in §1 (E1, E2, E3, E10) are from `measure_experiments` and `measure_retry2`,
  in which neighbouring cases measured correctly, so they stand
* A5's corrected build and a fresh A1/A4/A6 confirmation are the only outstanding measurements

Recovery needs a machine reboot or a SOLIDWORKS settings reset, which was not attempted here.

---

## 5. Aggregate

| | count |
|---|---|
| capability experiments measured exactly as predicted | **5** (E4, E6, E7, E8, E9) |
| capability experiments that reproducibly crash SOLIDWORKS | **4** (E1, E2, E3, E10) |
| capability experiments that open with no body | **1** (E5) |
| from-scratch parts measured exactly as predicted | **7** (A1 via D4, A2, A3, A4, A6, A7, A8) |
| from-scratch parts refused at emit time by design | **1** (A9) |
| from-scratch parts diagnosed but not re-measured | **1** (A5) |
| isolation variants measured exactly as predicted | **4** (D1–D4) |

Worst relative error among the exact matches: **2.7e-16**, eleven orders of magnitude inside the
1e-9 target.
