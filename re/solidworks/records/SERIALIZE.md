# Per-class field layouts of `Contents/Config-0-ResolvedFeatures`, recovered from the code

Source: Ghidra 12.1.2 headless decompilation of `swccu.dll`, `sldarchiveu.dll`, `sldmodu.dll` and
`sldmfcu.dll` from the licensed SOLIDWORKS 2025 install. No SOLIDWORKS process, no COM, no
debugger — the DLL bytes on disk only. `setup.md` has the exact commands.

Every table cites the function it came from. Confidence is one of:

* **confirmed** — read out of the decompiled `Serialize`, *and* the byte arithmetic reproduces a
  real traced object span or a real corpus record exactly.
* **partial** — read out of the decompiled `Serialize`, but the corpus does not exercise the field
  (its value is constant, or the branch is never taken), so nothing independent checks it.
* **unresolved** — not recovered.

---

## 0. How the archive frames objects, and how to read these tables

`su_CArchive::ReadObject` (`swccu.dll` @ `0x31eda570`) and `su_CArchive::ReadClass`
(`0x31eda2f0`) confirm the framing the earlier grammar work derived:

| token | meaning | bytes consumed by the framing |
|---|---|---|
| `ff ff` | class definition: `ff ff`, `u16 schema`, `u16 nameLen`, `nameLen` ASCII bytes | `6 + nameLen` |
| `0x8000 \| i` | class reference to map index `i` | 2 |
| `0x7fff` | escape: a `u32` class token follows | 6 |
| `0x0000` | null pointer — no object, no body | 2 |
| `t`, `0 < t < 0x8000` | reference to an already-mapped object | 2 |

`ReadObject` then calls the object's **vtable slot 5** (byte offset `0x28`), which is
`virtual void Serialize(su_CArchive&)`. Slot 2 is MFC's `Serialize(CArchive&)`; slot 5 is
SOLIDWORKS' own and is the one that reads the record. Every per-class layout below is the slot-5
function. Member sub-objects are serialised by the same `(**(code **)(*(longlong *)(this + off) +
0x28))(this + off, ar)` call, which is why that pattern appears in the tables as an inline
sub-record rather than as a nested `ReadObject`.

`RenameArchiveApi.java` renames each `su_CArchive::operator>>` overload to `AR_get_<type>` before
decompiling, so widths in the decompiled C are unambiguous:

| decompiled call | width | notes |
|---|---|---|
| `AR_get_uchar` / `AR_get_char` | 1 | |
| `AR_get_ushort` / `AR_get_short` | 2 | |
| `AR_get_long` / `AR_get_ulong` / `AR_get_int` / `AR_get_uint` / `AR_get_float` | 4 | |
| `AR_get_double` / `AR_get_int64` | 8 | little-endian |
| `su_CArchive::ReadObject` / `::operator>>(ar, T**)` | framing token + body | a traced child |

**Every read in every `mo*::Serialize` is gated on the document's file version**, fetched as
`*(uint *)(moArchiveHelper + 0x780)`, falling back to
`moVersionManager_c::getCurrentFileVerion()`. The gate constants are decimal-coded SOLIDWORKS
version numbers (`13103`, `14118`, `15110`, `16117`, `17115`, …). Every corpus file carries
`_MO_VERSION_18000/…` streams, i.e. a version above every gate constant found in these functions,
so **for the corpus all `if (CONST < version)` branches are taken and all legacy
`version < CONST` branches are not**. Two of the traced parts are older (see §2, tail budget) and
that is the one place where a gate actually changes the record length.

---

## 1. `moEndSpec_c` — CONFIRMED

Function: `sldmodu.dll` `0x4bb8d7d0` = `moEndSpec_c::Serialize` (vtable slot 5 of
`moEndSpec_c`'s vftable at `0x4cf62470`). Field names come from the exported accessors, each of
which was decompiled to bind a name to a `this` offset — see `out/sldmodu_accessors.c` and
`out/sldmodu_accessors3.c`.

`i` below is the direction index, 0 or 1; the accessors are `get*(int i)` and the members are
arrays of two.

| # | `this` offset | width | archive op | name (from accessor) | authored / cache | confidence |
|---|---|---|---|---|---|---|
| 1 | `0x138` | object | `operator>>` `moDirectionSpec_c*` | `getDirSpec()` | authored (null in corpus) | confirmed |
| 2 | `0x08` | 4 | `AR_get_long` | `getSingleEnd()` | authored | confirmed |
| 3 | `0x88` | 4 | `AR_get_long` | `getFlip()` | authored | confirmed |
| 4 | `0x8c` | 4 | `AR_get_long` | `getDirection()` — **the reverse flag** | authored | confirmed |
| 5 | `0x90` | object | `operator>>` | `getKeepPiece()` (`moFaceRef_c*`) | authored (null in corpus) | confirmed |
| 6 | `0x0c` | 4 | `AR_get_long` | `getType(0)` — **`swEndConditions_e`, direction 0** | authored | confirmed |
| 7 | `0x10` | 4 | `AR_get_long` | `getType(1)` — end condition, direction 1 | authored | confirmed |
| 8 | `0x18` | object | `operator>>` `moDisplayDim_c*` | depth dimension, direction 0 (`getDistance(0)` reads through it) | authored | confirmed |
| 9 | `0x20` | object | `operator>>` `moDisplayDim_c*` | depth dimension, direction 1 | authored | confirmed |
| 10 | `0x68` | object | **only if `getType(0) == 3`** | `getIPointRef(0)` — UpToVertex point | authored | partial |
| 11 | — | 1 | `AR_get_uchar` | surface-ref array present, direction 0 | authored | confirmed |
| 12 | `0x28` | sub-record | slot 5 of `suObArray` — only if #11 != 0 | surface refs, direction 0 (`getISurfRef(0)`) | authored | confirmed (2 bytes in corpus) |
| 13 | `0x70` | object | **only if `getType(1) == 3`** | `getIPointRef(1)` | authored | partial |
| 14 | — | 1 | `AR_get_uchar` | surface-ref array present, direction 1 | authored | confirmed |
| 15 | `0x48` | sub-record | slot 5 of `suObArray` — only if #14 != 0 | surface refs, direction 1 | authored | confirmed (2 bytes in corpus) |
| 16 | `0xa0` | 8 | `AR_get_double` | (no exported accessor) | unknown, `0.0` in corpus | partial |
| 17 | `0xb8` | 4 | `AR_get_long` | `getDraftCheck(0)` | authored | confirmed |
| 18 | `0xbc` | 4 | `AR_get_long` | `getDraftCheck(1)` | authored | confirmed |
| 19 | `0xc0` | 4 | `AR_get_long` | `getDraftDirection(0)` | authored | confirmed |
| 20 | `0xc4` | 4 | `AR_get_long` | `getDraftDirection(1)` | authored | confirmed |
| 21 | `0xb0` | 4 | `AR_get_long` (ver > 1864) | `getTranslateSurface(0)` | authored | confirmed |
| 22 | `0xb4` | 4 | `AR_get_long` | `getTranslateSurface(1)` | authored | confirmed |
| 23 | `0xc8` | object | `operator>>` `moDisplayDim_c*` | draft-angle dimension, direction 0 (`getAngle(0)`) | authored | confirmed |
| 24 | `0xd0` | object | `operator>>` `moDisplayDim_c*` | draft-angle dimension, direction 1 | authored | confirmed |
| 25 | `0xa8` | 4 | `AR_get_long` (ver > 209) | (no accessor) | unknown | partial |
| 26 | `0xac` | 4 | `AR_get_long` | (no accessor) | unknown | partial |
| 27 | `0xd8` | 4 | `AR_get_long` (ver > 305) | (no accessor) | unknown | partial |
| 28 | `0xdc` | 4 | `AR_get_long` | (no accessor) | unknown | partial |
| 29 | `0xe0` | sub-record | slot 5 (ver > 1021) | (a member object) | unknown | confirmed (2 bytes in corpus) |
| 30 | `0x100` | sub-record | slot 5 (ver > 1022) | (a member object) | unknown | confirmed (2 bytes in corpus) |
| 31 | `0x128` | 4 | `AR_get_long` (ver > 1605) | **`getMerge()` — merge result** | authored | confirmed |
| 32 | `0x12c` | 4 | `AR_get_long` (ver > 1672) | `getNormalCut()` | authored | confirmed |
| 33 | `0x130` | 4 | `AR_get_long` (ver > 9207) | (no accessor) | unknown | partial |
| 34 | `0x78` | object | **only if `getType(0) == 7`** (ver > 2154) | `getIBodyRef(0)` — UpToBody | authored | partial |
| 35 | `0x80` | object | **only if `getType(1) == 7`** | `getIBodyRef(1)` | authored | partial |
| 36 | `0x140` | object | `ReadObject(moFromEndSpec_c)` (ver > 2648) | `getFromEndSpec()` | authored | confirmed |
| 37 | `0x148` | 4 | `AR_get_long` (ver >= 4460) | `getCapEnd(0)` | authored | confirmed |
| 38 | `0x14c` | 4 | `AR_get_long` | `getCapEnd(1)` | authored | confirmed |
| 39 | `0x150` | 4 | `AR_get_long` | `getDelInitFace()` | authored | confirmed |
| 40 | `0x154` | 4 | `AR_get_long` | `getKnitRes()` | authored | confirmed |
| 41 | `0x158` | 4 | `AR_get_long` (ver >= 15105) | `getCreateSolidFrmCappedMidPlaneSurfExt()` | authored | confirmed |

Two post-read fixups the reader applies, which a writer must respect or the value it writes will
be silently changed on load:

* `if (getType(0) == 6) { this->0x08 = 1; }` — MidPlane forces `SingleEnd` to 1.
* `if ((uint)this->0x12c > 1) { this->0x12c = 0; }` — `NormalCut` is clamped to `{0, 1}`.

### Byte offsets, for the common corpus shape

For a class definition, data starts at `marker + 17` (`ff ff 01 00 0b 00` + `"moEndSpec_c"`); for
a class reference, at `marker + 2`. With `getDirSpec()` and `getKeepPiece()` both null — true in
158 of 158 corpus parts — the leading fields are at fixed offsets from `marker`:

| field | definition | class reference |
|---|---|---|
| `getSingleEnd()` | `marker + 19` | `marker + 4` |
| `getFlip()` | `marker + 23` | `marker + 8` |
| `getDirection()` (reverse) | `marker + 27` | `marker + 12` |
| `getType(0)` (`swEndConditions_e`) | `marker + 33` | `marker + 18` |
| `getType(1)` | `marker + 37` | `marker + 22` |

`marker + 27` and `marker + 33` are exactly the two bytes `.rescratch/corpus/REPORT.md` §5.3
found by differencing. The decompilation adds that both are **`i32`, not 1 byte** — the earlier
work explicitly could not determine the width — and that there is a second, per-direction copy of
each.

### Evidence

`verify_layout.py` walks the table against the real object segmentation in
`.rescratch/trace/out/segments_*.json`. It consumes the object's traced children in order and the
scalar bytes between them, and fails if any gap is not exactly filled.

```
13/13 moEndSpec_c objects across the 9 traced parts reproduce the traced spans exactly
```

with, notably, values never produced by the authored corpus:

| part | node | `getType(0)` | `getDirection()` |
|---|---|---|---|
| `COJINETE INFERIOR.SLDPRT` (V8 production) | 532 | **6 MidPlane** | 0 |
| `Piston Ring KF.SLDPRT` (V8 production) | 908 | **1 ThroughAll** | 1 |
| `PADPLANE_rev_d5` / `CUTBASE_cd5` / `THREEFEATURE` | 495/495/505 | 0 Blind | **1 reversed** |

`scan_endspec.py` then decodes the first `moEndSpec_c` of **every** part statically, using only the
fixed offsets above plus the two null-token checks:

```
parts with a moEndSpec_c definition: 158, decoded: 158, rejected: 0
  type0=0 (Blind)          type1=0 reverse=0  n=133
  type0=0 (Blind)          type1=0 reverse=1  n=17
  type0=6 (MidPlane)       type1=0 reverse=0  n=6
  type0=9 (ThroughAllBoth) type1=1 reverse=0  n=2   Cam_roller.SLDPRT, Piston.SLDPRT
```

158/158 decode consistently, and code **9 = ThroughAllBoth** appears in two real production parts
with `getType(1) = 1` — the first evidence in this project of a two-direction end condition and of
the second-direction field being used at all.

---

## 2. `moFromEndSpec_c` — CONFIRMED

Function: `sldmodu.dll` `0x4bb900d0`. Accessors: `getType()` → `FrmExtruType` (the API's
`swStartConditions_e`), `getRefWrap()`, `getOffset(i)`, `getOffsetDir()`.

The record is *variable length and driven entirely by its first field*:

| # | `this` offset | width | condition | name | confidence |
|---|---|---|---|---|---|
| 1 | — | 4 | always | raw type code `t` | confirmed |
| — | `0x10` | — | `t in {4,5}` → `0x10 = 3`; else `0x10 = t` | `getType()` | confirmed |
| 2 | `0x08` | object | `t == 1` or `t == 2` | `getRefWrap()` (`moRefWrapper_c*`) | partial |
| — | — | — | **if `getType() != 3` the record ends here** | | confirmed |
| 3 | `0x28` | object | `t == 5`, or (`t != 4` and ver > 4197) | offset dimension (`moDisplayDim_c*`) | partial |
| 3' | `0x18` | 8 | `t == 4`, or (`t != 4/5` and ver <= 4197) | `getOffset(0)` (metres) | partial |
| 4 | `0x20` | 4 | always when `getType() == 3` | `getOffsetDir()` | partial |

Type semantics, from the branches: `0` sketch plane, `1` surface/face (carries a ref), `2` vertex
(carries a ref), `3` offset (carries a dimension or a raw double), `4`/`5` legacy spellings of `3`.

**In all 9 traced parts the code is `0`, so the whole record is 4 bytes.** That is what makes the
tail budget below close exactly, and it is why the earlier marker-relative reading of
"`moFromEndSpec_c + 29`" and "`moFromEndSpec_c + 140`" was reading other objects' fields:
`moFromEndSpec_c` only ever owns 4 bytes in this corpus.

### The shared tail run, and the version gate that changes its length

The bytes after `moFromEndSpec_c`'s body belong to its ancestors, in this order:

```
moFromEndSpec_c      4                    (type code 0)
moEndSpec_c         16 or 20              CapEnd[0], CapEnd[1], DelInitFace, KnitRes,
                                          + CreateSolidFrmCappedMidPlaneSurfExt only if ver >= 15105
moExtrusion_c        8 + 4                double @0x7d0, long @0x7a8
stream driver        0 or 4               only when the extrusion is the last top-level object
```

Measured against the traced runs:

| part | run | 4 + moEndSpec + 12 + trailer | file era |
|---|---|---|---|
| `PADPLANE_rev_d5`, `CUTBASE_cd5`, `THREEFEATURE` | 36 | 4 + 20 + 12 + 0 | ver >= 15105 |
| `BASELINE_40x20x10`, `CIRCLE_r10`, `PLANE_TOP` | 40 | 4 + 20 + 12 + 4 | ver >= 15105, last object |
| `Piston Ring KF` (V8) | 32 | 4 + 16 + 12 + 0 | ver < 15105 |
| `COJINETE INFERIOR` (V8) | 36 | 4 + 16 + 12 + 4 | ver < 15105, last object |

All four cases close exactly, and the split is the direct consequence of the
`if (version < 15105) { this->0x158 = 1; } else { AR_get_long(this->0x158); }` gate. That the two
V8 parts land on the shorter form is independent evidence that they were saved by an older
SOLIDWORKS than the authored corpus.

---

## 3. `moRevEndSpec_c` — CONFIRMED

Function: `sldmodu.dll` `0x4bb9b650`. `moRevEndSpec_c::getType` is the *same machine code* as
`moEndSpec_c::getType` (`return *(int *)(this + 4*i + 0xc)`), so the two classes share the
end-condition offset.

| # | `this` offset | width | archive op | name | confidence |
|---|---|---|---|---|---|
| 1 | `0x08` | 4 | `AR_get_long` | `getSingleEnd()` (forced to 1 when `getType(0) == 6`) | confirmed |
| 2 | `0x138` | 4 | `AR_get_long` | (no accessor) | partial |
| 3 | `0x13c` | 4 | `AR_get_long` | (no accessor) | partial |
| 4 | `0x0c` | 4 | `AR_get_long` | **`getType(0)` — end condition, direction 0** | confirmed |
| 5 | `0x10` | 4 | `AR_get_long` | `getType(1)` — end condition, direction 1 | confirmed |
| 6 | `0x118` | object | `operator>>` | `getISurfRef(0)` (`moRefWrapper_c*`) | confirmed (null) |
| 7 | `0x120` | object | `operator>>` | `getISurfRef(1)` | confirmed (null) |
| 8 | `0x128` | object | `operator>>` | `getUpToPointRef(0)` (`moPointRef_w*`) | confirmed (null) |
| 9 | `0x130` | object | `operator>>` | `getUpToPointRef(1)` | confirmed (null) |
| 10 | `0x38` | 8 | `AR_get_double` | per-direction offset distance, direction 0 | partial |
| 11 | `0x40` | 8 | `AR_get_double` | per-direction offset distance, direction 1 | partial |
| 12 | `0x140` | 4 | `AR_get_long` | `getOffsetReverse(0)` | confirmed |
| 13 | `0x144` | 4 | `AR_get_long` | `getOffsetReverse(1)` | confirmed |
| 14 | `0x18` | object | `operator>>` `moDisplayDim_c*` (ver >= 4547) | angle dimension, direction 0 | confirmed |
| 15 | `0x20` | object | `operator>>` `moDisplayDim_c*` | angle dimension, direction 1 | confirmed |
| 16 | `0x28` | object | `operator>>` `moDisplayDim_c*` (ver > 4577) | offset dimension, direction 0 | confirmed |
| 17 | `0x30` | object | `operator>>` `moDisplayDim_c*` | offset dimension, direction 1 | confirmed |
| — | `0x150`, `0x158` | 8, 8 | **only if ver < 4547** | `getRevolveAngle(i)` — legacy raw angle | partial |

There is **no angle scalar in a modern `moRevEndSpec_c`**. `moRevEndSpec_c::getAngle(i)` reads the
`moDisplayDim_c` at `0x18 + 8i` and, when it is null, returns the literal `6.2831853071796` —
2π. That is exactly why all 67 corpus revolves are 360° with a constant record: a full revolve
stores no angle at all.

### Byte offsets and evidence

Data starts at `marker + 20` for a definition (`ff ff 01 00 0e 00` + `"moRevEndSpec_c"`),
`marker + 2` for a reference. With items 6–9 all null:

| field | definition |
|---|---|
| `getSingleEnd()` | `marker + 20` |
| `getType(0)` | `marker + 32` |
| `getType(1)` | `marker + 36` |
| offset distance 0 | `marker + 48` |
| offset distance 1 | `marker + 56` |
| `getOffsetReverse(0)` | `marker + 64` |
| `getOffsetReverse(1)` | `marker + 68` |

Total data length `4 + 4 + 4 + 4 + 4 + 2 + 2 + 2 + 2 + 8 + 8 + 4 + 4 = 52`, then four null
dimension tokens. **This is byte-for-byte the 52-byte constant record that
`.rescratch/revolve/REVOLVE.md` §4.1 measured** — `01 00 00 00`, 24 zero bytes, two `0.01`
doubles, 8 zero bytes — and it now decomposes as five `i32` plus four null object tokens, then the
two doubles, then two `i32`. `REVOLVE.md` §3.4's observation that in 22 of 40 parts the class
defined immediately after the record is `moDisplayAngularDim_c` is item 14.

`scan_revendspec.py`:

```
parts with a moRevEndSpec_c definition: 37
  type0=0 (Blind) type1=0 singleEnd=1 d@0x38=0.01 d@0x40=0.01 n=37
```

---

## 4. `moExtrusion_c` / `moICE_c` — CONFIRMED for its own three fields

Function: `sldmodu.dll` `0x4bb8eba0`. The function identifies itself: it opens with
`suCrash_c::Point::Point(&p, "moExtrusion_c::Serialize", false)`. `moICE_c` does not override it —
slot 5 of both `moExtrusion_c`'s and `moICE_c`'s vftables is this same address — so the two
classes have **identical record layouts**. `moICE_c` adds only a constructor
`moICE_c(moModel_c*, double, double)` and a virtual `isICE()`.

`moExtrusion_c::Serialize` contributes exactly three things, after delegating everything else:

| # | `this` offset | width | archive op | confidence |
|---|---|---|---|---|
| 0 | — | — | `moBodyFeature_c::Serialize(this, ar)` — the whole base record | confirmed |
| 1 | `0x7b0` | object | `ReadObject(moEndSpec_c)` | confirmed |
| 2 | `0x7d0` | 8 | `AR_get_double` (ver > 2455) | confirmed |
| 3 | `0x7a8` | 4 | `AR_get_long` (ver > 3518) | confirmed |

In every traced part `0x7d0 = 0.0` and `0x7a8 = 0xffffffff`. Those are the last 12 bytes of the
`moExtrusion_c` scope, and they are what makes the tail budget in §2 close.

**There is no boss/cut field and no operation code in this function.** See `ANSWERS.md` Q1.

### The base chain

`moBodyFeature_c::Serialize` (`0x4bb8aa10`) itself begins with an unnamed base call
(`FUN_4bb886c0`), so the bulk of the extrusion record — the traced 49-, 30-, 52- and 707/873-byte
runs — is produced by `moModelFeature_c` / `moFeature_c` / `moNode_c`, not by `moBodyFeature_c`
or `moExtrusion_c`. `moBodyFeature_c::Serialize`'s own modern reads are only:

| # | `this` offset | width | condition | confidence |
|---|---|---|---|---|
| 1 | `0x1d8` | 8 | ver in `[107, 938)` — never for corpus files | confirmed (not taken) |
| 2 | `0x6d8` | object | ver > 110: `ReadObject(moAsmFeatData_c)` | confirmed |
| 3 | `0x750` | object | ver > 3916 and `!hasCondition(1)`: `operator>> moCompFeature_c*` | confirmed |
| 4 | `0x778` | sub-record | ver > 4259: slot 5 of `suObArray` | confirmed |
| 5 | `0x798` | 4 | ver > 4583: `AR_get_long` | confirmed |

Recovering `moModelFeature_c` / `moFeature_c` / `moNode_c::Serialize` is the remaining work for a
complete extrusion record; their decompiled C is in `out/sldmodu.c` (`moFeature_c::Serialize`,
`moModelFeature_c::Serialize`, `moNode_c::Serialize`) but has not been reconciled against the
traced runs here. **unresolved.**

---

## 5. `moLengthParameter_c` — CONFIRMED

Function: `sldmodu.dll` `0x4c1d9b70`. The store branch writes a `su_DBKey` naming the field, which
is how the name is authoritative rather than inferred:

```c
CStringT(local_res18, "Value");
su_DBKey(local_res20, local_res18);
this = su_CArchive::AR_put_su_DBKey(ar, psVar3);
su_CArchive::AR_put_double(this, *(double *)(param_1 + 0x50));
```

| # | `this` offset | width | archive op | name | confidence |
|---|---|---|---|---|---|
| 0 | — | — | base `moParameter_c::Serialize` (`FUN_4c1dbf20`) | | confirmed |
| 1 | `0x50` | 8 | `AR_get_double` | **`Value`** — metres | confirmed |
| 2 | `0x60` | 1 | `AR_get_uchar`, ver > 986 and `!hasCondition(0x80)` | override present | confirmed |
| 3 | `0x58` | 8 | `AR_get_double`, only if #2 != 0 | override value; copied over `Value` | partial |

Reader fixup a writer must respect: if the owning parameter reports "not signed" (virtual slot
`0x518`) and `Value < 0`, the reader negates it. So a negative depth cannot be stored here — the
direction lives in `moEndSpec_c::getDirection()`.

This is the record `.rescratch/grammar/GRAMMAR.md` §5.2 calls the "dimension-scalar" whose `D1`
copy at `+0` is the authored depth: `+0` is `Value`.

---

## 6. `sgEntHandle` (and its 20 subclasses, including `sgArcHandle`, `sgLineHandle`) — PARTIAL

Function: `sldmodu.dll` `0x4c5c91a0` = `sgEntHandle::Serialize`, shared by 20 classes per
`out/serialize_map.json`. The store branch names the field:

```c
CStringT(&local_res18, "EntIndex");
if (*(uint *)(this + 0x18) < 0x777f) { AR_put_ushort(ar, *(ushort *)(this + 0x18)); }
else { AR_put_ushort(ar, 0x777f); /* then a wider write */ }
```

So the handle is an **escaped entity index**: a `u16` when below `0x777f`, otherwise the sentinel
`0x777f` followed by a wider field. That escape is why the traced `sgLineHandle` spans are 12, 16
and 99 bytes rather than one constant. The remainder of the record (the parts that make up the
99-byte instances) has **not** been reconciled against the traced spans. **partial.**

`sgArcHandle` has no `Serialize` of its own — slot 5 of its vftable is `sgEntHandle::Serialize`.
The `sg*` geometry classes that do have their own serialisers, with addresses, are listed in
`out/serialize_map.json` (`sgArc` `0x4c5c6b10`, `sgLine` `0x4c5cc540`, `sgSketch`, `sgDim`,
`sgLogDim`, …). Their layouts are **unresolved** here.

---

## 7. `moProfileFeature_c` — UNRESOLVED

Function: `sldmodu.dll` `0x4bb99220`, decompiled in `out/sldmodu_accessors2.c`. It is a large
function with many `AR_get_ushort` / `AR_get_long` reads interleaved with `sgSketch`,
`sgLineHandle`, `moContourChooser_c` and `moSketchBitmap_c` object reads, plus two sub-record
slot-5 calls into members at `+0x128` and `+0x148` of a sub-object. It has not been reconciled
against the traced 24-byte-header / 2200-byte-scope profile records. **unresolved.**

---

## 8. The class → `Serialize` address map

`out/serialize_map.json` maps **2607** RTTI-named classes in `sldmodu.dll` to their vtable slot-5
function: 1437 distinct functions, plus 549 classes that do not override it and inherit
`su_CObject::Serialize`. This is the index to use for any further class: look the class up, feed
the address to `DumpFunctions.java`, read the linear sequence of `AR_get_*` calls.

`out/sldmodu_vtslots.txt` is the raw dump (9395 vftables, first 40 slots each).
