<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Direct answers to the seven open questions

Confidence words are used exactly as in `Serialize.md`: **confirmed** = decompiled _and_
cross-checked against real bytes; **partial** = decompiled but not exercised by any available file;
**not found** = not recovered.

---

## Q1 — `moExtrusion_c` / `moICE_c` body layout: where is the boss-vs-cut selector?

**Answer: there is no operation field inside `moExtrusion_c`, `moICE_c` or `moEndSpec_c`. The
selector in this stream is the 32-bit tree-flags word after the feature's tree-node name — the
value the earlier work already found and dismissed. Status: confirmed (negative result) for the
three classes; the flags word is confirmed as the only operation-typed value in the record.**

Three independent lines of evidence.

1. `moExtrusion_c::Serialize` (`0x4bb8eba0`, self-identified by its
   `suCrash_c::Point("moExtrusion_c::Serialize")` guard) contains, after the base call, exactly
   three reads: `ReadObject(moEndSpec_c)` → `+0x7b0`, `AR_get_double` → `+0x7d0`, `AR_get_long`
   → `+0x7a8`. Nothing else. `moICE_c` does not override it — slot 5 of both classes' vftables is
   the same address — so `moICE_c` cannot carry an operation field that `moExtrusion_c` lacks
   either.
2. `moEndSpec_c` is **byte-identical** between a boss and a cut. `Classdiff.py padplane cutbase`
   reports **zero** class-count differences between `PADPLANE_rev_d5` (boss + boss) and
   `CUTBASE_cd5` (boss + cut), and `Bytediff.py moEndSpec_c padplane cutbase` reports zero byte
   differences for both the definition and the class-reference instance. A boss and a cut produce
   the same class set and the same end-spec bytes.
3. Scanning both streams for the tree-flags constants:

   ```
   PADPLANE_rev_d5   0x40000140 at 8329 and 13586;  0x400201ca absent
   CUTBASE_cd5       0x40000140 at 8329;            0x400201ca at 13584
   ```

   The second feature's flags word is `0x40000140` for the boss and `0x400201CA` for the cut, and
   it is the only place the two differ structurally. `13586` versus `13584` is the two-byte shift
   from `"Boss-Extrude2"` being one character longer than `"Cut-Extrude1"`.

Why flipping it alone still fails, which the measured evidence in `Grammar.md` §4 reports: the
boss/cut pair also differs inside the same `moICE_c` object in the surface-identity records that
follow — `moEndFaceSurfIdRep_c`, `moFromSktEntSurfIdRep_c`, `moEndFace3IntSurfIdRep_c` and the
`moFR_c` id words (`Bytediff.py` lists ~40 changed bytes in the 873-byte run, all of them
face/edge id hashes and small indices). Those describe the faces the operation created. Flipping
the flag without regenerating them leaves the record self-inconsistent, which is consistent with
the observed crash. So the honest position is unchanged from `Grammar.md`: **boss ↔ cut must come
from a donor of the right operation**, and the reason is now known — it is not a hidden opcode, it
is the derived face-identity records.

The remaining unrecovered piece is _which base-class `Serialize` writes the flags word_.
`moExtrusion_c::Serialize` → `moBodyFeature_c::Serialize` → `FUN_4bb886c0` (unnamed base), and the
flags live in that unnamed base chain (`moModelFeature_c` / `moFeature_c` / `moNode_c`). Recovering
it is mechanical with the tooling here but was not completed. **partial.**

---

## Q2 — Merge result

**Answer: `moEndSpec_c + 0x128`, `i32`, accessor `moEndSpec_c::getMerge()` / `setMerge()`.
Status: confirmed as the field. But it is already `1` in every corpus part, so it is not the cause
of the reported separate body.**

The offset comes from decompiling the export `?getMerge@moEndSpec_c@@QEAAHXZ` at
`0x4b3233a0`, which is `return *(int *)(this + 0x128);`. (Ghidra names that address
`moDimPoint_c::getAttachAlignH` because the linker folded the two identical one-instruction
getters; the address is the one from `sldmodu.dll`'s export table, resolved by `Exports.py`.)

In the field order that is item 31 of §1 in `Serialize.md`: it is the first of three `i32`s in the
32-byte scalar run that sits between the two draft-angle dimension reads and the
`moFromEndSpec_c` read, i.e. run offset +20. Read back by `VerifyLayout.py`, it is **1 in all 13
`moEndSpec_c` objects of all 9 traced parts**, including the two V8 production parts.

So a written file that produces a separate body is _not_ doing so because merge is 0 — merge is
already 1 in every donor. The 32000 mm³ / 2-body result must come from elsewhere. The two
candidates the segmentation actually exposes are the `moPerBodyChooserData_c` object inside the
extrusion (a real traced child, `moEndSpec_c`'s sibling under `moExtrusion_c`) and the
`moCompSolidBody_c` / body-list objects that `PADPLANE_rev_d5` has and `TWOPAD_d5` does not. That
was not investigated further. **Cause of the 2-body result: not found.**

Its neighbour `moEndSpec_c + 0x12c` is `getNormalCut()` (sheet-metal normal cut), value 0
throughout, and the reader clamps it: `if ((uint)this->0x12c > 1) this->0x12c = 0;`.

---

## Q3 — `moRevEndSpec_c`: end-condition code, direction flag, second angle, thin thickness

**Answer: the 52 bytes decompose completely. Status: confirmed for the structure and for the
end-condition/direction offsets; the "second angle" and "thin thickness" are not in this record
at all.**

Full table in `Serialize.md` §3. The four things asked for:

- **End-condition code**: `+0x0c` for direction 0, `+0x10` for direction 1, both `i32`.
  `moRevEndSpec_c::getType(int i)` is _the same machine code_ as `moEndSpec_c::getType(int i)` —
  `return *(int *)(this + 4*i + 0xc)` — so the revolve and the extrude share the
  `swEndConditions_e` offset. In stream terms, for a class definition: `marker + 32` and
  `marker + 36`. Value 0 in all 37 corpus parts.
- **Direction / reverse flag**: there is **no** `getDirection()` on `moRevEndSpec_c`. What exists
  is `getOffsetReverse(i)` at `+0x140` / `+0x144` (`marker + 64` / `marker + 68`), and
  `getSingleEnd()` at `+0x08` (`marker + 20`), which the reader forces to 1 when
  `getType(0) == 6`. The extrude's separate `getDirection()`/`getFlip()` pair at `+0x8c`/`+0x88`
  has no counterpart here. So the "reverse a revolve" flag is **not found** as a distinct field in
  this record; a two-direction revolve is expressed by `getType(1) != 0` plus a second angle
  dimension, not by a flag.
- **Second angle**: not a scalar. `moRevEndSpec_c::getAngle(i)` reads the `moDisplayDim_c*` at
  `+0x18 + 8i` and returns `6.2831853071796` (2π) when it is null. Items 14 and 15 of the record
  are those two dimension object reads. A modern file stores the angle only in the dimension
  chain; the raw doubles at `+0x150`/`+0x158` (`getRevolveAngle(i)`) are read **only when the file
  version is below 4547** and are absent from every corpus file. This is the direct explanation
  for the 52-byte constant: a 360° single-direction revolve genuinely stores no angle.
- **Thin-feature thickness**: not in `moRevEndSpec_c`. The two `0.01` doubles at `+0x38`/`+0x40`
  (`marker + 48` / `marker + 56`) sit between the up-to-point references and `getOffsetReverse`,
  i.e. in the per-direction _offset_ group, and `moRevEndSpec_c::getSurfOffsetDist(i)` returns the
  literal `0.01` when its dimension at `+0x28 + 8i` is null — the same default. So they are the
  per-direction surface-offset distances, default 10 mm, **partial** (no file exercises a non-zero
  offset). Thin-feature revolves use a different class: `moRevolutionThin_c`, whose own
  `Serialize` is `0x4bb9b920` (dumped, not analysed). **Thin thickness: not found.**

The record was validated two ways: `Serialize.md` §3 shows the field widths sum to exactly the
52 bytes `Revolve.md` §4.1 measured, with the two `0.01` doubles landing exactly where observed,
and `ScanRevendspec.py` decodes 37 parts with a consistent result.

---

## Q4 — The `moEndSpec_c` `swEndConditions_e` handling

**Answer: recovered in full. Status: confirmed for the enum offset and width and for codes 0, 1, 6
and 9; the extra records for codes 3 and 7 are confirmed in the code but partial against data;
codes 4, 5 do not add records.**

The enum is `i32` at `+0x0c` (direction 0) and `+0x10` (direction 1) — `getType(i)`. The earlier
work located the same byte at `marker + 33` but could not determine the width; it is 4 bytes, and
there is a second copy for the second direction at `marker + 37`.

What each code changes in the record, straight from the branches:

| code   | name                    | extra record                                                                        | where                                                                    |
| ------ | ----------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 0      | Blind                   | none                                                                                | depth is in the `moDisplayDim_c` at `+0x18`                              |
| 1      | ThroughAll              | none                                                                                | no depth dimension is written                                            |
| 2      | ThroughNext             | none                                                                                |                                                                          |
| **3**  | **UpToVertex**          | **one extra `operator>>` reading a `moPointRef_w*`**, before the surface-array flag | `+0x68` for direction 0, `+0x70` for direction 1                         |
| 4      | UpToSurface             | none extra beyond the surface-ref array that every record has                       | the array at `+0x28`/`+0x48`, gated by the `uchar` flag that precedes it |
| 5      | OffsetFromSurface       | as 4                                                                                | the offset value lives in the dimension chain                            |
| 6      | MidPlane                | none, but the reader forces `getSingleEnd()` to 1                                   |                                                                          |
| **7**  | **UpToBody**            | **one extra `operator>>` reading a `moRefWrapper_c*`**, after the `+0x130` field    | `+0x78` for direction 0, `+0x80` for direction 1                         |
| 9      | ThroughAllBoth          | none; pairs with `getType(1) = 1`                                                   | observed                                                                 |
| 10, 11 | UpToSelection, UpToNext | no branch on these values                                                           |                                                                          |

So exactly **two** codes add records — 3 and 7 — and both add a single object read at a known
position. Codes 4 and 5 need no new record: the surface reference is carried by the
`uchar` + `suObArray` pair that is present unconditionally in every record (items 11–12 and 14–15
of `Serialize.md` §1), which is why `getISurfRef(i)` exists for every end spec.

There is also a legacy remap the reader applies for files below version 318, which a writer of
modern files never needs but which explains why old files renumber: `3→4, 4→5, 5→6`.

Cross-checked on data: `ScanEndspec.py` decodes the first `moEndSpec_c` of all **158** corpus and
example parts, all 158 consistently, and finds codes `0` (150 parts, 17 of them with
`getDirection() = 1`), `6` (6 parts) and **`9` with `getType(1) = 1`** (2 parts:
`Cam_roller.SLDPRT`, `Piston.SLDPRT`). `VerifyLayout.py` additionally decodes `1` (ThroughAll,
reversed) in `Piston Ring KF.SLDPRT` and `6` in `COJINETE INFERIOR.SLDPRT` while proving the whole
record tiles the traced spans. Codes 3, 4, 5, 7, 10 and 11 appear in **no** available file, so
their branches are code-only. **partial** for those.

---

## Q5 — The two opaque scratch doubles

**Answer: neither belongs to the class it was attributed to. Status: partial — the misattribution
is confirmed, the true owner of `moExtrusion_c + 114` is not.**

- `moFromEndSpec_c + 140`: **`moFromEndSpec_c` owns only 4 bytes** in this corpus. Its whole record
  is one `i32` type code, and every branch that would extend it requires that code to be 3, 4 or 5;
  it is 0 (sketch plane) in all 9 traced parts. Byte 140 past the marker is therefore inside
  another object entirely. The tail budget in `Serialize.md` §2 accounts for every byte after
  `moFromEndSpec_c` in all 9 traced parts — 4 for `moFromEndSpec_c`, 16 or 20 for `moEndSpec_c`,
  12 for `moExtrusion_c`, plus a 4-byte driver trailer when the extrusion is last — with nothing
  left over, so there is no unexplained double in that region at all. The `0.0` / `0.016` value the
  earlier work saw at that marker-relative offset is a field of whatever object follows.
- `moICE_c + 106/+108` and `moExtrusion_c + 114`: `moExtrusion_c::Serialize` owns exactly one
  double, at `this + 0x7d0`, and it is the **third-from-last** item in the whole record, not byte 114. In all 9 traced parts it reads `0.0`. Byte 114 past the `moExtrusion_c` marker is inside the
  base-class region (the traced 49/30/52-byte runs), produced by the unnamed base
  `FUN_4bb886c0` below `moBodyFeature_c::Serialize` — not recovered here.

A general observation from the tail that is worth recording because it explains several "scratch"
values. `VerifyLayout.py` now decodes the shared tail run of all 9 traced parts, and three
`moEndSpec_c` tail fields behave like uninitialised memory rather than parameters:

| field                                               | seven authored parts                                  | `Piston Ring KF`     | `COJINETE INFERIOR` |
| --------------------------------------------------- | ----------------------------------------------------- | -------------------- | ------------------- |
| `getCapEnd(0)` `+0x148`                             | `1348739666` in all seven                             | 0                    | 0                   |
| `getCapEnd(1)` `+0x14c`                             | 0                                                     | 0                    | 0                   |
| `getDelInitFace()` `+0x150`                         | `1168530297` in all seven                             | 0                    | 0                   |
| `getKnitRes()` `+0x154`                             | `52818912` / `53700368` / `52476704`, varies per file | 0                    | 0                   |
| `getCreateSolidFrmCappedMidPlaneSurfExt()` `+0x158` | 0                                                     | absent (old version) | absent              |
| `moExtrusion_c +0x7d0`                              | `0.0`                                                 | `0.0`                | `0.0`               |
| `moExtrusion_c +0x7a8`                              | `0xffffffff`                                          | `0xffffffff`         | `0xffffffff`        |

Fields SOLIDWORKS never initialises for a plain solid extrude serialise whatever the allocation
happened to contain — deterministic for one build and code path (hence identical across the seven
authored parts written by the same session) and different for another build (hence zero in the two
older V8 parts). This proves they are not parameters and must not be copied from a sample. The
current typed programs emit the recovered stable semantics for supported families; an unrecovered
variant is rejected.

---

## Q6 — Profile geometry classes and the sketch-coordinate role/class trailer

**Answer: partially superseded.** This pass recovered one structural fact. Later work in
`../features/ArcLayout.md` located line, circle, and partial-arc coordinate roles, and the supported
typed feature programs construct their exact sketch families. Polygon, slot, spline, and arbitrary
mixed-profile layouts remain unrecovered.

The one fact recovered: `sgArcHandle`, `sgLineHandle` and 18 other handle classes do **not** have
their own serialiser — slot 5 of every one of their vftables is `sgEntHandle::Serialize`
(`0x4c5c91a0`), whose first field the store branch names, via a `su_DBKey`, as **`EntIndex`**, and
which is an escaped integer: a `u16` if below `0x777f`, otherwise the sentinel `0x777f` followed by
a wider field. That escape is why the traced `sgLineHandle` spans are 12, 16 and 99 bytes rather
than one constant.

Not recovered: the polygon / slot / spline profile layouts, and the meaning of the observed
`role ∈ {0, 2, 6, 8, 14, 24, 29}` and `class ∈ {0, 1, 2, 3, 5}` trailer values. `sgSpline` has no
RTTI vftable in `sldmodu.dll` at all, so it is either in another module or spelled differently.
The classes that do have their own serialisers are indexed in `out/SerializeMap.json` with
addresses (`sgArc` `0x4c5c6b10`, `sgLine` `0x4c5cc540`, `sgSketch`, `sgDim`, `sgLogDim`, …). This
checkpoint had not yet run `DumpFunctions.java` against them; retain that fact as history, not as the
current status of the recovered line/circle/arc families.

---

## Q7 — The `file_id` → container signature-triplet function

**Answer: found, and it is not a function. It is a 1000-entry lookup table in `sldmfcu.dll`, and
the relation has been inverted completely. The donor-template requirement for the container
signatures is removed. Status: confirmed, 184 of 184 real files.**

### The algorithm

`sldmfcu.dll` holds two adjacent arrays in `.rdata`:

| array      | virtual address | file offset (SW 2025 `sldmfcu.dll`) | size        | element                       |
| ---------- | --------------- | ----------------------------------- | ----------- | ----------------------------- |
| ids        | `0x3cf5a440`    | `0x566c40`                          | 4000 bytes  | `u32` file id, **big-endian** |
| signatures | `0x3cf5b3e0`    | `0x567be0`                          | 12000 bytes | three `u32`, **big-endian**   |

Both have exactly **1000** entries and the arrays are parallel: entry `i` of the id array pairs
with entry `i` of the signature array. The initialiser `FUN_3cc4e200` (decompiled in
`out/SldmfcuSigtableRefs.txt`, the only function that references either array) walks them once and
builds a red-black-tree map keyed by the id:

```c
do {
  local_res10[0] = (((*pb1 * 0x100 + *pb2) * 0x100 + *pb3) * 0x100 + *pb4);   /* id, big-endian */
  local_58   = big_endian_u32(&DAT_3cf5b3e0 + 12*i + 0);
  iStack_54  = big_endian_u32(&DAT_3cf5b3e0 + 12*i + 4);
  iStack_50  = big_endian_u32(&DAT_3cf5b3e0 + 12*i + 8);
  uStack_4c  = (&DAT_3d11bc60)[i];      /* one byte  */
  local_48   = (&DAT_3d11c050)[i];      /* one byte  */
  uStack_44  = (&DAT_3d11c440)[i];      /* one byte  */
  ... insert into the map under key local_res10[0] ...
} while (i < 1000);
```

The loop bound `1000` is literal in the code. Three further parallel 1-byte arrays carry ASCII-ish
per-entry values (`0x3d11bc60`, `0x3d11c050`, `0x3d11c440`, 1000 bytes each) which are stored in
the same map node but are not the container signatures.

To write a file: pick any index `i`, write `ids[i]` big-endian as the 4-byte file id in the header,
and write `signatures[i][0..2]` as the local-record, central-directory and end-of-directory
signatures. To read: look the header's id up in the id array; its index gives the three signatures.

Byte-order convention, stated so it cannot be got wrong: the id array's four bytes go into the
header **in the order they appear in the DLL**; each signature's four bytes go into the file
**reversed** — the DLL stores the signature as a big-endian `u32` and the file field is that same
`u32` little-endian.

The table is byte-identical in three shipped modules — `sldmfcu.dll`, `slwstep30.dll` and
`sldsetdocprop.exe` — which is why the two hardcoded pairs in `Container.py` are entries **711**
(`0xEC6E2386`) and **750** (`0x715BE98F`).

### Why every mixer search failed

There is no arithmetic relation to find. The ids and signatures are 4000 unrelated random dwords
baked into the DLL. XOR keys, affine maps over GF(2), LCGs, CRC32, rotations and bit permutations
were all correctly ruled out because none of them exists.

### Closure — the table is irreducible, measured over all 1000 pairs

The search was rerun exhaustively over all 1000 `(id, triplet)` pairs rather than the 58 files of
the earlier study, and the negative is now definitive. This question is closed.

Over all 1000 pairs, a Gaussian elimination over GF(2) for a 32x32 bit matrix plus a 32-bit offset
finds **0 of 32 solvable output bits** for each of the three signatures, keyed on `file_id`, on the
`.rdata` array index, and on both together — and equally 0 of 32 in the inverse direction and
between any two signatures. The same solver recovers CRC-32, byteswap and `rotl ^ const` at 32 of
32 bits from the same 1000 inputs, so it is the absence of structure that is being measured, not a
limitation of the method. Since every CRC is affine over a fixed-length input, this one result
rules out every CRC polynomial, init and xorout, every XOR key, every rotation and every bit or
byte permutation at once. Independently, the lowest width at which "output mod 2^w is a function of
input mod 2^w" fails is **w = 1** for all six key/signature combinations, which eliminates every
polynomial of any degree over Z/2^32, every LCG chain and every multiplicative hash. And the table
does not compress: 16,000 bytes go to **16,011** with zlib -9 and **16,060** with lzma -9e, byte
chi-square 218.7 on 255 df with all 256 values present. A 16,000-byte incompressible blob with no
affine, polynomial, per-byte or per-bit structure is a table of random constants, which is exactly
what `FUN_3cc4e200` treats it as.

Exhausted and all **0 of 1000**: 1953 CRC variants; 930 unseeded hashes and mixers; murmur2,
murmur3, xxhash32, xxhash64, one-at-a-time, SipHash and lookup3 at **all 65536 seeds** across 9
input encodings; TEA, XTEA, Speck32/64 and RC5 at **all 65536 repeated-word keys**. Affine mod
2^32 reached a best of 2 of 1000 and LCG 2 of 999, which is noise. There is no signature
interdependence — all 1000 XOR and arithmetic differences are distinct — and no per-byte
substitution.

One positional artifact is real and is recorded here so the question does not reopen on it: within
32-element blocks of the `end` word there is a measurable index-correlated pattern, but it covers
**250 of 96,000 output bits, 0.26%**, while a container needs 96 bits per entry. It is measured,
quantified and useless. Entry 477's low byte is `0x75` where entry 989's is `0x74`, which is the
documented exception to it. Two single-bit correlations at 3.5–4.6 sigma were also chased and fail
split-half replication.

Reproduction: `.rescratch/para417_sigrel/` holds 23 scripts, one family per file, each writing a
`.out` log, plus `REPORT.md`.

### Verification

`Sigtable.py` extracts all 1000 pairs, then reads every `.SLDPRT` / `.SLDASM` under `examples/`,
`.rescratch/corpus/parts`, `.rescratch/corpus2`, `.rescratch/trace/parts` and `.rescratch/re/parts`
with the project's own `Container.py` (`SldprtArchive` plus `_template_fields`, so the signatures
are the ones the real parser extracts, not a guess) and compares:

```
distinct file_ids 1000 of 1000
parts=184 match=184 mismatch=0 unknown=0 unreadable=0
```

**184 of 184 real SOLIDWORKS files — every file id present in the table, every one of the three
signatures exactly the parallel entry.** The full extraction, with the host digest and the two
array offsets, is written to `re/data/Serialization/SignatureTable.json`.

### How the table is stored and regenerated

Because the relation is irreducible, the 16,000 bytes have to be carried as data. They are _not_
hand-written source. `re/tooling/ghidra/Generation/GenSignatureTable.py` reads the tracked vendor DLL
`re/binaries/sldmfcu.dll`, checks its SHA-256 against `re/binaries/Manifest.json`, extracts the two
parallel arrays at file offsets `0x566C40` and `0x567BE0`, and writes both the shipped resource
`src/convert/adapters/solidworks/data/sldprt_signature_table.bin` and the human-readable
provenance record `re/data/Serialization/SignatureTable.json`. `Container.py` loads that resource through
`importlib.resources`; it holds no signature bytes of its own.

`GenSignatureTable.py --check` re-extracts from the DLL and compares against the shipped resource
byte for byte. `tests/convert/solidworks/container/SolidworksSignatureTableTests.py` performs the same reproduction as
a test, so the resource cannot drift from the DLL it came from.

### What this changes

`build_sldprt(..., file_id=..., template=None)` used to raise
`"SLDPRT file id requires a native template with matching signatures"` for any id outside two
hardcoded pairs. It now serves all 1000 ids from the extracted table, and the donor template is no
longer needed _for the container framing_. It is still needed for stream content — nothing here
changes that.
