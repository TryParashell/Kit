<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS multi-feature and cut-extrude ground truth

Extends `.rescratch/corpus/REPORT.md`. SOLIDWORKS 2025, pywin32, `.venv\Scripts\python.exe`.
Corpus: `.rescratch/corpus2/parts/` (20 `.SLDPRT`). Scripts: `.rescratch/corpus2/scripts/`.
Machine-readable results: `.rescratch/corpus2/out/`. Patched round-trip artefacts:
`.rescratch/corpus2/patched/`.

Nothing under `src/` or `tests/` was modified. Everything in report 1 is taken as given.

Current-status note: this is a historical donor-patching investigation. Its measurements remain
evidence, but its proposed donor library is superseded by the typed zero-donor programs recorded in
`../archive/MULTISTREAM.md`. Production must reject a family that has no such program.

---

## 0. New COM facts

| Call                           | Result                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FeatureManager.FeatureCut4`   | **27 arguments**, not 24. Read from `sldworks.tlb`: `Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, Ddir1, Ddir2, Dang1, Dang2, OffsetReverse1, OffsetReverse2, TranslateSurface1, TranslateSurface2, NormalCut, UseFeatScope, UseAutoSelect, AssemblyFeatureScope, AutoSelectComponents, PropagateFeatureToParts, T0, StartOffset, FlipStartOffset, OptimizeGeometry`. 24 args raises `Parameter not optional`. |
| `FeatureManager.FeatureCut3`   | 26 args (same minus `OptimizeGeometry`)                                                                                                                                                                                                                                                                                                                                                                        |
| `FeatureManager.FeatureCut5`   | **does not exist** on `IFeatureManager` (only `IModelDoc2.FeatureCut5`, which returns `void`)                                                                                                                                                                                                                                                                                                                  |
| `FeatureCut4` returning `None` | means the cut removed nothing — a direction problem, not an API problem                                                                                                                                                                                                                                                                                                                                        |
| cut direction                  | For a sketch on the **Front Plane** with the pad at z>0, the cut needs `Dir = True`. `Dir = False` returns `None`. For a sketch on the **pad top face**, the opposite: `Dir = False` works, `Dir = True` returns `None`. Probed exhaustively over (Dir, Flip) × (plane, face) in `out/probe_cut.json`.                                                                                                         |
| `Flip = True`                  | "flip side to cut" — keeps the inside, removes the outside (8000 → 4500 mm³ for a 10×10 cut in a 40×20×10 pad)                                                                                                                                                                                                                                                                                                 |
| enumerating signatures         | `pythoncom.LoadTypeLib(r"...\SOLIDWORKS\sldworks.tlb")`, walk `GetFuncDesc`/`GetNames`. Cheap, no SOLIDWORKS launch, and the only reliable way to get arity. `scripts/probe_cut_signature.py`, `out/cut_signature.txt`.                                                                                                                                                                                        |
| session fragility              | After a `FeatureCut` that returns `None`, `CloseAllDocuments` + `NewDocument` frequently raises `The server threw an exception` and every later part in the run fails. Do not rely on retry-in-session; pick the right direction up front.                                                                                                                                                                     |

`FeatureExtrusion3` remains 23 args and unchanged.

---

## 1. The corpus (20 files, every volume exact)

`out/manifest.json`, `out/build.txt`. Base pad in every file: 40×20 mm rectangle on the Front
Plane centred at the origin, blind 10 mm. All second/third sketches are concentric with it.

```
file                       family        second/third feature                       vol_mm3      expected     ok
CUTBASE_cd3                CUTBASE_DEPTH plane cut 10x10, blind 3 mm               7700.0000    7700.0000   True
CUTBASE_cd5                CUTBASE_DEPTH plane cut 10x10, blind 5 mm               7500.0000    7500.0000   True
CUTBASE_cd7                CUTBASE_DEPTH plane cut 10x10, blind 7 mm               7300.0000    7300.0000   True
CUTBASE_s8                 CUTBASE_SIZE  plane cut  8x8,  blind 5 mm               7680.0000    7680.0000   True
CUTBASE_s10                CUTBASE_SIZE  plane cut 10x10, blind 5 mm               7500.0000    7500.0000   True
CUTBASE_s14                CUTBASE_SIZE  plane cut 14x14, blind 5 mm               7020.0000    7020.0000   True
CUTTHROUGH_s10             CUTTHROUGH    plane cut 10x10, ThroughAll (T1=1)        7000.0000    7000.0000   True
CUTMID_d5                  CUTMID        plane cut 10x10, MidPlane (T1=6) 5 mm     7750.0000    7750.0000   True
CUTFACE_d5                 CUTFACE       top-face cut 10x10, blind 5 mm            7500.0000    7500.0000   True
PADPLANE_rev_d5            PADPLANE      plane boss 10x10, blind 5 mm, reversed    8500.0000    8500.0000   True
TWOPAD_d3                  TWOPAD        top-face boss 10x10, blind 3 mm           8300.0000    8300.0000   True
TWOPAD_d5                  TWOPAD        top-face boss 10x10, blind 5 mm           8500.0000    8500.0000   True
TWOPAD_d8                  TWOPAD        top-face boss 10x10, blind 8 mm           8800.0000    8800.0000   True
THREEFEATURE_pad_cut_pad   THREEFEATURE  plane cut 10x10x5 + top-face boss 8x8x4   7756.0000    7756.0000   True
CIRCLECUT_r4               CIRCLECUT     plane circular cut r=4, blind 5 mm        7748.6726    7748.6726   True
CIRCLECUT_r6               CIRCLECUT     plane circular cut r=6, blind 5 mm        7434.5133    7434.5133   True
CONTROL2_A                 CONTROL2      plane cut 10x10, blind 5 mm               7500.0000    7500.0000   True
CONTROL2_B                 CONTROL2      plane cut 10x10, blind 5 mm               7500.0000    7500.0000   True
CONTROL2PAD_A              CONTROL2PAD   top-face boss 10x10, blind 5 mm           8500.0000    8500.0000   True
CONTROL2PAD_B              CONTROL2PAD   top-face boss 10x10, blind 5 mm           8500.0000    8500.0000   True
```

`CUTBASE_cd5`, `CUTBASE_s10`, `CONTROL2_A` and `CONTROL2_B` are four independent authoring runs
of the _same_ part, so they double as controls. `CONTROL2PAD_A/B` are two runs of the same
face-supported two-pad part. `PADPLANE_rev_d5` / `CUTFACE_d5` were added specifically to isolate
boss-vs-cut with everything else held fixed, and `CUTMID_d5` to isolate the second feature's end
condition.

---

## 2. Stream lengths and marker counts (Q1, part 1)

`Contents/Config-0-ResolvedFeatures`, raw (as saved):

| file                                    | length                | class markers | distinct classes |
| --------------------------------------- | --------------------- | ------------- | ---------------- |
| corpus1 `BASELINE_40x20x10` (1 feature) | 11075                 | 41            | 41               |
| `CUTTHROUGH_s10`                        | 14800                 | 44            | 44               |
| `CIRCLECUT_r4` / `_r6`                  | 15953                 | 50            | 50               |
| `CUTBASE_cd3/cd5/cd7/s8/s10/s14`        | 16579                 | 45            | 45               |
| `CUTMID_d5`                             | 16579                 | 45            | 45               |
| `CONTROL2_A/_B`                         | 16581                 | 45            | 45               |
| `PADPLANE_rev_d5`                       | 16581                 | 45            | 45               |
| `CUTFACE_d5`                            | 19385                 | 48            | 48               |
| `CONTROL2PAD_A/_B`                      | 19387 / 19390         | 48            | 48               |
| `TWOPAD_d3/d5/d8`                       | 19388 / 19390 / 19392 | 48            | 48               |
| corpus1 `TWOFEATURES_pad_pad`           | 19390                 | 48            | 48               |
| `THREEFEATURE_pad_cut_pad`              | 24805                 | 48            | 48               |

The **marker count never equals the object count**, exactly as report 1 warned: a 3-feature part
has 48 markers, the same as a 2-feature part, because features 2 and 3 share one class.

### Length is not deterministic in the face-supported layouts

Two effects change the length between _identically parameterised_ runs:

1. The transient session document name (`Part2`, `Part70`, …) embedded twice as UTF-16 in
   `moCStringHandle_c`. Known from report 1. Normalising both copies to a fixed width
   (`scripts/normalise.py`) removes it: all six `CUTBASE_*` files and both `CONTROL2_*` files
   become **16593** bytes.
2. **New:** a zlib-compressed Parasolid transmit blob (§3) whose _compressed_ size varies
   run-to-run. `CONTROL2PAD_A` vs `CONTROL2PAD_B`, byte-identical authoring: compressed 1168 vs
   1171, inflated 2253 vs 2253, raw stream 19387 vs 19390. So for face-supported features the
   resolved-stream length carries ±3 bytes of pure noise and **cannot** be used as a structural
   fingerprint.

`TWOPAD_d3` = 19388 and `TWOPAD_d5` = 19390 look like a depth-driven length change; they are not.
`corpus1 TWOFEATURES_pad_pad` is also a 5 mm second pad and is 19390 with compressed size 1169,
while `TWOPAD_d5` is 19390 with compressed size 1171. The variation is the blob, not the depth.

---

## 3. New structural finding: an embedded Parasolid inside the resolved-features stream

Face-supported sketches embed a **zlib stream** (`78 01`) inside the resolved-features stream. It
inflates to a Parasolid transmit file: it starts `50 53 00 00 00` = `PS\0\0\0` followed by
`3: TRANSMIT FILE created by modeller version …`.

| file                                                                           | zlib offset        | compressed | inflated | enclosing record                   |
| ------------------------------------------------------------------------------ | ------------------ | ---------- | -------- | ---------------------------------- |
| `TWOPAD_d3`                                                                    | 13401 (normalised) | 1169       | 2253     | `moFromEndSpec_c`+2137             |
| `TWOPAD_d5`                                                                    | 13401              | 1171       | 2253     | `moFromEndSpec_c`+2137             |
| `TWOPAD_d8`                                                                    | 13401              | 1171       | 2253     | `moFromEndSpec_c`+2137             |
| `CONTROL2PAD_A`                                                                | 13401              | 1168       | 2253     | `moFromEndSpec_c`+2137             |
| `CONTROL2PAD_B`                                                                | 13401              | 1171       | 2253     | `moFromEndSpec_c`+2137             |
| corpus1 `TWOFEATURES_pad_pad`                                                  | 13401              | 1169       | 2253     | `moFromEndSpec_c`+2137             |
| `THREEFEATURE_pad_cut_pad`                                                     | 18907              | 1169       | 2251     | `moFromSktEnt3IntSurfIdRep_c`+4478 |
| `CUTBASE_*`, `CUTMID_d5`, `PADPLANE_rev_d5`, `CIRCLECUT_*`, corpus1 `BASELINE` | —                  | —          | —        | **none**                           |

Every part whose second (or third) sketch is supported by a **face** carries exactly one such
blob; every part whose sketches are all supported by **planes** carries none. This is the
serialised surface of the reference face.

Two conclusions:

- Report 1's claim that "you never need to author Parasolid" survives, but only just: this blob is
  inside the _feature_ stream, not the geometry cache, so it cannot be deleted like
  `Config-0-Partition`. It has to be carried over verbatim from the donor.
- It is a **cache, not an authored parameter**. §7 case C moves the supporting face from z=10 to
  z=11 and case D from z=10 to z=14, leaving the blob untouched, and SOLIDWORKS rebuilds both to
  the predicted volume with zero errors and zero warnings. It re-resolves the face reference.

Its content is nondeterministic: two identical authoring runs (`TWOPAD_d5` vs
`TWOFEATURES_pad_pad`, and `CONTROL2PAD_A` vs `_B`) inflate to the same 2253 bytes but differ in
**194 bytes across 192 runs** — scattered single bytes, i.e. ids/hashes inside the Parasolid.

---

## 4. Measured noise floor (Q1, part 2)

Two independent control pairs, both authored in the same session as the rest of the corpus.

### Plane-only two-feature layout — `CONTROL2_A` vs `CONTROL2_B`

Raw length 16581 both. **105 differing bytes in 48 runs.** Every run is 1–8 bytes and none forms a
`float64` matching any authored parameter. Runs (raw offsets):

```
(380,384) (582,586) (767,768) (886,887) (1005,1006) (1124,1125) (1319,1323) (1518,1522)
(1995,1999) (2190,2194) (3013,3017) (6247,6251) (8388,8395) (8456,8460) (8705,8706)
(8710,8711) (8782,8783) (8833,8834) (8853,8854) (8873,8874) (8893,8894) (8975,8976)
(8999,9000) (9019,9020) (9039,9040) (9059,9060) (11392,11400) (11460,11464) (13645,13653)
(13713,13717) (13933,13934) (13953,13954) (13977,13978) (13997,13998) (14021,14022)
(14101,14103) (14163,14164) (14222,14223) (14250,14251) (14278,14279) (14306,14307)
(14362,14364) (14396,14397) (14424,14425) (14448,14449) (14476,14477) (14504,14505)
(16561,16564)
```

`CUTBASE_cd5` vs `CUTBASE_s10` (also identical parameters, also 16579 both) gives 111 bytes in
49 runs at the same places. That is the pair used as the noise mask in §5, because it shares the
`CUTBASE` family's exact layout.

### Face-supported two-feature layout — `CONTROL2PAD_A` vs `CONTROL2PAD_B`

Length differs (19387 vs 19390). Splitting at the zlib blob:

| region              | length | differing runs | differing bytes |
| ------------------- | ------ | -------------- | --------------- |
| head `[0:13401]`    | 13401  | 30             | 70              |
| inflated Parasolid  | 2253   | 192            | 194             |
| tail after the blob | 4832   | 43             | 60              |

So the face-supported layout has roughly **130 bytes** of id noise plus **194 bytes** inside the
Parasolid, and a ±3-byte length wobble. All offsets quoted below are outside these sets unless
stated.

---

## 5. Which bytes vary per family, and what they decode to (Q1, Q2)

Raw streams, control-noise runs excluded. Full data in `out/analysis_raw.json`,
`out/analysis_b.json`, `out/analysis_final.json`.

`scalar1` = the first feature's depth `float64`; `scalar2` = the second's; `scalar3` = the third's.
These are located by the rule in §6.

### 5.1 `CUTBASE_DEPTH` — cut depth 3 / 5 / 7 mm

All three files 16579 bytes. 63 diff runs / 191 bytes total; **46 runs / 122 bytes** after removing
control noise. Of those, only 17 offsets carry a decodable `float64`, and only 6 are real:

| raw offset | value                   | marker-relative                    | anchor-relative |
| ---------- | ----------------------- | ---------------------------------- | --------------- |
| **15427**  | `+cut_depth` (3/5/7 mm) | `moFromSktEnt3IntSurfIdRep_c`+1250 | **scalar2+0**   |
| 15499      | `+cut_depth`            | +1322                              | scalar2+72      |
| 15825      | `−cut_depth`            | +1648                              | scalar2+398     |
| 15849      | `−cut_depth`            | +1672                              | scalar2+422     |
| 15987      | `+cut_depth`            | +1810                              | scalar2+560     |
| 16011      | `+cut_depth`            | +1834                              | scalar2+584     |

The other 40 runs are 1–2 byte object-index tags (`aa 70 6a`-style) plus the `0.0 / 0.016` scratch
double at `moExtrusion_c`+114 that report 1 §5.7 already flagged as indeterminate — it reads
0/0/16 mm here, again uncorrelated with anything authored.

**The delta set {0, +72, +398, +422, +560, +584} is exactly report 1's feature-1 depth copy set**
(`moLengthParameter_c`+57/+129/+455/+479/+617/+641 = scalar1+0/+72/+398/+422/+560/+584). The
dimension object has an identical internal layout wherever it appears.

### 5.2 `CUTBASE_SIZE` — cut rectangle 8×8 / 10×10 / 14×14 mm

All three 16579 bytes. 64 diff runs / 220 bytes; **16 runs / 113 bytes** as signal. Every one
decodes:

| raw offset pair         | value                       | marker-relative            | anchor-relative        |
| ----------------------- | --------------------------- | -------------------------- | ---------------------- |
| **11568 / 11576**       | `(−s/2, −s/2)`              | `moFromEndSpec_c`+318/+326 | scalar2−3859 / −3851   |
| **11730 / 11738**       | `(+s/2, +s/2)`              | +480/+488                  | scalar2−3697 / −3689   |
| **11892 / 11900**       | `(−s/2, +s/2)`              | +642/+650                  | scalar2−3535 / −3527   |
| **12054 / 12062**       | `(+s/2, −s/2)`              | +804/+812                  | scalar2−3373 / −3365   |
| 15459/15467/15483/15491 | `+s/2` (annotation witness) | +1282/+1290/+1306/+1314    | scalar2+32/+40/+56/+64 |
| 15656 / 15672           | `−s/2`                      | +1479/+1495                | scalar2+229/+245       |
| 15745                   | `s/10` (= `(s/2)/5`)        | +1568                      | scalar2+318            |

Corner **stride is 162 bytes** and the corner order is `(min,min), (max,max), (min,max),
(max,min)` — the same order report 1 found for feature 1. The annotation-witness offsets
scalar2+32/+40/+56/+64/+229/+245/+318 mirror feature 1's scalar1+32/+40/+56/+64/+229/+245/+318
(report 1 §5.6 quoted them absolutely as 9914/9922/9938/9946/10111/10200). Confirmed derived.

### 5.3 `CIRCLECUT` — circular cut r = 4 / 6 mm

Both 15953 bytes. 49 runs / 143 bytes; no same-length control exists for this layout, so the id
noise is not masked. Decodable:

| raw offset        | value                  | marker-relative                          | anchor-relative      |
| ----------------- | ---------------------- | ---------------------------------------- | -------------------- |
| **11712 / 11720** | `(r·cos17°, r·sin17°)` | `moFromEndSpec_c`+460/+468               | scalar2−3089 / −3081 |
| 14833 / 14857     | `+r` (annotation)      | `moFromSktEnt3IntSurfIdRep_c`+1144/+1168 | scalar2+32/+56       |
| 15030             | `−r`                   | +1341                                    | scalar2+229          |
| 15119             | `r/5`                  | +1430                                    | scalar2+318          |

Report 1 §7's finding generalises exactly: **the radius is never stored**. The second sketch's
circle is one centre point plus one point on the circumference at 17°, so `r = hypot(x, y)`:
r=4 → (3.825219023852, 1.169486818891), |p| = 4.000000000000; r=6 → (5.737828535778,
1.754230228336), |p| = 6.000000000000.

### 5.4 `TWOPAD` — second pad depth 3 / 5 / 8 mm (face-supported)

Aligned by splitting at the zlib blob (§3). Head `[0:13401]`: 38 runs / 130 bytes. Tail
(4832 bytes): 51 runs / 121 bytes. Inflated Parasolid: 192 runs / 194 bytes — i.e. entirely within
the noise floor of §4, so **the second pad's depth is not encoded in the embedded Parasolid**.

Decoded columns (offsets in the `TWOPAD_d5` normalised layout):

| offset               | value                                                | marker-relative                    | anchor           |
| -------------------- | ---------------------------------------------------- | ---------------------------------- | ---------------- |
| **18252**            | `+pad2_depth` (3/5/8)                                | `moFromSktEnt3IntSurfIdRep_c`+1250 | **scalar2+0**    |
| 18324                | `10 + pad2_depth` (13/15/18)                         | +1322                              | scalar2+72       |
| 18650 / 18674        | `−pad2_depth`                                        | +1648/+1672                        | scalar2+398/+422 |
| 18812 / 18836        | `+pad2_depth`                                        | +1810/+1834                        | scalar2+560/+584 |
| 17391                | `(10+d)/2`                                           | +389                               | —                |
| 17399                | `2·√(20²+10²+((10+d)/2)²)` (46.5725/47.1699/48.2079) | +397                               | —                |
| 4306                 | `−0.05·(10+d)`                                       | `moDefaultRefPlnData_c`+497        | —                |
| 4500/4508, 5054/5062 | `±0.55·(10+d)`                                       | +691/+699, +1245/+1253             | —                |
| 4547, 5117           | `(10+d)/2`                                           | +738, +1308                        | —                |
| 4876                 | `1.05·(10+d)`                                        | +1067                              | —                |

The `moDefaultRefPlnData_c` and bounding-sphere entries are report 1's ×1.1 plane-display and
bbox caches, now driven by the _total_ height `10+d` — confirming they are derived from the final
body, not from any one feature. The scalar2+72 copy is `10 + d`, i.e. the absolute end-plane
coordinate in the sketch frame (the sketch plane is the pad top at z=10), where for a
plane-supported feature it is just `d`.

### 5.5 `CUTTHROUGH` — ThroughAll instead of blind

`CUTBASE_cd5` (16579) vs `CUTTHROUGH_s10` (14800), −1779 bytes:

- `moFromSktEnt3IntSurfIdRep_c` shrinks **2402 → 679** (−1723).
- Class `moEndFace3IntSurfIdRep_c` (a 56-byte record) is **present only in the blind file**.
- The remaining −1779 is accounted for by those two plus the shorter feature name.
- The second feature has **no depth dimension at all**: the whole `D1` name-plus-scalar object is
  gone (§6 finds 1 scalar in `CUTTHROUGH_s10` vs 2 in `CUTBASE_cd5`).

So ThroughAll is not a code flipped in place — it **deletes** the dimension object. Every other
byte-level difference between the two files is object-index renumbering (84 small-value byte
diffs, all in the `xx aa 70 6a` / `xx af 70 6a` index-tag pattern). See `out/analysis_final.txt`.

### 5.6 `CUTMID` — MidPlane instead of blind

`CUTBASE_cd5` vs `CUTMID_d5`, both 16579 raw / 16593 normalised. 60 signal runs / 154 bytes, of
which all but two are index tags. The two that matter are §6.3.

---

## 6. Addressing features that have no class marker (Q3 — the key question)

Report 1 left this open. It is solved, and the mechanism that works is the one `native.py` already
uses for reading, generalised and made complete.

### 6.1 The rule that works: name-record scanning

Every feature-tree node — folder, plane, sketch, boss, cut — is serialised as

```
<u16 class_token> ff fe ff <u8 units> <utf16le name>  00 00 00 00  <u32 flags>  <u32 feature_id>
```

`class_token` is the MFC class-index tag of the string-handle class. `native.py::_name_marker`
already discovers it (it is `0x8004` in every one of the 20 corpus2 files plus every corpus1 file);
`native.py::_parse_names` already scans for it. What report 1 did not know is that the 12 bytes
_after_ the name identify the node:

| `flags`          | meaning                  | observed on                                         |
| ---------------- | ------------------------ | --------------------------------------------------- |
| `0x40000000`     | folder / sketch          | `Comments`, `Sketch1`, `Sketch2`, `Sketch3`, …      |
| `0xC0000000`     | reference plane / origin | `Front Plane`, `Top Plane`, `Right Plane`, `Origin` |
| **`0x40000140`** | **extruded boss**        | `Boss-Extrude1`, `Boss-Extrude2`                    |
| **`0x400201CA`** | **extruded cut**         | `Cut-Extrude1`                                      |

and `feature_id` is **exactly the `id` attribute in `swXmlContents/KeyWords`**: `Sketch1`=26,
feature 1=32, `Sketch2`=33, feature 2=40, `Sketch3`=41, feature 3=47.

This is marker-independent, so it finds unmarked objects. Verified on all 20 corpus2 files and 5
corpus1 files (`out/analysis_features.txt`). In `THREEFEATURE_pad_cut_pad` it finds
`Boss-Extrude2` (id 47, flags `0x40000140`) sitting inside the `moCompFace_c` record with no class
marker of its own.

### 6.2 Depths: dimension-scalar records, addressed by ordinal

`native.py::_parse_scalars` already does the right thing: for each name record, test whether
`DIMENSION_SCALAR_HEADERS[0]` (`0000000000000040 ffffffff 00000000 fffeff 000000`) immediately
follows the name text; if so the next 8 bytes are the value, `float64`, metres. Every feature depth
in the corpus is named `D1` (per-feature namespace) and every hit uses header index 0.

Scanning in stream order gives exactly one scalar per blind feature, in feature order:

| file                  | scalars found | values (mm) | value offsets                        |
| --------------------- | ------------- | ----------- | ------------------------------------ |
| corpus1 `BASELINE`    | 1             | 10          | 9882                                 |
| corpus1 `TWOFEATURES` | 2             | 10, 5       | 10120, 18238                         |
| `CUTBASE_cd3/cd5/cd7` | 2             | 10, 3/5/7   | 10118, 15427                         |
| `CUTBASE_s8/s10/s14`  | 2             | 10, 5       | 10118, 15427                         |
| `CUTTHROUGH_s10`      | **1**         | 10          | 10118                                |
| `CUTMID_d5`           | 2             | 10, 5       | 10118, 15427                         |
| `CUTFACE_d5`          | 2             | 10, 5       | 10118, 18233                         |
| `PADPLANE_rev_d5`     | 2             | 10, 5       | 10118, 15429                         |
| `TWOPAD_d3/d5/d8`     | 2             | 10, 3/5/8   | 10118/10118/10120, 18236/18238/18240 |
| `THREEFEATURE`        | **3**         | 10, 5, 4    | 10358, 15667, 23653                  |
| `CIRCLECUT_r4/r6`     | 2             | 10, 5       | 10120, 14801                         |

The marker-relative form of the second scalar is **not** stable — `moFromSktEnt3IntSurfIdRep_c`+1250
for the rectangular cut and the face pad, +1112 for the circular cut, and the third feature's is
`moCompFace_c`+2391. Marker-relative addressing is the wrong abstraction beyond feature 1; the
ordinal position among dimension-scalar records is the right one.

**Is this mechanism reliable enough to WRITE through?** Yes, with one qualification. The value
offset is found by structural pattern match, not by a guessed offset, and the pattern is
`name text end` immediately followed by a 22-byte constant header — no wildcards. Across 25 files
it produced zero false positives (the only string records that match the header are dimension
scalars) and zero misses (the count always equals the number of blind extrusions). §7 writes
through it four times and SOLIDWORKS agrees to 12 significant figures. The qualification: a blind
feature has one scalar and a ThroughAll feature has none, so a writer must pair scalars to features
positionally and tolerate features with no scalar rather than assuming one scalar per feature.

### 6.3 End condition and direction for feature 2+

Anchored on the feature's own depth scalar, the two flag bytes report 1 found at `moEndSpec_c`+27
and +33 sit at fixed negative offsets — but at _different_ offsets for the first feature and for
later ones:

| field                             | first feature                       | later features |
| --------------------------------- | ----------------------------------- | -------------- |
| direction reverse flag (1 byte)   | **scalar−824** (= `moEndSpec_c`+27) | **scalar−721** |
| `swEndConditions_e` code (1 byte) | **scalar−818** (= `moEndSpec_c`+33) | **scalar−715** |

Read back over 11 files and up to 3 features each (`out/probe_endspec.txt`), with no contradiction:

```
BASELINE          f1 blind fwd pad      -824=0 -818=0
REVERSED_d10      f1 blind rev pad      -824=1 -818=0
MIDPLANE_d10      f1 midplane pad       -824=0 -818=6
CUTBASE_cd5       f2 blind rev cut                     -721=1 -715=0
CUTMID_d5         f2 midplane cut                      -721=1 -715=6
CUTFACE_d5        f2 blind fwd cut                     -721=0 -715=0
PADPLANE_rev_d5   f2 blind rev boss                    -721=1 -715=0
TWOPAD_d5         f2 blind fwd boss                    -721=0 -715=0
TWOFEATURES       f2 blind fwd boss                    -721=0 -715=0
THREEFEATURE      f2 blind rev cut                     -721=1 -715=0
THREEFEATURE      f3 blind fwd boss                    -721=0 -715=0
CIRCLECUT_r4      f2 blind rev cut                     -721=1 -715=0
```

The 103-byte difference between the two anchor distances is the class-declaration overhead that
only the first instance of each dimension-chain class carries (`moDisplayDistanceDim_c`,
`moFeatureDimHandle_c`, `ParallelPlaneDistanceDim_c`, `moLengthParameter_c`). I did not reconcile
it byte for byte; I only established the two constants empirically. As in report 1, the true field
width is undetermined — only 0, 1 and 6 were exercised and the neighbouring bytes are zero.

### 6.4 Sketch geometry: a point-record signature

Sketch points cannot be anchored on the depth scalar: the corner-to-scalar distance is 3859 bytes
for a plane-supported rectangular second feature but 6670 for a face-supported one. What _is_
stable is the byte signature wrapping every 2-D sketch point, identical for the first and later
sketches:

```
… 00 00 00 00 00 00 f0 3f 00 00 00 00 00 00 00 00 1e 00   <x float64> <y float64>   00 00 02 00
  └──────────── 1.0 ────────────┘ └───── 0.0 ─────┘ └30┘                            └ suffix ┘
```

Scanning for the 18-byte prefix plus the 4-byte suffix enumerates all sketch points in stream
order. Assigning each point to the last `Sketch*` name record before it partitions them by sketch
exactly.

Verified on 20 files (`out/verify_locator.txt`): 4 points per rectangular sketch, 0 for a circular
sketch (arcs use a different record), correct values in every case, zero misassignments. Examples:
`CUTBASE_s14` → sketch 1 `(±20, ±10)`, sketch 2 `(±7, ±7)`; `THREEFEATURE` → `(±20, ±10)`,
`(±5, ±5)`, `(±4, ±4)`.

### 6.5 What I rejected

- **Marker-relative offsets.** Work for feature 1 only. `moFromSktEnt3IntSurfIdRep_c`+1250 happens
  to hold the second depth in `CUTBASE`/`TWOPAD`/`TWOFEATURES` but not in `CIRCLECUT` (+1112) and
  is a different class entirely for feature 3.
- **Ordinal position among `moEndSpec_c`-shaped records.** Not needed once the scalar anchor is
  known, and I could not find a byte signature specific enough to enumerate unmarked
  `moEndSpec_c` objects without false positives.
- **MFC class-index tags.** The `xx aa 70 6a` / `xx af 70 6a` sequences that dominate the residual
  diffs are clearly an object-index encoding, and their low byte renumbers whenever the object
  count changes (see the blind-vs-ThroughAll and blind-vs-MidPlane diffs). I did **not** decode
  them, and did not need to: the name-record signature reaches every object I had to address.

---

## 7. Cut versus boss in the stream (Q4)

### 7.1 There is no `moCut_c`

No `moCut_c` class exists anywhere in any corpus2 file. The class layout is:

- Feature 1 is always a **`moExtrusion_c`** record (244 bytes), whether it is a boss or (untested
  as feature 1) otherwise.
- Feature 2 is always a **`moICE_c`** record — 234 bytes for a cut, 236 for a boss, the 2-byte
  difference being only `len("Cut-Extrude1")=12` vs `len("Boss-Extrude2")=13` in UTF-16.
- Feature 3 is an **unmarked `moICE_c`** object (only one `moICE_c` class marker exists in
  `THREEFEATURE_pad_cut_pad`).

`moICE_c` is present in every ≥2-feature file including the all-boss ones, so it is "second and
later feature", not "cut".

### 7.2 The operation code

The two records have the same internal layout:

```
moExtrusion_c (feature 1, boss)   … 04 80 ff fe ff 0d "Boss-Extrude1" 00000000 [40 01 00 40] [20 00 00 00] …
moICE_c       (feature 2, boss)   … 04 80 ff fe ff 0d "Boss-Extrude2" 00000000 [40 01 00 40] [28 00 00 00] …
moICE_c       (feature 2, cut)    … 04 80 ff fe ff 0c "Cut-Extrude1"  00000000 [ca 01 02 40] [28 00 00 00] …
```

So at `name_text_end + 4`:

- **boss = `0x40000140`**
- **cut = `0x400201CA`**

and at `name_text_end + 8` the KeyWords feature id (32 / 40 / 47).

This was isolated by holding everything else fixed: `CUTBASE_cd5` vs `PADPLANE_rev_d5` (both
plane-sketched, both `Dir=True`, same 10×10×5 profile) and `CUTFACE_d5` vs `TWOPAD_d5` (both
face-sketched, both `Dir=False`). Intersecting the two pairs' per-record byte diffs left 150
positions; all but the flags word are ids, hashes, or the name-length shift
(`out/analysis_operation.txt`, `out/analysis_operation2.txt`). The flags word is the same for a
blind cut, a MidPlane cut, a ThroughAll cut, a plane-sketched cut and a face-sketched cut, so it
encodes the operation only — not the end condition.

### 7.3 End-spec differences

- Blind vs MidPlane: one byte, scalar−715, `0 → 6` (§6.3). Nothing else structural.
- Blind vs ThroughAll: the dimension object is removed entirely (§5.5), the class
  `moEndFace3IntSurfIdRep_c` disappears, and `moFromSktEnt3IntSurfIdRep_c` loses 1723 bytes. A
  writer cannot turn a blind cut into a ThroughAll cut by flipping a byte.
- The `moEndSpec_c` / `moFromEndSpec_c` **class markers exist once each** and belong to feature 1.
  Feature 2's and 3's equivalents are unmarked objects that happen to live inside the byte span
  attributed to `moFromEndSpec_c` and `moFromSktEnt3IntSurfIdRep_c` by a marker walk. Do not read
  the marker walk as an object segmentation.

---

## 8. `swXmlContents/KeyWords` across 1, 2 and 3 features (Q5)

Sizes: 1662 B (1 feature) → 1864–1866 B (2 features) → 2069 B (3 features), and 1819 B for the
2-feature ThroughAll part.

1 feature (`BASELINE_40x20x10`):

```xml
<Extrusion id="32" Name="Boss-Extrude1" Type="Boss-Extrude"><Dimension Name="D1">10</Dimension></Extrusion>
…
<Sketch id="26" Name="Sketch1" Dissectable="true"/>
```

2 features (`CUTBASE_cd5`) adds:

```xml
<Extrusion id="40" Name="Cut-Extrude1" Dissectable="true" DissectableChildren="33" DissectableRoot="true">
  <Dimension Name="D1">5</Dimension></Extrusion>
…
<Sketch id="33" Name="Sketch2" Dissectable="true"/>
```

3 features (`THREEFEATURE_pad_cut_pad`) adds a third:

```xml
<Extrusion id="47" Name="Boss-Extrude2" Dissectable="true" DissectableChildren="41" DissectableRoot="true">
  <Dimension Name="D1">4</Dimension></Extrusion>
…
<Sketch id="41" Name="Sketch3" Dissectable="true"/>
```

Concrete differences:

1. One extra `<Extrusion>` and one extra `<Sketch>` element per feature. Ids advance
   sketch 26 → feature 32 → sketch 33 → feature 40 → sketch 41 → feature 47 (gap of 7 between
   consecutive feature ids), matching the `feature_id` field in §6.1 exactly.
2. **Only the first feature carries `Type="Boss-Extrude"`.** Features 2 and 3 have no `Type`
   attribute at all; they carry `Dissectable="true" DissectableChildren="<sketch id>"
DissectableRoot="true"` instead. So in KeyWords, boss versus cut is distinguishable _only_ by
   the `Name` string (`Cut-Extrude1` vs `Boss-Extrude2`).
3. `DissectableChildren` is the id of the feature's own sketch (33 for feature 2, 41 for
   feature 3), and `Sketch1` gains `Dissectable="true"` in all cases.
4. A **ThroughAll** feature's `<Extrusion>` element has **no `<Dimension>` child**
   (`CUTTHROUGH_s10`), consistent with the missing scalar in the resolved stream.
5. Nothing else changes — the ~24 boilerplate `<Feature>` elements, `<Configuration>` and
   `<Sketch id="5" Name="Origin">` are byte-identical apart from the `Keywords id`/`Name`
   attributes, which carry the transient document name (`Part2`, `Part9`, `Part70`, …).

---

## 9. Round-trip proof (PROVE IT)

`scripts/prove.py` → `out/prove.txt`, `out/prove.json`, artefacts in `patched/`.

For each case: locate every feature with §6, patch both/all features' sketch corners and depth
scalars, **delete `Contents/Config-0-Partition` entirely**, rebuild the container with
`.rescratch/swcontainer.py::build_container` reusing the donor's `file_id` and its
local/central/end signature triplet (extracted from the donor with
`container._template_fields`), then open the result in SOLIDWORKS, rebuild and read
`GetMassProperties`. Nothing else was touched — the five derived depth copies, the bbox cache, the
plane display extents, the annotation witness points and the embedded Parasolid were all left
stale.

| case | donor                                                     | patch                                        | predicted mm³ | measured mm³           | match |
| ---- | --------------------------------------------------------- | -------------------------------------------- | ------------- | ---------------------- | ----- |
| A    | `CUTBASE_cd5` (16579 B, 40×20×10 pad + 10×10×5 plane cut) | pad → 50×30×12, cut → 14×14×7                | 16628         | **16627.999999999996** | ✔     |
| B    | `CUTBASE_cd5`                                             | pad unchanged, cut → 8×8×3                   | 7808          | **7808.000000000002**  | ✔     |
| C    | `TWOPAD_d5` (19390 B, face-supported second boss)         | pad → 45×25×11, boss2 → 12×12×6              | 13239         | **13239.000000000004** | ✔     |
| D    | `THREEFEATURE_pad_cut_pad` (24805 B, three features)      | pad → 60×25×14, cut → 12×12×6, boss2 → 6×6×3 | 20244         | **20243.999999999996** | ✔     |

All four: `opened=True, open_errors=0, open_warnings=0, rebuild=True, bodies=1`, and the feature
tree comes back complete (`Sketch1, Boss-Extrude1, Sketch2, Cut-Extrude1, Sketch3, Boss-Extrude2`
for case D). Re-running the whole script end to end reproduces the same four numbers.

Container arithmetic, case A: donor 56366 bytes → patched 46102 bytes, 40 streams → 39
(`Contents/Config-0-Partition`, 6864 bytes, dropped), `file_id = 0x651DC788`, signature triplet
`e5edab7c / f1935f31 / 02a15b56` carried over unchanged. Case D: donor 64393 → 52123 bytes,
`file_id = 0xF2EA07D7`, triplet `70b78761 / d7b187db / 3144e9e5`.

Offsets actually written, case A: sketch-1 corners at 6357 / 6535 / 6697 / 6859, sketch-2 corners
at 11568 / 11730 / 11892 / 12054, depth 1 at 10118, depth 2 at 15427 — all found by the locator,
none hard-coded.

Case C is the load-bearing one for §3: the supporting face moved from z=10 to z=11 and the
embedded Parasolid still describes the z=10 face. SOLIDWORKS rebuilt to the exact predicted volume
with no warning. Case D does the same with a 4 mm face displacement and a third feature that has
no class marker.

---

## 10. Historical donor-patching boundary (superseded)

**Donor-patching is sufficient** — proven by §9 — for any part that reuses a donor with the same
_feature topology_, i.e. the same ordered sequence of operations, profile types, support types and
end conditions. Within that constraint every numeric parameter is free:

| family                                                           | verdict                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CUTBASE` (pad + plane rectangular cut, blind)                   | **donor-patch.** Cut depth and cut rectangle are 1 + 8 `float64` writes. Proven, cases A and B.                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `TWOPAD` (pad + face rectangular boss, blind)                    | **donor-patch.** Proven, case C, including moving the supporting face.                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `THREEFEATURE` (pad + cut + face boss)                           | **donor-patch.** Proven, case D. The unmarked third feature is reachable.                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `CUTMID` (MidPlane cut)                                          | **donor-patch**, plus one byte at scalar−715 if you need to switch a blind donor to MidPlane. Not round-trip-tested as a _switch_; the read-back is verified on 11 files.                                                                                                                                                                                                                                                                                                                                                              |
| `PADPLANE` / direction changes                                   | **donor-patch**, one byte at scalar−721 (feature 2+) or scalar−824 (feature 1). Read-back verified; switching not round-trip-tested.                                                                                                                                                                                                                                                                                                                                                                                                   |
| `CIRCLECUT` (circular cut)                                       | **donor-patch with a caveat.** The radius is not stored; you must write the 17° circumference point as `(r·cos17°, r·sin17°)`. The arc record does not match the rectangular point signature, so the §6.4 locator returns 0 points for it and a circle writer needs a separate arc locator. Not implemented, not round-trip-tested.                                                                                                                                                                                                    |
| `CUTTHROUGH` (ThroughAll)                                        | **historical result, now superseded.** The differential proved that switching blind ↔ ThroughAll adds/removes a 1723-byte dimension object and a class record. The current `resolved_bosscutthrough_program.py` emits the recovered family from typed fields with no donor.                                                                                                                                                                                                                                                            |
| changing feature **count** (2 → 3) or **operation** (boss ↔ cut) | **needs real serialization.** Feature count changes the class-declaration layout, the object-index numbering, the `moICE_c`/`moCompFace_c` chain and every id in `moCompFeature_c`, and adds a `<Extrusion>`/`<Sketch>` pair to KeyWords. Boss ↔ cut is one `u32` in the stream but also changes the feature _name_ string (`Cut-Extrude1` ↔ `Boss-Extrude2`), which is variable-length and appears in both the resolved stream and KeyWords, and changes `moEndFace3IntSurfIdRep_c` presence. I would not attempt either by patching. |
| changing the **support** of a sketch (plane ↔ face)              | **needs real serialization.** Adds or removes `moEdgeRef_c`, `moFaceRefPlnData_c`, `moCompFace_c` and the embedded Parasolid blob — thousands of bytes.                                                                                                                                                                                                                                                                                                                                                                                |
| changing the **profile type** (rectangle ↔ circle)               | **needs real serialization.** Different `sg*` classes, different record lengths. Report 1 already established this for feature 1.                                                                                                                                                                                                                                                                                                                                                                                                      |

Historical consequence: this report proposed a small donor library keyed by feature topology. That
architecture is prohibited and has been removed. The measured topology keys instead select complete
typed serializers; there is no production donor fallback.

---

## 11. What I could not determine

- The **MFC object-index encoding** (`xx aa 70 6a`, `xx af 70 6a`). It clearly renumbers with
  object count and dominates the residual diffs, but I did not decode it. Everything I needed was
  reachable without it. A writer that changes the object count will have to.
- The **true width** of the direction and end-condition fields. Still only 0, 1 and 6 observed,
  still surrounded by zeros.
- Whether the two anchor distances in §6.3 (824/818 for the first feature, 721/715 for later ones)
  hold for a **fourth** feature or for feature 2 with a non-rectangular, non-circular profile. Only
  ordinals 1–3 and rectangle/circle profiles were exercised.
- The exact byte accounting for the 103-byte difference between those two anchor distances.
- The internal structure of the inflated 2253-byte Parasolid transmit blob beyond identifying it and
  demonstrating that it can be left stale.
- The **`0.0 / 0.016` m scratch double** at `moExtrusion_c`+114 that report 1 flagged. It shows up
  again in every family here (0/0/16 mm across `CUTBASE_DEPTH`, 16/0/0 across `CUTBASE_SIZE`,
  0/15/16 across `TWOPAD`) with no correlation to anything authored. Also a second one at
  `moFromEndSpec_c`+140 and `moICE_c`+106/+108 with the same behaviour. Still indeterminate.
- End conditions other than Blind (0), MidPlane (6) and ThroughAll (1). `T1 = 5` still raises an
  internal application error without a pre-selected surface.
- Whether a **cut as the first feature** uses `moExtrusion_c` with the cut flags word, or a
  different class. Not authorable in the corpus (a cut needs existing material).

---

## 12. Files on disk

```
.rescratch/corpus2/
  REPORT.md                      this report
  parts/                         20 .SLDPRT
  patched/                       4 round-trip artefacts (A/B/C/D)
  scripts/
    swcom2.py                    COM helper; wraps corpus/scripts/swcom.py, adds cut_extrude
                                 (correct 27-arg FeatureCut4) and face/plane sketch helpers
    probe_cut_signature.py       reads FeatureCut*/FeatureExtrusion* arity from sldworks.tlb
    probe_cut.py                 exhaustive (Dir, Flip) x (plane, face) x end-condition cut probe
    build_corpus2.py             authors the corpus (accepts names to rebuild selectively)
    swstreams.py                 stream access, class-record walk, diff-run helpers
    normalise.py                 rewrites the transient document name to a fixed width
    analyse_a.py                 lengths, marker counts, control noise, first-pass column scan
    analyse_b.py                 per-family diff + float64 classification on normalised streams
    analyse_raw.py               same on raw streams, with scalar-anchor-relative offsets
    analyse_scalars.py           dimension-scalar enumeration + native.py decoder comparison
    analyse_structure.py         class-record tables, string tables, KeyWords XML
    show_records.py              renders out/records_summary.txt
    analyse_features.py          name-record scan: flags word + feature id per tree node
    analyse_operation.py         cut-vs-boss record diff, intersected over two pairs
    analyse_operation2.py        filters that to small-value candidates, dumps moICE_c hex
    analyse_final.py             TWOPAD aligned around the Parasolid, blind-vs-ThroughAll
    analyse_endcond.py           blind-vs-MidPlane, CONTROL2PAD noise, CUTMID readback
    probe_zlib.py                finds and inflates the embedded Parasolid transmit blobs
    probe_strings.py             string-record inventory
    probe_records.py             per-class record-length tables side by side
    probe_shift.py               common prefix/suffix of two streams
    probe_insert.py              difflib opcode diff of a byte range
    probe_points.py              hex context around known sketch-point offsets
    probe_endspec.py             reads scalar-824/-818/-721/-715 for every feature
    locator.py                   the deliverable: name-record + scalar-header + point-signature
                                 locator, and patch()
    verify_locator.py            asserts the locator against 20 files of known parameters
    prove.py                     patch both/all features, drop the Partition, rebuild the
                                 container, open in SOLIDWORKS, compare volumes
  out/
    build.txt  manifest.json  cut_signature.{txt,json}  probe_cut.json
    analysis_a.{txt,json}  analysis_b.{txt,json}  analysis_raw.{txt,json}
    analysis_scalars.{txt,json}  analysis_structure.{txt,json}  records_summary.txt
    analysis_features.{txt,json}  analysis_operation.{txt,json}  analysis_operation2.txt
    analysis_final.{txt,json}  analysis_endcond.{txt,json}
    probe_zlib.{txt,json}  probe_strings.txt  probe_records.txt  probe_shift.txt
    probe_insert.txt  probe_points.{txt,json}  probe_endspec.{txt,json}
    verify_locator.{txt,json}  prove.{txt,json}
```
