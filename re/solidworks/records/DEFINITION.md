<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# `Contents/Definition` — field map, and an emitted one that opens

Status: **confirmed**. A constructively emitted `Contents/Definition` was measured opening in
SOLIDWORKS 2025 with the correct volume and centre of mass, in two different host documents.

The stream is document-level. It carries **no geometry, no feature, no sketch and no configuration
data**. It is a scalar preamble followed by a seven-class `su_CArchive` object graph holding the
drafting standard, the line-style table, the annotation-to-line-font bindings, the user model
environment, the BOM manager and the design-journal record. Kit emits it from
`src/convert/adapters/solidworks/container/Definition.py`.

`../measurements/Measure.md` classes this stream load-critical: deleting it from a vendor file
crashes SOLIDWORKS on open. Before this work it was the only load-critical stream with no recorded
grammar at all.

## 1. Corpus

673 CAD files under `examples/`, `.rescratch/**`, `files/` and `tests/fixtures/solidworks/` carry
the stream: **194 distinct payloads across 21 sizes**.

Size is a function of exactly five things, none of them geometric:

1. the drafting-standard class name — `moBS_c` (74 payloads), `moISO_c` (116), `moANSI_c` (3);
2. the author's Windows user name in `uiUserModelEnv_c`, two bytes per UTF-16 code unit;
3. one byte gating a 72-byte view block in the preamble;
4. two optional classes, `mfcutZebraData_c` (10 payloads) and `CRectNonOleItems_c` (2);
5. the design-journal record, which grows in the three vendor outliers carrying embedded-item lists.

Within the 24-payload group authored on one install by one user, **97.9 % of the bytes are
byte-constant** (76 varying bytes in 13 runs). The 36–70 % variation seen across other same-size
groups is **permutation, not information**: the annotation bindings are written in hash-map
iteration order, so two documents with identical settings emit an identical multiset of records in a
different sequence. Measured: 1 distinct string multiset per group, 2 to 5 distinct orders.

What the varying regions correlate with:

| region                        | correlates with                                                            |
| ----------------------------- | -------------------------------------------------------------------------- |
| `u32 flags` @0                | a document flag word; 80, 101, 160, 166, 59 observed                       |
| `u32 generation` @4           | 5, 6 or 7 — not the `_MO_VERSION_` number                                  |
| CLSID @20                     | document type: `83A33D30-…` part (184 payloads), `83A33D36-…` assembly (9) |
| `u8 view_count` @39           | 0 → 120-byte preamble (26 payloads); 1 → 192-byte preamble (167). 193/193  |
| view and tail doubles         | the saved model view orientation and zoom                                  |
| `uiLFConfig_c` order          | hash-map iteration order; the set is invariant                             |
| `uiUserModelEnv_c`            | the author's Windows user name, plus the saved camera                      |
| `moLineStyle_c` display names | the UI language of the authoring install                                   |
| `uoJournal_c`                 | the design-journal attachment and embedded-item list                       |

**Nothing in the stream correlates with feature count, sketch count, body count or geometry.** That
is what makes it emittable.

## 2. The preamble

The stream does **not** begin with an MFC tag, which is why `Archive.py`'s `segment()` and
`resolve_base()` cannot walk it and why **there is no base value for this stream**. Every base 1–19
against every header size 100–130 fails; with the shipped 6-byte header the walk dies at byte 8
reading `u32@8` as a tag. None of the stream's seven classes appear in `re/data/Layouts/ClassLayouts.json`.

The first class-definition tag sits at byte 120 or 192. Everything before it:

| offset | width | type    | name           | notes                                             |
| ------ | ----- | ------- | -------------- | ------------------------------------------------- |
| 0      | 4     | u32     | `flags`        |                                                   |
| 4      | 4     | u32     | `generation`   | 5 / 6 / 7                                         |
| 8      | 4     | u32     | `field8`       | 50 in 190 of 193                                  |
| 12     | 4     | u32     | `field12`      | 1 or 0                                            |
| 16     | 4     | u32     | `field16`      | 1 in all 193                                      |
| 20     | 16    | GUID    | document CLSID | part or assembly                                  |
| 36     | 3     | bytes   | reserved       | `00 00 00` in all 193                             |
| 39     | 1     | u8      | `view_count`   | 0 or 1                                            |
| 40     | 72    | 9 × f64 | view basis     | present only when `view_count == 1`               |
| …      | 24    | bytes   | `middle24`     | all zero in 87 of 193, otherwise three f64        |
| …      | 8     | f64     | `scale`        | 1.0 in all 193                                    |
| …      | 2     | u16     | pad            | 0 in all 193                                      |
| …      | 32    | 4 × f64 | tail           | the saved camera                                  |
| …      | 14    | bytes   | `trailer14`    | 15 distinct values; carried as a recorded literal |

Acceptance: parsing that map and re-emitting reproduces **193 of 193 payloads byte-identically**,
and it lands exactly on the first class tag in all 193 with no slack byte and no search. Landing
exactly is what makes this a decode rather than a fit.

## 3. The body

Seven classes in read order. Spans measured on `boss1_front_rect_blind`, body 3618 bytes.

| body offset | span | class                                   | schema |
| ----------- | ---- | --------------------------------------- | ------ |
| 0           | 16   | `moBS_c` / `moISO_c` / `moANSI_c`       | 1      |
| 16          | 496  | `moLineStyle_c` × 7                     | 1      |
| 512         | 2345 | `uiLineFontMgr_c` + `uiLFConfig_c` × 40 | 1      |
| 2857        | 447  | `uiUserModelEnv_c`                      | 1      |
| 3304        | 38   | `moBomInfoMgr_c`                        | 1      |
| 3342        | 276  | `uoJournal_c`                           | **0**  |

The archive framing is computed, not recorded. A `u16` token of `0xFFFF` introduces a class
definition (`u16 schema`, `u16 name length`, ASCII name); `0x8000 | index` introduces a new object
of the class already at `index` in the load array. Indices start at 1 and both classes and objects
consume one. That model predicts every back-reference in the stream exactly — `0x8003` before line
styles 2–7 and `0x800d` before bindings 2–40 — so all **52 object tokens** are derived.

### 3.1 Field orders recovered from the decompiler

`moLineStyle_c::Serialize` @ `0x3cab9220` (sldmfcu, imagebase `0x3c9f0000`):

1. `su_CObject::Serialize` — zero bytes
2. `CString` — the style key, e.g. `CONTINUOUS`
3. `CString` — the display name, e.g. `Solid`
4. `u16` — dash-segment count
5. `count ×` `f64` — segment lengths, positive for dashes and negative for gaps
6. `u8` — a flag

`uiLFConfig_c::Serialize` @ `0x3ca67450`:

1. `su_CObject::Serialize`
2. `CString` — the line-font key this annotation type binds to
3. `utLineWidth_c::Serialize` @ `0x3cb08110` — for file version `>= 0xf41`: `i16` line-weight enum
   then `f32` custom width, `-1.0` meaning none
4. file version `>= 0xc9f` → `i16`, else the field is forced to 0

The drafting-standard base `0x4c6e19a0` → `0x4c6e19c0` and `moBomInfoMgr_c::Serialize`
@ `0x4bdf2790` are in sldmodu (imagebase `0x4b1e0000`). `uiLineFontMgr_c`, `uiUserModelEnv_c` and
`uoJournal_c` live in `slduiu.dll`, which has no Ghidra project, so their field orders were not
recovered.

The storage-open site does not exist as a string reference. `Definition` appears once as a UTF-16
literal in sldmodu at VA `0x4ce9987c`, and `DumpRefs` reports **0 functions** referencing it. The
sldmfcu occurrence sits inside a table of stream names alongside `eModelLic`, `Config-0-LWDATA`,
`Config-0-Partition`, `Config-0-ResolvedFeatures`, `CMgr`, `Header2` and the rest, so storages are
opened by table index. This is the same table-indexed pattern as the container signature table in
`Answers.md` Q7.

### 3.2 The settings tables

The line styles are a dash-pattern table:

| key           | display          | segments                                | flag |
| ------------- | ---------------- | --------------------------------------- | ---- |
| `CONTINUOUS`  | Solid            | `12.0`                                  | 0    |
| `HIDDEN`      | Dashed           | `0.25, -0.125`                          | 0    |
| `PHANTOM`     | Phantom          | `1.25, -0.25, 0.25, -0.25, 0.25, -0.25` | 0    |
| `CHAIN`       | Chain            | `1.25, -0.25, 0.25, -0.25`              | 0    |
| `CENTER`      | Center           | `3.0, -0.25, 0.25, -0.25`               | 0    |
| `STITCH`      | Stitch           | `0.0, -0.125`                           | 0    |
| `CHAIN_THICK` | Thin/Thick Chain | `1.25, -0.25, 0.25, -0.25`              | 1    |

`uiLineFontMgr_c` writes `u16 count = 40`, then 40 `(CString annotation key, uiLFConfig_c object)`
pairs, then `u16 1`. The bindings are settings: `Visible` takes line weight 1, `Section`,
`ViewArrow` and `EmphasizedOutline` take 2, every other annotation takes the default 0;
`Centerlines` binds to `CENTER`, `TanVisible` and `Explodelines` to `PHANTOM`, `CosmeticThread` to
`DUMMYTHREAD` (a font key with no `moLineStyle_c` record of its own), and no annotation overrides
the custom width. The full ordered list is in `Definition.py`.

Note for anyone reading the first draft of this work: there are **40** bindings, not 48, and
`Sketch` is the first map key binding to `CONTINUOUS`, not a separate "active configuration name"
field. Reading it as a name field is what makes the table look like 48 values with 39 keys.

### 3.3 Byte accounting

**All 3618 body bytes are emitted from declared fields; zero bytes remain opaque.** The parser
asserts that the cursor finishes at exactly 3618 and that re-emission is byte-identical, making this
complete typed ownership rather than an estimate.

| span               | offset | length | owner              |
| ------------------ | ------ | ------ | ------------------ |
| `session_header`   | 2891   | 16     | `uiUserModelEnv_c` |
| `window_placement` | 3063   | 24     | `uiUserModelEnv_c` |
| `environment_tail` | 3255   | 49     | `uiUserModelEnv_c` |
| `manager_tail`     | 3328   | 14     | `moBomInfoMgr_c`   |
| `record_head`      | 3399   | 47     | `uoJournal_c`      |
| `record_tail`      | 3464   | 146    | `uoJournal_c`      |

These six ranges were the last residuals. They are now emitted as primitive fields: eight `u16`
session words; two `u32` window coordinates, six `u16` placement fields and one `i32` sentinel;
reserved-zero environment ranges, one capacity, two sentinels, a build stamp and trailing flag; an
empty-BOM schema/build tail; and sparse typed journal option tables with explicit reserved gaps.
No raw range or vendor byte block remains in `Definition.py`.

## 4. The oracle

SOLIDWORKS 2025, `KIT_SOLIDWORKS_ORACLE=1`, one fresh process per candidate, dialog dismisser
running, control before and after every batch. Four batches, **every one `control healthy: True`**
with the control at 8000.000000000001 mm³ and CoM `[0, 0, 5]` on both sides. Candidates were built
with `build_sldprt(streams, file_id=archive.file_id, signatures=container_signatures(blob))` and
only `Contents/Definition` replaced.

Host `TWOFEATURES_pad_pad` (`_MO_VERSION_18000`) = 8500.0 mm³, CoM `[0, 0, 5.441176470588235]`.

| candidate                                             | bytes    | result      | volume mm³            |
| ----------------------------------------------------- | -------- | ----------- | --------------------- |
| rebuilt with the original                             | 3666     | opened      | 8500.0                |
| parse/emit round-trip of the original                 | 3666     | opened      | 8500.0                |
| **constructed, `moBS_c`, user `Kit`**                 | **3736** | **opened**  | **8500.0**            |
| constructed, `moISO_c`, identity view                 | 3821     | opened      | 8500.0                |
| constructed, `moANSI_c`, 27-char user                 | 3860     | opened      | 8500.0                |
| **same constructed stream, host `BASELINE_40x20x10`** | **3736** | **opened**  | **8000.000000000001** |
| whole `Definition` of two other 18000 parts           | 3666 / — | opened      | 8500.0                |
| `Definition` of `BIELA` (`_MO_VERSION_14000`)         | 3883     | **refused** | —                     |
| `Definition` of `Alternator` (`_MO_VERSION_13000`)    | 3721     | **refused** | —                     |

The second-host result is the generality proof: the same constructed stream opens in a different
document and yields that document's own correct volume and centre of mass, so the stream carries
nothing document-specific that the host needs.

### 4.1 The generation rule

Bisecting the cross-version refusal:

| candidate                                                           | result      |
| ------------------------------------------------------------------- | ----------- |
| own preamble + foreign body                                         | **refused** |
| foreign preamble + own body                                         | opened      |
| own, with the foreign `flags`                                       | opened      |
| own, with the foreign `trailer14`                                   | opened      |
| own, with the foreign `middle24`, view block and tail doubles       | opened      |
| foreign body with `moISO_c` renamed to `moBS_c`                     | **refused** |
| own body with only its **last 40 bytes** taken from the foreign one | **refused** |

**The whole preamble is freely substitutable**; the refusal lives entirely in the archive body. The
last-40-bytes result is the sharpest: the trailing scalar block of `uoJournal_c` is
generation-sensitive and cannot be freely set, which is why its typed option values are pinned to
the generation-18000 grammar.

The mechanism is visible in the decompiler. The reads in `0x4c6e19c0` and `utLineWidth_c::Serialize`
are gated on a file version taken from `moArchiveHelper_c + 0x780`, falling back to
`moVersionManager_c::getCurrentFileVerion()` — **the archive's version, which comes from the
document, not from the stream**. A body serialised at one generation and read back under another
generation's gates is parsed with the wrong field widths and the read runs off the end.

Kit authors `_MO_VERSION_18000` and the recorded tables came from an 18000 part, so this is
satisfied by construction. `Definition.py` states it as `DOCUMENT_GENERATION = 18000`. **The tables
must be re-recorded if Kit ever targets another generation.**

One confound, stated plainly: both refusing donors are also Spanish-locale vendor files, so UI
language is perfectly correlated with generation in this corpus and the two are not separated by
these measurements. Generation is the better-supported explanation because the mechanism above
exhibits it and because a localisation-independent variable (`moISO_c`, the standard the Spanish
files use) opens fine. Separating them needs a Spanish-locale 18000 part, which the corpus does not
contain.

### 4.2 Failure mode

Refusals show **no dialog**. SOLIDWORKS dies inside `OpenDoc6` and the COM channel breaks:

```
com_error(-2147023170, 'The remote procedure call failed.', None, None)
```

Every refusal produced that identical record on all four retry attempts, in 12–13 s against 15–18 s
for a successful measurement, with the controls either side opening normally. That is deterministic
rejection, not session flakiness.

## 5. How Kit emits it

`src/convert/adapters/solidworks/container/Definition.py`. The preamble is built from named fields with
`view_count = 0` and a zeroed camera, which is honest for a freshly written document and is the
branch measured opening. The body is written from the declared tables with two parameterised holes,
the drafting-standard class name and the user name. Default output is deterministic:

```
3736 bytes  sha256 7479a6640fa3647a4801f41bc2bd1cc4a08c845620fc0a4412dd2aa407aadf19
```

Do **not** copy a donor's `Definition` and do **not** substitute one from an arbitrary corpus file —
that is measured as a crash whenever the donor's generation differs from the host's.

`tests/convert/solidworks/configuration/SolidworksDefinitionTests.py` pins the byte-identity of the body against the
recorded digest, the default stream digest, all three drafting standards, four user-name lengths,
the assembly CLSID, the view block, complete typed-byte accounting, and the absence of encoded
vendor blocks.
