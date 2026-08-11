<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# `Contents/Config-0` — node plan, the `moDetailDefs_c` tree, and an emitted one that opens

Status: **confirmed**. A constructively emitted `Contents/Config-0` was measured opening in
SOLIDWORKS 2025 with the correct volume and centre of mass, with the full 19-node feature tree, and
also with a changed part name whose byte sequence exists in no corpus file. Kit emits it from
`src/convert/adapters/solidworks/config0.py`.

Current closure: the historical residual accounting in §§5.7 and 7–8 records the path used to
recover the grammar, but it is superseded by the generated `config0_program.py` field program. The shipped
writer now reports `CONFIG_OPAQUE_BYTES = 0`; its 25,214-byte reference stream is emitted from
typed operations with contiguous source offsets, every operation has a recovered serializer owner,
and custom raw prologue bodies are rejected. The two-view default, fillet/chamfer, and
linear/circular-pattern annotation managers are likewise typed programs with zero opaque bytes.
No corpus stream or donor block is read at runtime.

The stream is document-level. It carries the units tables, the annotation and dimension style tree,
the named view table, the lights, the equation manager and the material appearance. Its **only**
feature-dependent content is a three-node atom record per feature, and a per-solid-body 16-byte
entry in the `moCThreadRefMgr_c` tail.

`../measurements/MEASURE.md` classes this stream load-critical. Together with `Contents/CMgr` it was
one of the two remaining load-critical streams with no recorded grammar.

## 1. The prologue, and base 4

The stream does **not** open with a node. Byte 0 is a class definition of **`moPart_c`**, followed by
a 12-byte `moPart_c` body, and only then the first node:

```
ff ff 01 00 08 00 6d 6f 50 61 72 74 5f 63   moPart_c definition, schema 1, 14 bytes
08 0b 00 00 00 00 00 00 50 46 00 00         moPart_c body, 12 bytes
ff ff 01 00 0c 00 ...                       moNodeName_c definition, node 0, at offset 26
```

So the prologue is **26 bytes**, and the map counter base is **4**. Base 4 is confirmed
independently: `moPart_c` takes class index 2 and object index 3, so the counter stands at 4 when
`moNodeName_c` is defined, which is the index `../archive/EXTERNAL_CLASSES.md` §2 observes for it.
`config0.py` states this as `PROLOGUE_LENGTH = 26` and `MAP_COUNTER_BASE = 4`.

Replaying the traced node sequence confirms the 26 bytes are exact rather than fitted, at three
feature counts:

```
boss1: stream 25212  nodes 123  modelled 25186  implied header = 26  tag mismatches = 0
boss2: stream 25316  nodes 126  modelled 25290  implied header = 26  tag mismatches = 0
boss3: stream 25420  nodes 129  modelled 25394  implied header = 26  tag mismatches = 0
```

Zero tag mismatches and the cursor landing exactly on the stream length.

Related correction: `../archive/EXTERNAL_CLASSES.md` §4.1 calls `moNodeName_c` "the **first** class
definition of `Contents/Config-0`". It is the **second**; `moPart_c` is first. The index 4 it quotes
is right.

### 1.1 Correction to `../archive/MULTISTREAM.md` §2

`MULTISTREAM.md` §2 reads as though `archive.py`'s `segment()` plus `re/data/class_layouts.json`
already tiles this stream statically at "a map-counter base of 4 and a 6-byte stream header". It does
not, and cannot. Measured over all 206 distinct payloads at base 4: **0 segmented, 206 failed**,
every one at offset 6, because the prologue is 26 bytes and `segment()` reads `6d 6f` ("mo") as a
tag.

The classes are simply absent from the layout table:

```
layout table classes: 76
  moPart_c         ABSENT
  moNodeName_c     ABSENT
  moRelMgr_c       ABSENT
  moAtom_c         ABSENT
  suObList         present
```

The §2 result was produced from the **cdb runtime trace**, which supplies object boundaries directly.
It is not a static result. This is the dependency `EXTERNAL_CLASSES.md` §5.2 flags: static
`Config-0-ResolvedFeatures` segmentation needs static `Config-0`, which needs the layouts of the 40
classes `Config-0` defines. Those layouts are still absent, and a template-guided segmenter was
built instead.

## 2. The 123-node plan

123 nodes at one feature, **39 class definitions**, base 4. `config0.py` carries the plan as
`NODE_PLAN`, one row per node: the tag kind (`definition`, `classref`, `objectref`, `null`), the
class name, the schema, and the body. Class and object reference indices are **resolved by target
node** and recomputed by `assign_indices`, never recorded, because they shift between documents (the
`moDirectionLight_c` reference is index 75 in `boss1` and 76 in `TWOFEATURES_pad_pad`).

Where the bytes are:

| node  | owner                     | bytes    | content                                             |
| ----- | ------------------------- | -------- | --------------------------------------------------- |
| 36–58 | `moDetailDefs_c` tree     | 17484    | the annotation, dimension, table and label styles   |
| 1     | `moVisualProperties_c`    | 621      | material `Steel`, `defaultplastic`, the `.p2m` path |
| 86–95 | `moView_c`                | ~200 ea  | the 11 named views                                  |
| 115   | `moCThreadRefMgr_c` frame | 299      | atom high-water pair, per-solid-body doubles        |
| 24    | `moTransRefPlaneData_c`   | 249      | the three reference-plane transforms                |
| 105   | `moAnnotationView_c`      | 210      | the saved annotation view                           |
| 59–84 | light frames              | 44–227   | `Ambient-1`, `Directional-1..3`                     |
| 2–20  | the 18 unit records       | 56–73 ea | length, angle, density, force, time, frequency, …   |
| 33–35 | `moAtom_c` frame          | 112      | the atom region, §3                                 |

Across the 47 one-feature 18000 parts in the corpus, **98.38 % of the body bytes are byte-constant**
(23802 of 24157, 391 varying bytes in 16 varying nodes). Every one of the 47 writes the same 123
nodes in the same order with the same class-definition sequence, so there is **no permutation
effect** here, unlike `Contents/Definition`.

Static segmentation result, over the same-generation payloads:

```
18000 payloads : 90
walked exactly : 89
```

"Walked exactly" means the definition sequence matches the template, every tag matches its expected
kind and resolved index, and the cursor lands on `len(blob)` with no slack. Re-emitting every one of
those 89 from the node model with all indices recomputed is **byte-identical 89 of 89**. The single
failure is `examples/.../example.SLDPRT`, which has 49 class definitions rather than 39.

## 3. The atom region — the only feature-dependent content

After the `moAtom_c` class definition at node 33, per feature: a `null` tag plus a 24-byte `moNode_c`
scalar block, a `null` tag plus a 58-byte atom record, and a `classref moAtom_c` between consecutive
features. The final atom record carries a 12-byte tail. Measured on `THREEFEATURE_pad_cut_pad`:

```
null 24  0100000000000040 ffffffff 00000000 fffeff00 00000000
null 58  ... 67000000 ... 2f000000 2f000000 ... a33b0000 ... a33b0000 06000000
classref moAtom_c 0
null 24  (identical)
null 58  ... 66000000 ... 28000000 28000000 ... a33b0000 ...
classref moAtom_c 0
null 24  (identical)
null 70  ... 65000000 ... 20000000 20000000 ... a33b0000 ... + 50460000 10270000 00000010
```

Decoded: the **atom id** (`0x65`, `0x66`, `0x67`, newest first), the **feature tree id** written
twice (32, 40, 47 — the same tree ids `MULTISTREAM.md` §3 reports for `CMgr`), a per-document
**session stamp** repeated twice (`0xa33b` here, `0x76a5` in `BASELINE_40x20x10`, `0xc72f` in
`TWOPAD_d5`), and a flag that is 0 on the first record and 1 on the rest. The 12-byte tail is
`u32 18000, u32 10000, u32 0x10000000` — the first word is the document generation, so it is derived.

Node 115 opens with `u32 highest_atom_id, u32 next_free_id` at body offset 25: `(0x65, 0x67)` at one
feature, `(0x66, 0x69)` at two, `(0x67, 0x6b)` at three — the highest id and a free-id watermark
advancing by 2 per feature. Those 8 bytes are declared; `config0.py` writes them with
`high_water_body`.

**The per-feature step is 88 bytes**, not 104. Measured over 1→5 features from the encoder:
`growth [88, 176, 264, 352]`, `per feature step [88, 88, 88, 88]`.

### 3.1 The extra 16 bytes are per solid body, not per feature

`MULTISTREAM.md` §3 gives `(2+24) + (2+58) + (2+0) + 16 = 104` per feature. The first three terms are
right. The 16-byte term is **per solid body**:

| part                       | features | solid bodies | node 115 body |
| -------------------------- | -------- | ------------ | ------------- |
| `BASELINE_40x20x10`        | 1        | 1            | 299           |
| `TWOPAD_d5`                | 2        | 1            | **299**       |
| `THREEFEATURE_pad_cut_pad` | 3        | 1            | **299**       |
| `boss2_front_rect_blind`   | 2        | 2            | 315           |
| `boss3_front_rect_blind`   | 3        | 3            | 331           |

`TWOPAD_d5` stacks two pads into one body and **does not grow**. The `boss` family makes one disjoint
body per feature, so there the two rules coincide and `88 + 16` reads as 104. The `+16` is a pair of
`f64` inside the `moCThreadRefMgr_c` tail. `config0.py` states it as `PER_SOLID_BODY_BYTES = 16`
against `PER_FEATURE_ATOM_BYTES = 88`.

## 4. The `single_length_unit` variant, and the "+38 fifth-feature anomaly"

Only five of the 39 class-definition regions ever vary in span across parts:

| region                | boss1 | boss4 | boss5   | boss6 | `boss_midplane` | `PLANE_TOP` |
| --------------------- | ----- | ----- | ------- | ----- | --------------- | ----------- |
| `moNodeName_c`        | 56    | 56    | 56      | 56    | 56              | **58**      |
| `moLengthUserUnits_c` | 157   | 157   | **91**  | 157   | **91**          | 157         |
| `moAtom_c`            | 112   | 376   | **464** | 552   | 112             | 112         |
| `moAnnotationView_c`  | 324   | 324   | 324     | 324   | 324             | **256**     |
| `moCThreadRefMgr_c`   | 332   | 380   | **396** | 412   | 332             | 332         |

`moAtom_c` = 112 + 88·(n−1) and `moCThreadRefMgr_c` = 332 + 16·(n−1), both exactly on trend at n=5.
**Nothing is inserted at the fifth feature.** `boss5` is 66 bytes light because its
`moLengthUserUnits_c` region is 91 bytes instead of 157, and `104 − 66 = 38`. That is the whole of the
apparent anomaly.

The 66 bytes are one object. The 157-byte form is
`definition (25) + body (64) + classref moLengthUserUnits_c (2) + body (64) + null (2)`; the 91-byte
form is `definition (25) + body (64) + null (2)` — the **secondary (dual) length unit record is
absent**. `boss_midplane` shows the 91-byte form at one feature and `PLANE_TOP` the 157-byte form, so
the variant is independent of feature count and of stream size. `boss5` happens to be the corpus's
only 5-feature part and it happens to be a `single_length_unit` document; a one-part coincidence read
as a rule is what made the step look non-constant.

Corpus distribution over the 89 walked payloads:

```
(1, 'dual_length_units')    47      (5, 'single_length_unit')    1
(1, 'single_length_unit')    1      (6, 'dual_length_units')     1
(2, 'dual_length_units')    27      (7, 'dual_length_units')     1
(3, 'dual_length_units')     5      (8, 'dual_length_units')     1
(4, 'dual_length_units')     5
```

`config0.py` carries it as the `dual_length_units` parameter with
`SECONDARY_LENGTH_UNIT_POSITION = 4`. `encode_config0_stream(dual_length_units=False)` emits
**25148 bytes**, exactly 66 less than the 25214 default.

## 5. The `moDetailDefs_c` tree — nodes 36 to 58

Nodes 36–58 are **not** 80 like-shaped records. They are **one `moDetailDefs_c` object tree**,
17484 bytes of node bodies plus 22 two-byte object tags, and `moDetailDefs_c` starts **36 bytes into
node 36's body**, immediately after `moRelMgr_c`'s own body.

### 5.1 Correction to the "80 records" reading

The earlier reading was that the region is 80 records each shaped
`64-byte <IIdIIdIIIIIIII prefix, font name, tail`, with the record boundary 64 bytes before each font
name. Measured: **only 10 of the 80 supposed 64-byte prefixes unpack to plausible unit values.** The
other 70 give values like `(2851864576, 1649267441, 5.56e-309, 178651136, 41231686, 4.04e-319, …)`.

The `struct.pack(struct.unpack(x)) == x` check that reading relied on is **vacuous**: for a
fixed-width little-endian format it reproduces the input for _any_ 64 bytes, so it never tested the
boundary at all.

The ten that do look like unit records **are** unit records, reached through `moBaseDimDef_c`, which
is why the "+64 rule" fits the first ten and is arbitrary for the rest.

The repeated shape is `utCharFormat_c` — a `CString` plus exactly 68 bytes — and there are **81
instances** of it in the region, not 80.

### 5.2 How the owner was found

`moPart_c::Serialize` does not read the table itself. It calls the model serializer through the
vtable and then reaches the detail defs by accessor:

```c
  if (0xc7c < uVar4) {
    (**(code **)(*(longlong *)param_1 + 0x4a8))();
    (**(code **)(*(longlong *)param_1 + 0x4b0))(param_1,param_2);
    pmVar8 = moModel_c::getDetailDefs(param_1);
```

`moModel_c::getDetailDefs` returns `moDetailDefs_c *` from `this + 0xac8`, which named the class.
`moDetailDefs_c` has **no entry in `out/serialize_map.json`** (that map is sldmodu only); its
`Serialize` is slot 5 of its sldmfcu vftable:

```
VT moDetailDefs_c @ 3cf20350 slots=17
  5|3cb15020|moDetailDefs_c::Serialize
```

### 5.3 Recovered function addresses

sldmodu, imagebase `0x4b1e0000`:

| function                           | address                              |
| ---------------------------------- | ------------------------------------ |
| `moPart_c::Serialize`              | `0x4c285f50`                         |
| `moModel_c::Serialize`             | `0x4c2813e0` (vtable offset `0x4b0`) |
| `moModel_c::getDetailDefs`         | `0x4c08a140`                         |
| `moRelMgr_c::Serialize`            | `0x4c392f10`                         |
| `moCThreadRefMgr_c::Serialize`     | `0x4b38b750`                         |
| `moTransRefPlaneData_c::Serialize` | `0x4c732bc0`                         |
| `moView_c::Serialize`              | `0x4c288eb0`                         |
| `moAnnotationView_c::Serialize`    | `0x4c274100`                         |
| `moAtom_c::Serialize`              | `0x4bd68d80`                         |
| `moNodeName_c::Serialize`          | `0x4c1db8a0`                         |

sldmfcu, imagebase `0x3c9f0000` — `moDetailDefs_c::Serialize` is at file offset `0x125020`, export
ordinal 3387:

| function                                     | address        |
| -------------------------------------------- | -------------- |
| `moDetailDefs_c::Serialize`                  | `0x3cb15020`   |
| `utCharFormat_c::Serialize`                  | `0x3ca7e750`   |
| `moDimDefs_c::Serialize`                     | `0x3cb18f10`   |
| `moAnnotationDefs_c::Serialize`              | `0x3cb13520`   |
| `moTableDefs_c::Serialize`                   | `0x3cb1d860`   |
| `moLabelDefs_c::Serialize`                   | `0x3cb1be10`   |
| `moBaseDimDef_c::Serialize`                  | `0x3cb13f90`   |
| `moLinearDimDef_c::Serialize`                | `0x3cb1bfe0`   |
| `moAngleDimDef_c::Serialize`                 | `0x3cb13260`   |
| `moAngOrdinateDimDef_c::Serialize`           | `0x3cb13160`   |
| `moArcLengthDimDef_c::Serialize`             | `0x3cb13850`   |
| `moChamferDimDef_c::Serialize`               | `0x3cb14910`   |
| `moDiameterDimDef_c::Serialize`              | `0x3cb18e60`   |
| `moHoleCalloutDimDef_c::Serialize`           | `0x3cb1bb70`   |
| `moOrdinateDimDef_c::Serialize`              | `0x3cb1cec0`   |
| `moRadialDimDef_c::Serialize`                | `0x3cb1d120`   |
| `moBaseAnnotationDefs_c::Serialize`          | `0x3cb13d20`   |
| `moBalloonDefs_c::Serialize`                 | `0x3cb139c0`   |
| `moBendNoteDefs_c::Serialize`                | `0x3cb144a0`   |
| `moDatumDefs_c::Serialize`                   | `0x3cb14a90`   |
| `moGtolDefs_c::Serialize`                    | `0x3cb1ae60`   |
| `moNoteDefs_c::Serialize`                    | `0x3cb1cd30`   |
| `moRevCloudDefs_c::Serialize`                | `0x3cb1d1d0`   |
| `moSFDefs_c::Serialize`                      | `0x3cb1d770`   |
| `moViewLocationLabelDefs_c::Serialize`       | `0x3cb1da40`   |
| `moWeldDefs_c::Serialize`                    | `0x3cb1e230`   |
| `moGeneralTableDefs_c::Serialize`            | `0x3cb1ac80`   |
| `moTitleBlockTableDefs_c::Serialize`         | `0x3cb1da30`   |
| `moBOMTableDefs_c::Serialize`                | `0x3cb13860`   |
| `moBendTableDefs_c::Serialize`               | `0x3cb14570`   |
| `moFamilyTableDefs_c::Serialize`             | `0x3cb1a110`   |
| `moHoleTableDefs_c::Serialize`               | `0x3cb1bc00`   |
| `moPunchTableDefs_c::Serialize`              | `0x3cb1cfc0`   |
| `moRevisionTableDefs_c::Serialize`           | `0x3cb1d220`   |
| `moWeldTableDefs_c::Serialize`               | `0x3cb1e2b0`   |
| `moDrawingDefs_c::Serialize`                 | `0x3cb19ee0`   |
| `moDrViewLabelData_c::Serialize`             | `0x3cb29f10`   |
| `moAuxLabelData_c::Serialize`                | `0x3cb29db0`   |
| `moDetailLabelData_c::Serialize`             | `0x3cb29e30`   |
| `moMiscLabelData_c::Serialize`               | `0x3cb2a3a0`   |
| `moSectionLabelData_c::Serialize`            | `0x3cb2a450`   |
| `moSFDataHelper_c::Serialize`                | `0x3cb1d320`   |
| `moNoteDataHelper_c::Serialize`              | `0x3cb1c170`   |
| `moWeldDataHelper_c::Serialize`              | `0x3cb1dbf0`   |
| `moGTolDataHelper_c::Serialize`              | `0x3cb1a180`   |
| `moCenterMarkSymDataHelper_c::Serialize`     | `0x3cb14650`   |
| `moDatumFeatureDataHelper_c::Serialize`      | `0x3cb14b80`   |
| `moDatumTargetDataHelper_c::Serialize`       | `0x3cb14d10`   |
| `moAnnotationDataHelper_c::Serialize`        | `0x3cb132e0`   |
| `moGTolDlgDataFrame_c::Serialize`            | `0x3cb1a6c0`   |
| `moGTolDlgDataTol_c::Serialize`              | `0x3cb1ab80`   |
| `moGtolItemDatum2022_c::Serialize`           | `0x3cb1af70`   |
| `moGtolItemIndicator_c::Serialize`           | `0x3cb1b2c0`   |
| `moSwiftGtsOptions_c::Serialize`             | `0x3caf9fa0`   |
| `utLineWidthPrintData_c::Serialize`          | `0x3cb08680`   |
| `utLineWidth_c::Serialize`                   | `0x3cb08110`   |
| `uiLFConfig_c::Serialize`                    | `0x3ca67450`   |
| `moLayerData_c::Serialize`                   | `0x3cb1bf20`   |
| `moUserUnits_c::Serialize`                   | `0x3cbc8e80`   |
| `moLengthUserUnits_c::Serialize`             | `0x3cbc8cb0`   |
| `moAngleUserUnits_c::Serialize`              | `0x3cbc89e0`   |
| `moWeldDataHelper_c::moWeldDataHelper_c`     | `0x3ca911e0`   |
| `moGTolDlgDataFrame_c::moGTolDlgDataFrame_c` | `0x3ca906a0`   |
| version gate helper                          | `FUN_3ca67520` |

Every version gate is read off `moArchiveHelper_c + 0x780` through `FUN_3ca67520`, which is the
mechanism `DEFINITION.md` §4 documents. At generation 18000 the legacy branch `if (uVar7 < 0xf5c)`
is dead, so the layout is the modern branch plus the ungated tail, and every gate in it is taken.

### 5.4 The member chain

`moDetailDefs_c` member classes, from `moDetailDefs_c::moDetailDefs_c`:

| offset                  | class                                           |
| ----------------------- | ----------------------------------------------- |
| `+0x90` `+0xa0` `+0xa8` | `utCharFormat_c` (`operator_new(0x60)`)         |
| `+0xb0`                 | `utLineWidthPrintData_c` (`operator_new(0x28)`) |
| `+0x1390`               | `moDimDefs_c`                                   |
| `+0x1ef8`               | `moAnnotationDefs_c`                            |
| `+0x23f0`               | `moTableDefs_c`                                 |
| `+0x2730`               | `moLabelDefs_c`                                 |
| `+0x2e8`                | `moSFDataHelper_c`                              |
| `+0x4b8`                | `moNoteDataHelper_c`                            |
| `+0x710`                | `moWeldDataHelper_c`                            |
| `+0x980`                | `moGTolDataHelper_c`                            |
| `+0xb68`                | `moCenterMarkSymDataHelper_c`                   |
| `+0xcb8`                | `moDatumFeatureDataHelper_c`                    |
| `+0xdc0`                | `moDatumTargetDataHelper_c`                     |
| `+0xf48`                | `moSwiftGtsOptions_c`                           |

`moDimDefs_c` holds ten `moBaseDimDef_c`-derived styles, and `moBaseDimDef_c::Serialize` ends with
direct virtual calls on `+0xf0` `moLengthUserUnits_c`, `+0xf8` `moAngleUserUnits_c`, `+0xe8`
`utCharFormat_c` and `+0xd0`/`+0xd8` `uiLFConfig_c`. Direct calls emit **no** tag. The 22 tags come
from inside `moLengthUserUnits_c::Serialize`, which finishes with a real archive object write
`::operator<<(param_1,(moLengthUserUnits_c **)(this + 0xb8))`. That predicts ten tags for ten
dimension styles, each non-null one contributing a 64-byte body and one further tag. The region has
exactly **8 `classref moLengthUserUnits_c` + 10 `null` = 18 tags** in that group, i.e. eight styles
carry a dual length unit and two do not — an independent structural prediction that came out right,
and the reason the walker sees `CLS 64 / nul 442 / nul 434 / CLS 64 / …` rather than a flat array.

`moUserUnits_c::Serialize` is 62 bytes
(`long long double long long double long long int int double ushort int`); `moLengthUserUnits_c` adds
a `ushort` and the tagged reference, which is the real layout of the 64-byte bodies — not
`<IIdIIdIIIIIIII`.

### 5.5 `utCharFormat_c`, the shape mistaken for "the record"

Store side, the modern layout: `CString` font name, then 68 bytes —
`double` height, `int`, `double`, `uint`, `double`, `double`, `double`, `double`, `double`,
`uint` weight. The read side names the fields independently through its version defaults: `+0x28`
defaults to `0x3f50624dd2f1a9fc` = 0.001, and `+0x38` is compared against 1.0 and passed to
`_finite`, so it is the width factor.

Checked against the reference bytes at node-36 offset 723:

```
   723 STR +32 'Century Gothic'
   755 79e9263108ac6c3f d=0.0035          <- +0x10 height, 3.5 mm
   763 00000000                           <- +0x18
   767 0000000000000000 d=0               <- +0x20
   775 00000000                           <- +0x30
   779 fca9f1d24d62503f d=0.001           <- +0x28, equals the version default
   787 000000000000f03f d=1               <- +0x38 width factor
   795 0000000000000000                   <- +0x40
   803 0000000000000000                   <- +0x48
   811 000000000000f03f d=1               <- +0x50
   819 90010000          u32=400          <- +0x58 weight
```

Ends at 823, where `moDimDefs_c` begins with `u32 4` and then arrow sizes 0.001016, 0.003302,
0.00635. Nothing is left over.

### 5.6 Four modelling bugs the region decode exposed

The decoder is a field-program interpreter, so a wrong width fails hard at a named path rather than
producing a plausible wrong answer. Four bugs were located that way, and each was a place where the
generated program silently dropped bytes:

1. **`moWeldDataHelper_c` +0x158.** The store branch ends with a two-trip loop
   `AR_put_uchar(*pmVar3); virtual Serialize(pmVar5)` where the vtable variable and the object
   variable differ (`pmVar4` versus `pmVar5`), and the alias was assigned without a cast
   (`pmVar4 = this + 0x158;`). The constructor shows
   `_eh_vector_constructor_iterator_(this + 0x158, 0x60, 2, utCharFormat_c::utCharFormat_c, …)`, i.e.
   an array of two `utCharFormat_c` at `+0x158` and `+0x1b8`. Dropping them cut the decode short at
   region offset 13920 — the failure the earlier pass attributed to `moSFDataHelper_c`, whose own
   program is correct.
2. **`moNoteDataHelper_c` +0x248.** `AR_put___uint64` writes an 8-byte map size, then a
   `while (cVar1 == '\0')` loop writes that many entries. The 8-byte put was dropped as an unknown
   width and the loop body's two puts leaked in as unconditional fields, and `4 + 4` happened to
   equal the 8 bytes of a zero map size. Modelling it as a count-driven repeat is what makes it right
   for a non-empty map.
3. **`moGTolDataHelper_c` +0x08.** `su_CPtrArray::GetSize` then `AR_put_long`, then
   `if (0 < iVar1) { do { getGtolDlgFrame(...); virtual Serialize } while … }`. The guard was
   unresolvable, so the whole object array was dropped. `moGTolDlgDataFrame_c::Serialize`
   `0x3cb1a6c0` was not in any earlier dump and had to be decompiled.
4. **`moDatumTargetDataHelper_c` +0x78.** `mgVector_c::save((mgVector_c *)(this + 0x78), param_1)` is
   a serialize under a different method name and was dropped, costing exactly 24 bytes.
   `mgVector_c::save` is an import, so it has no body in the sldmfcu program; its width is fixed by
   three independent measurements that agree: the gap is exactly 24 bytes, the member at `+0x78` is
   followed by `+0x90` in the same function so the object spans `0x78..0x8f`, and
   `mgVector_c::mgVector_c` is called elsewhere with three `double` arguments.

### 5.7 Historical region result (superseded)

```
region bytes                     17484
declared span byte-identical     True
declared span bytes              17446
full region reconstruction       True over 17484 bytes
utCharFormat_c instances         81
recovered class programs         65
```

At this recovery checkpoint, two named residual spans remained in the region:

- **`RESIDUAL_MORELMGR_C_HEAD`, 36 bytes** — `moRelMgr_c`'s own body ahead of `moDetailDefs_c`.
  `EQUATIONS.md` records the `u16` count at `+0`, and every one of the 89 walked payloads has
  `count == 0` there with no `moRelation_c` class definition. Reading the store branch of
  `moRelMgr_c::Serialize` `0x4c392f10` accounts for 34 of the 36:
  `Serialize(+0x10)` 4, `CString +0x170` 4 (empty), `long +0x178` 4, `su_CTime +0x180` 4,
  `long +0x150` 4 = 1, `long +0xf4` 4 = −1 (matching the read side's `if (*(int *)pmVar2 == -1)`
  check), `Serialize(+0xa0)` 2, `long +0x1b0` 4 = −1, feature-parameter count 4 = 0, trailer 2. The
  span is carried whole rather than split because the two bytes at `+2` sit inside the relation
  container and one sample cannot separate them from the count word.
- **`RESIDUAL_MODETAILDEFS_C_TAIL`, 2 bytes** — `moDetailDefs_c::Serialize` returns after
  `int +0x1b8`, and the last two bytes of node 58's body are written by its caller.

## 6. The oracle

SOLIDWORKS 2025, `KIT_SOLIDWORKS_ORACLE=1`, one fresh process per candidate, dialog dismisser
running, process sweep between candidates, control before **and** after, per `../../METHODOLOGY.md`
§9. Candidates built with
`build_sldprt(streams, file_id=archive.file_id, signatures=container_signatures(blob))`, only
`Contents/Config-0` replaced. Host and control `BASELINE_40x20x10.SLDPRT`, one feature,
`_MO_VERSION_18000`.

| rung | candidate                                          | bytes | result      | volume mm³            | centre mm   |
| ---- | -------------------------------------------------- | ----- | ----------- | --------------------- | ----------- |
| 0    | control, pristine `BASELINE_40x20x10`              | —     | opened      | 8000.000000000001     | —           |
| 1    | container rebuilt with the original `Config-0`     | 25214 | opened      | 8000.000000000001     | `[0, 0, 5]` |
| 2    | walker segment → re-emit round-trip                | 25214 | opened      | 8000.000000000001     | `[0, 0, 5]` |
| 3    | `Config-0` of `WIDTH_w60` (18000, 1 feature)       | 25214 | opened      | 8000.000000000001     | `[0, 0, 5]` |
| 4    | `Config-0` of `THREEFEATURE_pad_cut_pad` (3 feat.) | 25390 | **refused** | —                     | —           |
| 5    | **`encode_config0_stream()`**                      | 25214 | **opened**  | **8000.000000000001** | `[0, 0, 5]` |
| 6    | **`encode_config0_stream(part_name="KitPart")`**   | 25216 | **opened**  | **8000.000000000001** | `[0, 0, 5]` |
| 0    | control after the batch                            | —     | opened      | 8000.000000000001     | —           |

Both controls returned the identical volume, so **`control healthy: True`** and the batch stands.
Every opened candidate, rungs 5 and 6 included, reported the complete 19-node feature tree identical
to the control:

```
Comments, Favorites, History, Selection Sets, Sensors, Design Binder, Annotations,
Surface Bodies, Solid Bodies, Lights and Cameras, Markups, Equations,
Material <not specified>, Front Plane, Top Plane, Right Plane, Origin, Sketch1, Boss-Extrude1
```

`Lights and Cameras`, `Annotations`, `Equations` and `Material` are the tree nodes this stream owns,
so the tree is direct evidence the emitted records were read and accepted rather than skipped.

**Rung 6 is the claim that matters against `.kiro/steering/no-donor-blocks.md`.** The part name is
changed, so the emitted sequence is 25216 bytes and equals **no `Contents/Config-0` in the 219-file
corpus**, and it still opens with the host's own correct volume and centre of mass.

### 6.1 Rung 4 — the refusal that proves the atom region load-bearing

A same-generation `Config-0` from a **3-feature** document dropped into a **1-feature** host kills
SOLIDWORKS inside `OpenDoc6`, with no dialog:

```
opened=False
com_error(-2147417851, 'The server threw an exception.', None, None)
attempts=4  history=['solidworks-crashed-on-open'] × 4
34 s, against 12-14 s for every successful measurement
```

Identical on all four retry attempts with healthy controls either side, so this is deterministic
rejection and not session flakiness. The code differs from the `-2147023170`
(`'The remote procedure call failed'`) that `DEFINITION.md` §4.2 records for its cross-generation
refusals; both are the same failure class — the process dies inside `OpenDoc6` — reported through a
different COM path.

Rung 3 shows a same-generation, same-feature-count donor opens fine, so the refusal isolates to the
feature-dependent content, which is exactly the atom region of §3. **This is the measurement that
proves the 88-byte-per-feature block is load-bearing rather than cosmetic**, and it is why
`encode_config0_stream` rejects a foreign `generation` outright.

Not measured, and therefore not claimed: emission at feature counts above 1 was verified for size
only. A multi-feature host needs its `Config-0-ResolvedFeatures`, `CMgr` and `ModelHeader` to agree.

## 7. Historical byte accounting, before and after (superseded)

The region decode moved the split as follows, both measured with
`declared_opaque_split()` asserting `accounted == stream_bytes`:

| category           | before         | after              |
| ------------------ | -------------- | ------------------ |
| derived framing    | 1045           | 1045               |
| declared fields    | 8267 (32.8 %)  | **19051 (75.6 %)** |
| named opaque spans | 15902 (63.1 %) | **5118 (20.3 %)**  |
| **total emitted**  | **25214**      | **25214**          |

Inside the region alone, declared went from 8267 to **17402 of 17440 node-body bytes**, and the
region's named opaque went from 15902 to 38. The 17 unit records of §7.1 contributed a further 1077.

Two accounting corrections came with the port. The old `declared_opaque_split` mapped plan positions
by `id(body)`, and because `build_nodes` substitutes a fresh object for node 115 the
`HIGH_WATER_POSITION` branch never fired, crediting all 299 bytes of the `moCThreadRefMgr_c` frame as
declared. Only the 8-byte high-water pair is declared; the other 291 are the per-solid-body doubles.
The new walk iterates plan positions directly, so those 291 bytes are now counted as opaque. Reading
the after-figure against the before-figure therefore understates the improvement by 291 bytes.

### 7.1 The 17 unit records

Nodes 3–20 are the document's unit tables, and every one of them opens with the **62-byte
`moUserUnits_c` field block** from `moUserUnits_c::Serialize` `0x3cbc8e80`
(`long long double long long double long long int int double ushort int`). Running that program
against each body lands exactly:

| node                         | class                                                                                                                                                                                         | body | `moUserUnits_c` | remainder |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | --------------- | --------- |
| 3, 4                         | `moLengthUserUnits_c`                                                                                                                                                                         | 64   | 62              | 2         |
| 6                            | `moAngleUserUnits_c`                                                                                                                                                                          | 64   | 62              | 2         |
| 8                            | `moDensityUnits_c`                                                                                                                                                                            | 73   | 62              | 11        |
| 11                           | `moUnitSysUnits_c`                                                                                                                                                                            | 64   | 62              | 2         |
| 12                           | `moForceUnits_c`                                                                                                                                                                              | 64   | 62              | 2         |
| 17, 18, 19                   | `moPowerUnits_c`, `moEnergyUnits_c`, `moTimeUnits_c`                                                                                                                                          | 64   | 62              | 2         |
| 7, 9, 10, 13, 14, 15, 16, 20 | `moNumberUserUnits_c`, `moFloatNumberUserUnits_c`, `moSpringConstantUnits_c`, `moStressUnits_c`, `moGravityUnits_c`, `moLinearMotorUnits_c`, `moRotaryMotorUnits_c`, `moFrequencyUserUnits_c` | 62   | 62              | 0         |

The remainders are accounted for by the derived serializers:

- `moLengthUserUnits_c::Serialize` `0x3cbc8cb0` and `moAngleUserUnits_c::Serialize` `0x3cbc89e0` add
  one `ushort`. `moLengthUserUnits_c` also ends with a tagged object write, which is the node tag of
  the following node and therefore not part of this body — that write is the source of the 22 region
  tags in §5.4.
- `moEnergyUnits_c::Serialize` `0x3cbc8c30` adds one `ushort`. Its export block shows the address is
  **shared by five classes** through identical-code folding —
  `moEnergyUnits_c`, `moPowerUnits_c`, `moSpecificHeatUnits_c`, `moThermalConductivityUnits_c` and
  `moTimeUnits_c` — which is how nodes 17, 18 and 19 are covered by one recovered function.
- `moDensityUnits_c::Serialize` `0x3cbc8a40` adds `ushort +0xc0`, `ushort +0xc4`, a `uchar` presence
  flag, an optional tagged object when that flag is set, `ushort +0xc8` and `int +0xcc`. With the flag
  at zero that is 2 + 2 + 1 + 2 + 4 = **11**, exactly the measured remainder.

The eight 62-byte bodies land on the body end with nothing left, so those derived classes serialize no
fields of their own. Nodes 11 and 12 keep a **2-byte named residual each**
(`RESIDUAL_MOUNITSYSUNITS_C_N011_TAIL`, `RESIDUAL_MOFORCEUNITS_C_N012_TAIL`) because
`moUnitSysUnits_c::Serialize` and `moForceUnits_c::Serialize` have no primary symbol in the sldmfcu
program — folded like `moEnergyUnits_c`, but onto an address Ghidra names after another class — so the
`ushort` is measured but not read off its own function.

That is 1077 declared bytes against 4 residual, and `declared_unit_bytes()` reports exactly that.

### 7.2 What remained at this checkpoint

The remaining 5118 bytes were **67 named spans**, then listed in `config0.py` as `RESIDUAL_SPANS` with
`RESIDUAL_BYTES` asserted equal to the split's opaque figure. Every one is named for its owning
class. The largest:

| span                                  | bytes      | owner                   |
| ------------------------------------- | ---------- | ----------------------- |
| `MOVISUALPROPERTIES_N001_BODY`        | 621        | `moVisualProperties_c`  |
| `MOCTHREADREFMGR_N115_BODY`           | 291        | `moCThreadRefMgr_c`     |
| `MOTRANSREFPLANEDATA_N024_BODY`       | 249        | `moTransRefPlaneData_c` |
| `MOVIEW_N086..N095_BODY`              | 122–203 ea | `moView_c`              |
| `MOANNOTATIONVIEW_N105_BODY`          | 198        | `moAnnotationView_c`    |
| `MONODENAME_N066/N071/N076/N081_BODY` | 142–227 ea | light frames            |
| `RESIDUAL_MORELMGR_C_HEAD`            | 36         | `moRelMgr_c`            |
| `RESIDUAL_MODETAILDEFS_C_TAIL`        | 2          | `moDetailDefs_c`        |

`moVisualProperties_c`, `moFeatColorTab_c`, `suObList`, `gcXhatch_c` and `gcCurvatureObject_c` have
**no entry in `serialize_map.json` at all**. That is what bounds the remaining spans, and it is the
next thing to attack: `moView_c` `0x4c288eb0`, `moTransRefPlaneData_c` `0x4c732bc0`,
`moAnnotationView_c` `0x4c274100` and `moCThreadRefMgr_c` `0x4b38b750` are all in sldmodu and all
decompilable today, and together they are about **2500 of the 5118**.

Stated plainly against `.kiro/steering/no-donor-blocks.md`: 20.3 % of the stream in 67 named spans is
still above `definition.py`'s 8.2 %, so this is visible debt, not a finished stream. What has changed
is that the debt is down from 15902 bytes to 5118, no span is unexplained, and the four largest
classes remaining have addresses against them.

## 8. Historical transitional emitter (superseded)

`src/convert/adapters/solidworks/config0.py`, following `definition.py`: declarative tables as module
literals, `MO_VERSION = 18000`, one public `encode_config0_stream(...)`, a `declared_opaque_split()`
the test suite asserts on, and named residual spans named for their owning class.

The `moDetailDefs_c` tree is carried as `MODETAILDEFS_C_FIELDS`, one row per decoded field, each row
carrying an index into `DETAIL_OWNERS` — the object path that names the class the field belongs to.
`encode_detail_region()` rebuilds the 17484-byte region from those fields plus the two named
residuals, and `detail_region_bodies()` re-cuts it into the 23 node bodies of nodes 36–58 using
`DETAIL_REGION_PLAN`.

The unit records are carried the same way as `UNIT_NODE_RECORDS`, one entry per node, each with its
program class, its declared fields against `UNIT_OWNERS`, and its named tail. `UNIT_RECORD_SERIALIZE`
lists the five recovered serializer addresses the fields came from.

Default output is deterministic:

```
25214 bytes  sha256 a0877db37735da4027459d8161425843e3ad90f1e3e90dc32835f9370dd643bb
```

The caller must supply the feature atom list `((atom_id, feature_tree_id), …)` newest-first, and
those tree ids must be the **same ids** written into `Contents/CMgr` and `Config-0-ModelHeader`. That
is the one real coupling between this stream and the rest of the writer.

`encode_config0_stream` raises `SldprtFormatError` on an empty atom list and on any `generation` other
than 18000, because the tables are 18000-only and rung 4 makes cross-generation substitution a
measured crash rather than a risk. **The tables must be re-recorded if Kit ever targets another
generation.**

`tests/convert/test_solidworks_config0.py` pins the reference digest and length, the 88-byte
per-feature step over 1–8 features, the 25148-byte `single_length_unit` variant, the atom region as
the only feature-dependent content, the region reconstruction and its node tiling, the 17 unit records
and the 62-byte `moUserUnits_c` block inside each, that every declared field names its owning class,
that every opaque byte sits in a named span summing to the split's opaque figure, and the
declared-versus-opaque accounting with `opaque <= 5118` so the debt can only shrink.

## 9. Dimensioned circle specialization

The 12,514-byte diameter-driven circle resolved program requires the 25,158-byte single-length-unit
configuration shape already closed by `config0_box_program.py`. Its controlled `r5 h10` stream
differs from that typed baseline in 30 fields, one of which is only the five-character part name.
Production preserves `Part1` and specializes the remaining 29 typed fields rather than retaining a
recorded byte range.

The geometry-dependent fields are radius in millimetres plus centre, extrema, depth, and bounding
sphere radius in metres. The other fields carry the recovered diameter-profile flags, object 33
feature identities, field-program generation values, and the session records coupled to this
resolved program. Every override is encoded by the existing primitive writer at its traced field
offset; no raw block or vendor file is packaged.

Oracle minimization established two distinct gates:

1. generic `Config-0` plus the dimensioned-circle resolved stream kills SOLIDWORKS during
   `OpenDoc6`;
2. geometry-only overrides load and permit diameter edits, but the boss history collapses when its
   depth changes; and
3. all 29 typed circle overrides load without warnings and permit independent diameter and depth
   rebuilds with one body and exact measured mass properties.

The raw reverse-direction oracle has a 25,190-byte configuration stream, but its apparent 32-byte
growth is only the saved document-name string. Canonicalizing that metadata restores the same
25,158-byte configuration width as the normal-direction specialization. The reverse program owns
all 4,345 typed operations and specializes the recovered negative-depth bounds, feature state,
cache identities, and direction semantics. Its paired canonical resolved program is 12,514 bytes;
neither program contains a saved path, filename, opaque span, or donor block.

The canonical reverse pair opens and rebuilds without warnings. Driving the sketch diameter from
10 mm to 16 mm and the boss depth from 10 mm to 12 mm independently rebuilt one negative-Z body at
the exact measured volumes recorded in `CIRCLE_REVERSE.md`. Reversed origin-centred Front-plane
circular blind bosses are therefore inside the strict production gate; off-origin and non-front
variants still fail closed.

This is why the session-valued fields remain explicit typed semantics even though some do not vary
with source radius or depth. Removing them is a measured parametric failure, not a harmless
normalization.
