# SOLIDWORKS `Contents/Config-0-ResolvedFeatures` — corpus + differential layout analysis

SOLIDWORKS 2025, pywin32 311, `.venv\Scripts\python.exe`.
Corpus: `.rescratch/corpus/parts/` (31 `.SLDPRT`).
Scripts: `.rescratch/corpus/scripts/`. Machine-readable results: `.rescratch/corpus/out/`.

Nothing under `src/` or `tests/` was modified.

---

## 0. COM authoring — what actually works in 2025

| Call | Result |
|---|---|
| `Dispatch("SldWorks.Application")`, `app.Visible = False` | works |
| `gencache.EnsureDispatch("SldWorks.Application")` | **fails**: `GetTypeInfo` → `Element not found`, then `TypeError: This COM object can not automate the makepy process`. Early binding is not available. |
| `app.NewPart()` | **fails**: `Member not found` (does not exist on the 2025 interface) |
| `app.NewDocument(template, 0, 0, 0)` — **integer** 3rd/4th args | **works**, returns the model |
| `app.NewDocument(template, 0, 0.0, 0.0)` | fails, `Type mismatch` (arg 8) — this is the reported failure; the fix is int args, not early binding |
| `Extension.SelectByID2(name, kind, 0.0,0.0,0.0, False, 0, None, 0)` | **fails**, `Type mismatch` (arg 8) — the `Callout` param cannot be Python `None` |
| `Extension.SelectByID2(..., VARIANT(pythoncom.VT_DISPATCH, None), 0)` | **works** |
| `Extension.SaveAs2(path, 0, 1, None, "", False, err, warn)` | fails, `Type mismatch` (arg 4) |
| `model.SaveAs4(path, 0, 1, err, warn)` | **works** (`ok=True, errors=0, warnings=0`) |
| `model.EditRebuild3` | a **property**, not a method — `model.EditRebuild3()` raises `TypeError: 'bool' object is not callable` |
| `FeatureExtrusion3(..., T1=4, ...)` for mid-plane | **wrong**: returns `None`, no body |
| `T1 = 6` | **correct** — read from `swconst.tlb`: `swEndCondMidPlane = 6` (`swEndCondUpToSurface = 4`) |

Full `swEndConditions_e` read from the type library (`out/enums.json`):
`Blind=0, ThroughAll=1, ThroughNext=2, UpToVertex=3, UpToSurface=4, OffsetFromSurface=5, MidPlane=6, UpToBody=7, ThroughAllBoth=9, UpToSelection=10, UpToNext=11`.

Enumerating type-library constants without launching SOLIDWORKS:
`pythoncom.LoadTypeLib(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\swconst.tlb")` then walk `TKIND_ENUM` type infos (`scripts/dump_enums.py`). This works and is much cheaper than makepy.

Step 1 verification (`out/step1_probe.json`): 40×20×10 mm pad, 1 body, volume `8.000000000000001e-06 m³` = authored `w·h·d`, saved, reopened, same volume and same 19-feature tree.

---

## 1. The corpus (all 30 planned files authored, all volumes exact)

`out/corpus_table.txt`, `out/manifest.json`. One SOLIDWORKS session for the whole run.

```
file                    family      params                                            vol_mm3     expected   ok bodies
DEPTH_d10               DEPTH       Front Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
DEPTH_d11               DEPTH       Front Plane, 40x20 @(0,0), d=11, rev=0, T1=0    8800.0000    8800.0000 True      1
DEPTH_d12               DEPTH       Front Plane, 40x20 @(0,0), d=12, rev=0, T1=0    9600.0000    9600.0000 True      1
DEPTH_d20               DEPTH       Front Plane, 40x20 @(0,0), d=20, rev=0, T1=0   16000.0000   16000.0000 True      1
DEPTH_d50               DEPTH       Front Plane, 40x20 @(0,0), d=50, rev=0, T1=0   40000.0000   40000.0000 True      1
WIDTH_w40               WIDTH       Front Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
WIDTH_w41               WIDTH       Front Plane, 41x20 @(0,0), d=10, rev=0, T1=0    8200.0000    8200.0000 True      1
WIDTH_w42               WIDTH       Front Plane, 42x20 @(0,0), d=10, rev=0, T1=0    8400.0000    8400.0000 True      1
WIDTH_w60               WIDTH       Front Plane, 60x20 @(0,0), d=10, rev=0, T1=0   12000.0000   12000.0000 True      1
WIDTH_w100              WIDTH       Front Plane, 100x20 @(0,0), d=10, rev=0, T1=0  20000.0000   20000.0000 True      1
HEIGHT_h20              HEIGHT      Front Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
HEIGHT_h21              HEIGHT      Front Plane, 40x21 @(0,0), d=10, rev=0, T1=0    8400.0000    8400.0000 True      1
HEIGHT_h22              HEIGHT      Front Plane, 40x22 @(0,0), d=10, rev=0, T1=0    8800.0000    8800.0000 True      1
HEIGHT_h30              HEIGHT      Front Plane, 40x30 @(0,0), d=10, rev=0, T1=0   12000.0000   12000.0000 True      1
HEIGHT_h50              HEIGHT      Front Plane, 40x50 @(0,0), d=10, rev=0, T1=0   20000.0000   20000.0000 True      1
OFFSET_x5_y0            OFFSET      Front Plane, 40x20 @(5,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
OFFSET_x0_y5            OFFSET      Front Plane, 40x20 @(0,5), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
OFFSET_x10_y7           OFFSET      Front Plane, 40x20 @(10,7), d=10, rev=0, T1=0   8000.0000    8000.0000 True      1
PLANE_FRONT             PLANE       Front Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
PLANE_TOP               PLANE       Top Plane,   40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
PLANE_RIGHT             PLANE       Right Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
CIRCLE_r10              CIRCLE      Front Plane, r=10, d=10                         3141.5927    3141.5927 True      1
CIRCLE_r11              CIRCLE      Front Plane, r=11, d=10                         3801.3271    3801.3271 True      1
CIRCLE_r20              CIRCLE      Front Plane, r=20, d=10                        12566.3706   12566.3706 True      1
REVERSED_d10            REVERSED    Front Plane, 40x20 @(0,0), d=10, rev=1, T1=0    8000.0000    8000.0000 True      1
MIDPLANE_d10            MIDPLANE    Front Plane, 40x20 @(0,0), d=10, rev=0, T1=6    8000.0000    8000.0000 True      1
TWOFEATURES_pad_pad     TWOFEATURES 40x20x10 + 10x10x5 pad on the pad top face      8500.0000    8500.0000 True      1
CONTROL_A               CONTROL     Front Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
CONTROL_B               CONTROL     Front Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
BASELINE_40x20x10       BASELINE    Front Plane, 40x20 @(0,0), d=10, rev=0, T1=0    8000.0000    8000.0000 True      1
```

`step1_pad.SLDPRT` is also on disk (the step-1 artefact, stream length 11073). The 2-byte difference
is localised to exactly one record: `moCStringHandle_c` is 130 bytes instead of 132 because it embeds
the **transient in-session document name** as UTF-16 — `Part8` in `step1_pad` versus `Part70` in
`BASELINE_40x20x10`. That name is assigned by `NewDocument` and depends on how many documents the
running SOLIDWORKS instance has created, not on the authored geometry or the filename. The record
structure is otherwise identical.

`CONTROL_A`/`CONTROL_B` are byte-for-byte-identical authoring runs. They exist to measure
save-to-save nondeterminism so that real signal can be separated from ids and hashes.

### Measured noise floor

`CONTROL_A` vs `CONTROL_B`: **54 differing bytes in 22 runs** out of 11075. Every run is 1–6 bytes
wide, and none of them forms a complete `float64` that matches any authored parameter. They are
4-byte ids/hashes plus the UTF-16 digits of the transient session document name inside
`moCStringHandle_c` (e.g. `"70"` vs `"67"` at 8467–8473):

```
(380,384) (582,586) (767,768) (886,887) (1081,1085) (1280,1284) (1757,1761) (1952,1956)
(2775,2779) (6009,6013) (8218,8222) (8467,8473) (8544,8545) (8595,8596) (8615,8616)
(8635,8636) (8655,8656) (8737,8738) (8761,8762) (8781,8782) (8801,8802) (8821,8822)
```

All offsets in this report are excluded from that set unless stated.

---

## 2. Structural walk of the stream (representative file: `BASELINE_40x20x10`)

Stream length **11075**. `CLASS_MARKER = ff ff 01 00` followed by `<u16 name length>` and the ASCII
class name. 41 markers, in stream order (`marker` = offset of `ff ff 01 00`, `record` = first byte
after the class name, `len` = distance to the next marker):

```
marker    name@   record@    len   class
     6       12        30    197   moCommentsFolder_c
   203      209       227    207   moFavoriteFolder_c
   410      416       433    196   moHistoryFolder_c
   606      612       635     51   moHistoryFeatItemData_c
   657      663       678    233   moCompFeature_c
   890      896       918    219   moSelectionSetFolder_c
  1109     1115      1131    193   moSensorFolder_c
  1302     1308      1322    203   moDocsFolder_c
  1505     1511      1528     79   moDetailCabinet_c
  1584     1590      1612    573   moNotesAreaFtrFolder_c
  2157     2163      2184    224   moSurfaceBodyFolder_c
  2381     2387      2406    220   moSolidBodyFolder_c
  2601     2607      2626    196   moInkMarkupFolder_c
  2797     2803      2816    194   moEqnFolder_c
  2991     2997      3015    237   moMaterialFolder_c
  3228     3234      3246    343   moRefPlane_c
  3571     3577      3598   1332   moDefaultRefPlnData_c
  4903     4909      4933    205   moOriginProfileFeature_c
  5108     5114      5122    261   sgSketch
  5369     5375      5388    282   sgPointHandle
  5651     5657      5673    185   moCompRefPlane_c
  5836     5842      5860    303   moProfileFeature_c
  6139     6145      6157   1498   sgLineHandle
  7637     7643      7659    112   moSketchRegion_c
  7749     7755      7770    287   moSketchChain_c
  8036     8042      8055    244   moExtrusion_c
  8280     8286      8308     30   moPerBodyChooserData_c
  8310     8316      8327     55   moFaceRef_c
  8365     8371      8391     28   moEndFaceSurfIdRep_c
  8393     8399      8405     12   moFR_c
  8405     8411      8424     19   moExtObject_c
  8424     8430      8447    132   moCStringHandle_c
  8556     8562      8585    299   moFromSktEntSurfIdRep_c
  8855     8861      8879    176   moBBoxCenterData_c
  9031     9037      9048     41   moEndSpec_c
  9072     9078      9100    584   moDisplayDistanceDim_c
  9656     9662      9682    133   moFeatureDimHandle_c
  9789     9795      9821     36   ParallelPlaneDistanceDim_c
  9825     9831      9850    653   moLengthParameter_c
 10478    10484     10502    536   moFavoriteHandle_c
 11014    11020     11035     61   moFromEndSpec_c
```

**Important caveat on the marker walk.** `ff ff 01 00` marks a *class definition*, not an object
instance. It is the MFC `CArchive` "new class" tag: the first object of a class carries the tag plus
schema plus name, later objects of the same class are tagged by index only. In
`TWOFEATURES_pad_pad` there are 47 distinct `mo*`/`sg*` ASCII tokens and 48 marker records, yet the
file contains **two** extrusions, two sketches and two length parameters. The second
`moExtrusion_c` / `moEndSpec_c` / `moLengthParameter_c` objects have **no marker at all**. Any
addressing scheme built on marker-relative offsets works for the first object of a class and silently
fails for the rest.

---

## 3. Stream length per family (answer to Q1)

| family | member stream lengths | same length? |
|---|---|---|
| DEPTH (10/11/12/20/50 mm) | 11075 ×5 | yes |
| WIDTH (40/41/42/60/100 mm) | 11075 ×5 | yes |
| HEIGHT (20/21/22/30/50 mm) | 11075 ×5 | yes |
| OFFSET ((0,0)/(5,0)/(0,5)/(10,7) mm) | 11075 ×4 | yes |
| CIRCLE (r 10/11/20 mm) | 10556 ×3 | yes (but 519 bytes shorter than the rectangle layout) |
| REVERSED vs BASELINE | 11075, 11075 | yes |
| MIDPLANE vs BASELINE | 11075, 11075 | yes |
| PLANE | Front 11075, Top 11075, **Right 11147** | no (+72 for Right) |
| TWOFEATURES vs BASELINE | 11075, **19390** | no (+8315) |

Every scalar parameter is a fixed-width `float64` written in place, so no numeric change resizes the
stream. Length changes come only from structural change (profile type, sketch support plane,
extra features).

---

## 4. Differing byte ranges per family (answer to Q2)

Run counts are contiguous differing byte runs across *all* members of the family
(`out/analysis.json` has the full run lists; `out/analysis2.json` has hex context per run).

| family | diff runs | differing bytes | runs that are not control noise |
|---|---|---|---|
| DEPTH | 39 | 182 | 13 |
| WIDTH | 38 | 175 | — |
| HEIGHT | 36 | 158 | — |
| OFFSET | 40 | 261 | 29 (of which 15 are 2-byte id noise) |
| CIRCLE | 29 | 184 | — |
| REVERSED | 44 | 92 | 18 |
| MIDPLANE | 33 | 116 | 11 |
| PLANE (Front vs Top) | 56 merged runs | 1885 over the common prefix | — |
| TWOFEATURES | 722 | 6121 over the first 11075 bytes | — (whole tail shifts, see §8) |

---

## 5. Confirmed field offsets (answer to Q3)

All offsets are absolute in the canonical **11075-byte single-rectangular-pad** layout, decoded as
little-endian `float64` unless a width is given. "Marker-relative" is validated across all 31 files
where noted. Every claim below was verified by requiring the decoded value to equal the authored
parameter **in metres** for every member of the family simultaneously (exact equality, tolerance
1e-12), not by eyeballing one file.

### 5.1 Extrusion depth — CONFIRMED

| offset | marker-relative | value | evidence |
|---|---|---|---|
| **9882** | `moLengthParameter_c` **marker+57** (= record data start +32) | `+depth` (m) | 0.010/0.011/0.012/0.020/0.050 across DEPTH; unchanged by width, height, offset, reverse and mid-plane |
| 10442 | marker+617 | `+depth` | same 5-value column |
| 10466 | marker+641 | `+depth` | same 5-value column |
| 9954 | marker+129 | signed end-plane z: `+depth` blind-forward, `-depth` reversed, `+depth/2` mid-plane | |
| 10280 | marker+455 | `-depth` forward, `+depth` reversed | |
| 10304 | marker+479 | `-depth` forward, `+depth` reversed | |

`marker+57` was read back on all 31 corpus files and returned the authored depth in every one,
including the shorter CIRCLE layout (absolute 9363) and the shifted TWOFEATURES layout
(absolute 10120) and the Top/Right layouts (absolute 9954).

Consequence for writers: **9882 is the parameter, but it is not the only copy.** Editing 9882 alone
leaves five other depth-derived doubles stale.

### 5.2 Sketch rectangle geometry — CONFIRMED

Four corner points, each two `float64` (x, y) in sketch-plane coordinates, metres:

| x offset | y offset | value | enclosing marker |
|---|---|---|---|
| 6119 | 6127 | `(cx − w/2, cy − h/2)` | `moProfileFeature_c` (tail; the sketch-point records precede the `sgLineHandle` marker) |
| 6297 | 6305 | `(cx + w/2, cy + h/2)` | `sgLineHandle` |
| 6459 | 6467 | `(cx − w/2, cy + h/2)` | `sgLineHandle` |
| 6621 | 6629 | `(cx + w/2, cy − h/2)` | `sgLineHandle` |

Stride between the last three points is **162 bytes**. Confirmed independently by three families:
WIDTH pins the x columns (±20, ±20.5, ±21, ±30, ±50 mm), HEIGHT pins the y columns
(±10, ±10.5, ±11, ±15, ±25 mm), OFFSET pins both simultaneously as absolute (not centre-relative)
coordinates — e.g. `OFFSET_x10_y7` gives 6119 = −0.010, 6127 = −0.003, 6297 = +0.030, 6305 = +0.017.

### 5.3 End condition and direction flags — CONFIRMED (answer to Q6)

`moEndSpec_c`, marker 9031, 41 bytes total:

```
ff ff 01 00 0b 00 "moEndSpec_c" 00 00 01 00 00 00 00 00 00 00 [F] 00 00 00 00 00 [C] 00 00 00 00 00 00 00
                                                               ^9058                ^9064
```

| offset | marker-relative | width | meaning | observed |
|---|---|---|---|---|
| **9058** | `moEndSpec_c` **marker+27** | 1 byte | direction reverse flag | 0 forward, **1** reversed |
| **9064** | `moEndSpec_c` **marker+33** | 1 byte | `swEndConditions_e` code | 0 blind, **6** mid-plane |

`moFromEndSpec_c` (marker 11014) mirrors the direction flag:

| offset | marker-relative | width | observed |
|---|---|---|---|
| **11043** | `moFromEndSpec_c` **marker+29** | 1 byte | 0 forward, **1** reversed |

`REVERSED_d10` differs from `BASELINE` in exactly these two flag bytes plus derived geometry;
`MIDPLANE_d10` differs in exactly the one end-condition byte plus derived geometry. Read back over
all 31 files, `marker+27`/`marker+33`/`marker+29` are 0/0/0 everywhere except
`REVERSED_d10` (1/0/1) and `MIDPLANE_d10` (0/6/0).

The neighbouring bytes are `00`, so these are plausibly the low byte of 32-bit fields; the corpus
only exercises values 0, 1 and 6, so the true field width is **not determined**.

### 5.4 Bounding-box cache — CONFIRMED

`moBBoxCenterData_c`, marker 8855:

| offset | marker-relative | meaning |
|---|---|---|
| 8883 | marker+28 | body bbox centre **x** (m) |
| 8891 | marker+36 | body bbox centre **y** (m) |
| 8899 | marker+44 | body bbox centre **z** (m) |
| 8907 | marker+52 | bounding-sphere **diameter** = `2·√(hx²+hy²+hz²)` (m) |

Read back on all 31 files. Examples: `BASELINE` (0, 0, 5) mm, `OFFSET_x10_y7` (10, 7, 5) mm,
`DEPTH_d50` (0, 0, 25) mm, `MIDPLANE_d10` (0, 0, 0) mm, `REVERSED_d10` (0, 0, −5) mm,
`PLANE_TOP` (0, 5, 0) mm, `PLANE_RIGHT` (5, 0, 0) mm.
Diameter: `BASELINE` 45.8258 = 2√525 ✔, `WIDTH_w100` 102.4695 = 2√2625 ✔,
`HEIGHT_h50` 64.8074 = 2√1050 ✔, `DEPTH_d50` 67.0820 = 2√1125 ✔, `CIRCLE_r10` 30.0 = 2√225 ✔.

This is a derived cache, not an authored parameter.

### 5.5 Reference-plane display rectangles — CONFIRMED as derived

`moRefPlane_c` (3228) and `moDefaultRefPlnData_c` (3571, 1332 bytes) hold three display rectangles,
one per principal plane, sized to the model. The rule is `half-extent × 1.1`, centred on the body
bbox centre:

| offset | value | family that pins it |
|---|---|---|
| 3533 | `−1.1·(cx + w/2)`-style x extent (−22.0 for w=40; −55.0 for w=100; −22.55 for w=41) | WIDTH, CIRCLE, OFFSET |
| 3541 | `+1.1·h/2` (11.0 for h=20; 27.5 for h=50) | HEIGHT, CIRCLE |
| 3680 / 3688 | `±1.1·w/2` | WIDTH, CIRCLE |
| 3696 / 3704 | `±1.1·h/2` | HEIGHT, CIRCLE |
| 3727 / 3735 | Front-plane rectangle centre `(cx, cy)` | OFFSET |
| 4052, 4246, 4254 | `±1.1·w/2` again (second plane block) | WIDTH |
| 4068 | `−0.05·depth` | DEPTH |
| 4262 / 4270 | `±0.55·depth` | DEPTH |
| 4293 | `cx` | OFFSET |
| 4309 | `depth/2` | DEPTH |
| 4630, 4832, 4840 | `±1.1·h/2` (third plane block) | HEIGHT |
| 4638 | `+1.05·depth` | DEPTH |
| 4816 / 4824 | `±0.55·depth` | DEPTH |
| 4871 | `cy` | OFFSET |
| 4879 | `depth/2` | DEPTH |

`−0.05·depth` and `+1.05·depth` are exactly `depth/2 ∓ 0.55·depth`, i.e. the body's z range
[0, depth] expanded 5 % on each side — consistent with the `×1.1` rule. None of these are authored
parameters; they all follow from the sketch and the depth.

### 5.6 Dimension annotation geometry — CONFIRMED as derived

Inside `moLengthParameter_c` (9825), the depth dimension's witness points, in metres:

| offsets | content | baseline | `OFFSET_x10_y7` | `MIDPLANE_d10` | `REVERSED_d10` |
|---|---|---|---|---|---|
| 9914, 9922, 9930 | attach point A `(x, y, z_start)` | (20, 10, 0) | (30, 17, 0) | (20, 10, **−5**) | (20, 10, 0) |
| 9938, 9946, 9954 | attach point B `(x, y, z_end)` | (20, 10, 10) | (30, 17, 10) | (20, 10, **+5**) | (20, 10, **−10**) |
| 10111, 10119, 10127 | `(−x, z_start, −y)` | (−20, 0, −10) | (−30, 0, −17) | (−20, −5, −10) | (−20, 0, −10) |
| 10004 / 10370 | ±1.0 / ∓1.0 (direction unit) | +1 / −1 | +1 / −1 | +1 / −1 | **−1 / +1** |
| 10200 | `x / 5` exactly | 4 mm | 6 mm | 4 mm | 4 mm |

`x = cx + w/2`, `y = cy + h/2` (the rectangle's max corner). In the CIRCLE layout the same fields
appear at 9395, 9419, 9592 and 9681 with `x = r`, `y = r`, `x/5 = r/5` — which is why a naive
"radius lives here" reading of the circle stream is wrong (see §7).

The `x/5` relation at 10200 holds in every file measured, but I have no explanation for the factor
1/5 and do **not** claim it is a stored ratio rather than a coincidence of the default annotation
placement.

### 5.7 An indeterminate scratch double

A slot holding either `0.0` or exactly `0.016` m appears in different records in different files
(8150 = `moExtrusion_c`+114 in the DEPTH/WIDTH/REVERSED families; 5941 = `moProfileFeature_c`+105 in
the DEPTH/OFFSET/MIDPLANE families). Its value does not correlate with any authored parameter
(DEPTH gives 16, 16, 0, 16, 0 mm for d = 10, 11, 12, 20, 50). **Not determined.** I would treat it
as uninitialised or as a display/tessellation scratch value, not as a field.

---

## 6. OFFSET and PLANE coordinate encoding (answer to Q4)

### OFFSET

The sketch stores **absolute 2-D sketch-plane coordinates**, two `float64` per point (x then y),
never a centre plus a size. Translating the rectangle centre to `(cx, cy)` changes exactly the eight
corner doubles of §5.2 (plus the derived plane-display and annotation copies). There is no separate
"sketch origin" or "translation" field: the OFFSET family produced **zero** new numeric fields
relative to WIDTH/HEIGHT — the same eight offsets carry the change.

Confirmed for all three offsets, e.g. `OFFSET_x10_y7`:
6119/6127 = (−0.010, −0.003), 6297/6305 = (0.030, 0.017),
6459/6467 = (−0.010, 0.017), 6621/6629 = (0.030, −0.003).

### PLANE

Sketch coordinates are **plane-local and therefore identical** for Front, Top and Right
(±20, ±10 mm in all three). The plane is carried by a reference plus a basis, inside
`moSketchChain_c`:

| field | Front | Top | Right |
|---|---|---|---|
| support plane object id (`u32`) | **2** | **3** | **4** |
| axis code (`u32`, +10 bytes after the id) | **3** | **2** | **1** |
| 3×3 basis, 9 × `float64` row-major at marker+224 | **absent** | present | present |
| trailing `1.0` double | marker+248 | marker+320 | marker+320 |
| `moSketchChain_c` record length | 287 | 359 | 359 |

* The object ids 2/3/4 are exactly the Front/Top/Right ids in `native._BASE_OBJECTS`.
* In the rectangle layout the id sits at absolute **7958** = `moSketchChain_c` marker+209. In the
  CIRCLE layout the same field is at marker+**197** (record is 275 bytes, not 287) and reads 2 for
  the Front-plane circle. So the id is **not at a fixed marker-relative offset**; what is stable is
  that the axis code follows the id 10 bytes later. A reader must locate the pair, not hard-code 209.
* Axis code = 1-based index of the plane normal: Front normal +Z → 3, Top normal +Y → 2,
  Right normal +X → 1.
* The 9-double basis decodes to the expected sketch frames:
  Top → `(1,0,0), (0,0,−1), (0,1,0)`; Right → `(0,0,−1), (0,1,0), (1,0,0)`.
  Front is the identity and is **omitted entirely** — that is the whole 72-byte (9 × 8) difference.

**Why Top is still 11075 while Right is 11147.** Both grow `moSketchChain_c` by 72, but in
`PLANE_TOP` `moLengthParameter_c` shrinks by exactly 72 (653 → 581) and cancels it; in
`PLANE_RIGHT` it does not (653 → 653), so the file grows. All 41 other records are byte-identical in
length across the three files. I did not determine what the 72 bytes inside `moLengthParameter_c`
are — the record is the dimension annotation, and the Top-plane dimension apparently needs one fewer
72-byte block.

---

## 7. Circle profile: the radius is not stored (bonus finding)

The CIRCLE family stream is 10556 bytes and swaps `sgLineHandle` for
`sgArcHandle, sgExtEnt_c, moSketchExtRef_w, moCompSketchEntHandle_c, moPointBackedUpData_c`.

An exhaustive scan for a `float64` column equal to `(0.010, 0.011, 0.020)` or its negation over the
whole stream found **only three offsets — 9395, 9419, 9592 — and all three are the dimension
annotation fields of §5.6**, not a radius. There is no explicit radius double.

What is stored is the arc centre `(0, 0)` plus **a point on the circle at exactly 17°**:

| file | point at 6261/6269 (mm) | `|p|` | angle | error vs authored r |
|---|---|---|---|---|
| CIRCLE_r10 | (9.563047560, 2.923717047) | 10.000000000000 | 17.000000° | 0.0 |
| CIRCLE_r11 | (10.519352316, 3.216088752) | 11.000000000000 | 17.000000° | −1.8e-15 mm |
| CIRCLE_r20 | (19.126095119, 5.847434094) | 20.000000000000 | 17.000000° | 0.0 |

So the radius must be reconstructed as `hypot(x, y)`, and 17° is SOLIDWORKS' fixed start angle for a
`CreateCircleByRadius` circle.

---

## 8. TWOFEATURES: how the stream grows (answer to Q5)

Length 11075 → **19390 (+8315)**. Class-marker count 41 → 48.

**Earlier offsets do shift.** `moCompFeature_c` (the feature-tree record) grows 233 → 471, i.e.
**+238**, and everything from `moSelectionSetFolder_c` onward moves by exactly +238
(890 → 1128, 8036 → 8274, 9825 → 10063, 11014 → 11252). Comparing the baseline from byte 1128 to the
two-feature stream at +238 gives **9780 / 9947 = 98.32 % identical bytes**; the residual is the
second feature's ids and the changed body topology. The `D1` depth scalar moves 9882 → **10120**
(= 9882 + 238), which `marker+57` finds correctly.

Growth accounting:

| where | baseline | two features | delta |
|---|---|---|---|
| `moCompFeature_c` (feature tree) | 233 | 471 | **+238** |
| `moFromEndSpec_c` (last record, absorbs the second feature's objects) | 61 | 3320 | **+3259** |
| 7 appended class records | — | 4818 | **+4818** |
| total | | | **+8315** ✔ |

The seven appended records, in order:

```
moEdgeRef_c                  marker 14572   1015 bytes
moFaceRefPlnData_c           marker 15587    169
moCompFace_c                 marker 15756    590
moICE_c                      marker 16346    236
moCompSolidBody_c            marker 16582    350
moEndFace3IntSurfIdRep_c     marker 16932     56
moFromSktEnt3IntSurfIdRep_c  marker 16988   2402
```

`moFaceRefPlnData_c` / `moCompFace_c` / `moEdgeRef_c` are exactly what a face-supported sketch needs,
which matches the authoring (Sketch2 on the pad top face).

**The second feature has no class marker.** There is exactly one `moExtrusion_c`, one `moEndSpec_c`
and one `moLengthParameter_c` marker in the file. Reading `moLengthParameter_c` marker+57 returns
10.0 mm (feature 1) and there is no second marker to read 5.0 mm from. The second depth lives at
absolute **18238** (inside the `moFromSktEnt3IntSurfIdRep_c` span), found by
`decode_native_model` via the scalar header pattern, not by marker walking.

---

## 9. Comparison with `convert.adapters.solidworks.native.decode_native_model`

Run over all 31 files (`out/analysis5.txt`, `out/analysis5.json`).

### What the decoder gets right

* Class walk: 41 / 41 markers on the baseline, 45 for CIRCLE, 48 for TWOFEATURES — identical to my
  independent walk.
* Depth scalar: `D1` at **9882** with value 0.01 — the same offset my column scan confirmed, and it
  tracks correctly through every layout shift (9363 CIRCLE, 9954 Top/Right, 10120 TWOFEATURES).
* Rectangle bounds: exact for every WIDTH/HEIGHT/OFFSET member, e.g. `OFFSET_x10_y7` →
  `(−10.0, −3.0, 30.0, 17.0)` mm.
* `direction_code` = 1 for `REVERSED_d10` and `termination_code` = 6 for `MIDPLANE_d10` — so it does
  read offsets 9058 and 9064 correctly.
* Both features in TWOFEATURES: `Boss-Extrude1` 10.0 mm and `Boss-Extrude2` 5.0 mm (scalar at 18238),
  both sketches with correct rectangles — it finds the marker-less second object.
* No diagnostics emitted on any corpus file.

### What the decoder misses

1. **Support plane is wrong for non-Front sketches.** `PLANE_TOP` and `PLANE_RIGHT` both report
   `support_plane_id = 2` (Front) although the stream stores 3 and 4 at `moSketchChain_c`+209.
   `TWOFEATURES` Sketch2 also reports plane id 2 although it is supported by a face
   (`moFaceRefPlnData_c` / `moCompFace_c` are present). This is a real bug: a Top-plane or
   Right-plane part will be reconstructed on the wrong plane.
2. **No sketch-plane basis.** The 9-double basis at `moSketchChain_c`+224 and the axis code are not
   read, so the plane orientation cannot be recovered even if the id were right.
3. **Circle radius is reconstructed lossily.** The decoder reports 9.999999999999554 / 10.9999999999996 /
   20.000000000000355 mm, whereas the stored point at 6261/6269 reproduces 10 / 11 / 20 mm to
   ≤1.8e-15 mm. The arc start angle (17°) is not captured at all.
4. **Only one of six depth copies is modelled.** The decoder exposes 9882 but not 9954, 10280, 10304,
   10442, 10466. A write path that patches only the exposed offset produces an internally
   inconsistent stream.
5. **No bounding-box cache.** `moBBoxCenterData_c`+28/36/44/52 (centre and bounding-sphere diameter)
   is not decoded, so it cannot be recomputed on write.
6. **No reference-plane display extents.** The `×1.1` display rectangles in `moRefPlane_c` /
   `moDefaultRefPlnData_c` are not modelled.
7. **`moFromEndSpec_c`+29 (the mirrored direction flag) is not read**, so `direction_code` has a
   second, unmodelled copy.
8. `native_end` for the extrusion operation is reported as `11075`, i.e. end-of-stream, rather than
   the `moExtrusion_c` record end (8280). Harmless for reading, misleading for slicing.

---

## 10. What I could not determine

* The true width of the `moEndSpec_c` flag fields at +27 and +33 (only values 0, 1, 6 observed; the
  surrounding bytes are zero, so 1-, 2- or 4-byte fields all fit).
* What the 72 bytes are that `moLengthParameter_c` loses in `PLANE_TOP` but not in `PLANE_RIGHT`.
* The meaning of the 0.0/0.016 m scratch double (§5.7).
* Why the annotation field at marker+375 of `moLengthParameter_c` equals `x/5` exactly.
* The internal structure of the second feature's objects inside the expanded `moFromEndSpec_c`
  (3320 bytes) — I confirmed the second depth is at 18238 but did not segment that block, because
  it has no class markers to segment on. Doing so needs the MFC class-index tag decoding that
  `Native.py`'s `_CURRENT_MARKER` / `_LEGACY_MARKER` constants hint at.
* Extrusion end conditions other than blind and mid-plane. `T1 = 5`
  (`swEndCondOffsetFromSurface`) raised SOLIDWORKS "Internal application error" without a
  pre-selected surface, so those code paths were not corpus-tested.

---

## 11. Files on disk

```
.rescratch/corpus/
  REPORT.md                     this report
  parts/                        31 .SLDPRT (30 corpus + step1_pad)
  scripts/
    swcom.py                    COM helper: com_value, working NewDocument/SelectByID2/SaveAs4 wrappers
    step1_probe.py              step 1, records which COM call form works
    dump_enums.py               reads swconst.tlb enums without launching SOLIDWORKS
    probe_midplane.py           finds swEndCondMidPlane by experiment
    probe_constants.py          demonstrates that gencache early binding is unavailable
    build_corpus.py             authors the corpus (accepts file names to rebuild selectively)
    manifest_table.py           renders out/corpus_table.txt
    analyse.py                  per-family length + diff runs + float64 column scan
    analyse2.py                 control-noise baseline + per-run hex context
    analyse3.py                 varying float64 columns attributed to class records
    analyse4.py                 PLANE record lengths, flag byte tables, decoder dump
    analyse5.py                 plane-reference integer scan, circle radius search, whole-corpus decode
    analyse6.py                 validates marker-relative fields across all 31 files
    analyse7.py                 moSketchChain_c record anatomy
    analyse8.py                 circle arc encoding + radius reconstruction
    analyse9.py                 class-marker vs ASCII-token audit (multi-feature segmentation)
    analyse10.py                step1_pad vs BASELINE record-length diff (session document name)
  out/
    manifest.json  corpus_table.txt  step1_probe.json  enums.json
    analysis.json  analysis2.json  analysis3.{json,txt}  analysis4.{json,txt}
    analysis5.{json,txt}  analysis6.{json,txt}  analysis7.{json,txt}
    analysis8.{json,txt}  analysis9.{json,txt}  analysis10.txt
```
