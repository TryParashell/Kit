# `sg*` sketch-geometry record layouts

Source: Ghidra 12.1.2 headless decompilation of `sldmodu.dll` from the licensed SOLIDWORKS 2025
install. No SOLIDWORKS process, no COM, no debugger. The dump is
`.rescratch/ghidra/out/task2.c` (325 functions, `RunDumpTaskTwo.ps1` + `SpecTaskTwo.txt`);
`RenameArchiveApi.java` had already been applied and saved to the project, so every
`su_CArchive::operator>>` overload appears as `AR_get_<type>` and the widths below are read, not
guessed.

Confidence words are used exactly as in `Serialize.md`:

* **confirmed** — read out of the decompiled `Serialize` *and* the byte arithmetic reproduces a
  real traced object span exactly.
* **partial** — read out of the decompiled `Serialize`, but no traced span independently checks it.
* **not found** — not recovered.

Version gates are the decimal-coded file version fetched as `*(uint *)(moArchiveHelper + 0x780)`.
Every corpus and traced part is version 18000+, so **every `if (CONST < version)` branch below is
taken and every `version < CONST` legacy branch is not**. The tables give the modern shape only;
the legacy shape is noted where it changes the length.

---

## 1. `sgEntHandle` — CONFIRMED

Function: `0x4c5c91a0`, shared by **20** handle classes — `sgArcHandle`, `sgLineHandle`,
`sgPointHandle`, `sgEntHandle` itself and 16 more. None of them override slot 5, so this is the
whole record for all of them, and the concrete subclass adds nothing of its own.

The store branch names every field with a `su_DBKey`, so the names are authoritative:

| # | `this` offset | width | archive op | name | confidence |
|---|---|---|---|---|---|
| 0 | — | 0 | `su_CObject::Serialize` | (no bytes) | confirmed |
| 1 | `0x18` | 2, or 2+4 | `AR_get_ushort`, then `AR_get_long` **only if the `u16` is `0x777f`** | **`EntIndex`** | confirmed |
| 2 | `0x1c` | 4 | `AR_get_long` (ver >= `0x9f7` = 2551) | **`RefId`** | confirmed |
| 3 | `0x08` | 4 | `AR_get_long` (ver >= `0x17d7` = 6103) | **`DimOnCM`** | confirmed |

**Total: 10 bytes** unescaped, 14 when `EntIndex >= 0x777f`.

Two legacy details a modern writer does not need but which explain old files: below version
`0xa84` (2692) an `EntIndex` in the range that makes `(u16 + 99)` fit in a byte is
**sign-extended** from `i16`, so small negative indices exist in old files; below `0x77e` (1918)
there is no `su_DBKey` framing and `RefId`/`DimOnCM` are absent entirely.

### Evidence

`VerifySketch.py` walks every traced handle object in the 9 segmented parts, takes the object's
first scalar gap (children excluded by `layout.gaps`) and decodes it with the escape rule:

```
sgArcHandle      classref    ok            20
sgArcHandle      definition  ok             2
sgLineHandle     classref    ok            97
sgLineHandle     definition  ok             8
sgPointHandle    classref    ok            12
sgEntHandle chain: 139/309 traced handle records tile exactly
RefId   values {-1: 139}
DimOnCM values {0: 139}
```

**139 traced handle records are exactly 10 bytes, with `RefId = -1` and `DimOnCM = 0` in every
one.** The arithmetic also closes on the raw traced spans without the walker: a `sgLineHandle`
class *reference* is `2` (token) `+ 10` = **12 bytes**, and 97 traced instances measure exactly 12;
a `sgLineHandle` class *definition* is `6 + len("sgLineHandle")=12` `+ 10` = **28 bytes**, and all
8 traced definitions measure exactly 28; `sgArcHandle` definitions are `6 + 11 + 10` = **27**, and
both traced ones measure 27.

The remaining 170 traced handle objects carry 4 to 90 further bytes in the same gap. Those are
**not** extra `sgEntHandle` fields — no handle subclass overrides slot 5 — they are bytes the
tracer folded into the last child's scope because it derives `scope_end` from the next sibling's
start. Reconciling them needs the *owner's* field table (`sgSketch`, `moProfileFeature_c`), not
this one. So the 10-byte base record is confirmed; the per-owner trailers are **partial**.

---

## 2. `FUN_4c5d1b60` — the shared curve base of `sgArc` and `sgLine` — PARTIAL

Both `sgArc::Serialize` and `sgLine::Serialize` open with an unnamed base call to `0x4c5d1b60`.
That function has no RTTI name in `sldmodu.dll`; it is the common curve/edge base
(`sgCurve`-level). Its store branch names all five fields with `su_DBKey`s.

| # | `this` offset | width | archive op | name | confidence |
|---|---|---|---|---|---|
| 1 | `0xc8` | 2, or 2+4 | `AR_get_ushort`, then `AR_get_long` **only if the `u16` is `0xffff`** | **`End1`** — start point handle index | partial |
| 2 | `0xcc` | 2, or 2+4 | same escape | **`End2`** — end point handle index | partial |
| 3 | `0xd0` | 2 | `AR_get_ushort` | **`isContour`** | partial |
| 4 | `0xd4` | 2 | `AR_get_ushort` | **`isFlipped`** | partial |
| 5 | `0xc0` | 8 | `AR_get_double` (ver > `0x771` = 1905) | **`NormalScale`** | partial |

**Total: 16 bytes** with neither end escaped (`2 + 2 + 2 + 2 + 8`).

Reader fixups a writer must respect:

* `NormalScale` is initialised to `-1.0` before the read. Only if the value read is **> 0.0** does
  the reader allocate a 0x58-byte side object and store it at `this + 0xc0`; otherwise `0xc0`
  stays null. So `NormalScale <= 0` means "no normal scaling", and the store branch only writes
  the double at all when `this + 0xc0` is non-null.
* Below version `0x4a1` (1185) `End1` / `End2` / `isContour` are three plain `u16`s with no escape
  and `isFlipped` follows; the escape and the `su_DBKey` naming are modern only.

So a line or an arc **does not store its own coordinates**. It stores *point-handle indices* into
the owning `sgSketch`'s point table (`End1`, `End2`, and for an arc also `Center`), and the
coordinates live in the sketch's point array. That is the single most important fact for the
profile writer.

---

## 3. `sgLine` — PARTIAL

Function: `0x4c5cc540`.

| # | `this` offset | width | archive op | condition | confidence |
|---|---|---|---|---|---|
| 0 | — | 16 | `FUN_4c5d1b60` — the whole curve base above | always | partial |
| 1 | `0xe0` | object | `mgVector_c::restore(ar)` | **only if `(*(u16 *)(this + 0x56) & 0x200) != 0`** | partial |
| 2 | `0xe8` | 2 | `AR_get_ushort` | ver > `0xd98` = 3480 | partial |

**Total: 18 bytes** when the `0x200` flag is clear. The `0x56` half-word is a display/state flag
set by the base chain, not by this function; when its bit `0x200` is set an `mgVector_c` (a
direction vector) is read inline through `mgVector_c::restore`, which is *not* an archive object
token, so it does not appear as a traced child.

There is a second, non-archive side effect: when `(*(u8 *)(this + 0x54) & 8) != 0` the reader
overwrites the line width at `this + 0x3c` with `utLineWidth_c(0)`. No bytes.

---

## 4. `sgArc` — PARTIAL

Function: `0x4c5c6b10`. The store branch names every field with a `su_DBKey`.

| # | `this` offset | width | archive op | name | confidence |
|---|---|---|---|---|---|
| 0 | — | 16 | `FUN_4c5d1b60` — the curve base above | | partial |
| 1 | `0xd8` | 4 | `AR_get_long` | **`Rotation`** | partial |
| 2 | `0xdc` | 2, or 2+4 | `AR_get_ushort`, then `AR_get_long` **only if the `u16` is `0xffff`** | **`Center`** — centre point handle index | partial |
| 3 | `0xe0` | 4 | `AR_get_long` | **`Normal`** | partial |
| 4 | `0xe4` | 4 | `AR_get_long` (ver > `0x411` = 1041) | **`FiletLine1`** | partial |
| 5 | `0xe8` | 4 | `AR_get_long` | **`FiletLine2`** | partial |
| 6 | `0xec` | 4 | `AR_get_long` (ver > `0x413` = 1043) | **`VirtualPoint`** | partial |

**Total: 38 bytes** with no escape (`16 + 4 + 2 + 4 + 4 + 4 + 4`), 42 when `Center` escapes.

Reader fixups:

* When the version gate for items 4–6 is *not* met the reader writes the sentinel `0xfffffffe`
  (`-2`) into `FiletLine1`, `FiletLine2` and `VirtualPoint`. `-2` is therefore the "absent"
  value for all three, not `0` and not `-1`.
* Below version `0x1ff` (511), and when `(*(u8 *)(this + 0x54) & 1) == 0`, the reader
  *synthesises* a centre `sgPointHandle` and calls `addCenterReference` instead of reading the
  fillet fields. Modern files never take that path.

So the geometric content of an arc is: two endpoint handles (`End1`, `End2` in the base), a centre
handle (`Center`), a `Normal` index and a `Rotation` index. **A full circle and an arc use the same
record**; nothing in it is an angle or a radius. Radius comes from the point coordinates in the
sketch, exactly as it does for a line.

---

## 5. `sgSketch` — PARTIAL, container only

Function: `0x4c5d28c0`, **4849 decompiled lines**. It is the container that owns the point table
and the entity list, and it is count-driven rather than a flat field list: it reads entity counts
with `AR_get_int`, then loops, and inside each loop it dispatches on a `u16` discriminator read
with `AR_get_ushort` (`0`, `1`, `2` are the branch values at the first dispatch) before calling
slot 5 on the member entity.

What is established:

* `sgArc` and `sgLine` records are **inline sub-records** reached through
  `(**(code **)(*member + 0x28))(member, ar)`, not through `ReadObject`. That is why neither class
  appears anywhere in the traced segmentation — only the *handles* do — and it is why their
  layouts above are **partial**: there is no traced span whose length they can be checked against.
  Verifying them requires tiling `sgSketch`'s own scalar gaps, which needs the full container
  field order.
* The traced `sgSketch` definitions are 540 and 541 bytes and the class references 1433–8847
  bytes, and a `sgPointHandle` **class definition appears inline inside one of those scalar
  gaps** — further confirmation that the sketch body is not fully segmented by the tracer.
* `sgSketch::Serialize` registers itself with `moArchiveHelper_c::addSgSketchesSerialized` and
  branches on `isSerializingSketchInfo`, so the same function emits two different records
  depending on which stream is being written.

The full container field order is **not found**.

## 6. The sketch-coordinate role/class trailer — NOT FOUND

The observed `role ∈ {0, 2, 6, 8, 14, 24, 29}` and `class ∈ {0, 1, 2, 3, 5}` are **not**
`sgEntHandle`'s `RefId`/`DimOnCM`: those are `-1` and `0` respectively in all 139 traced handle
records, so neither field is the trailer. The enum was not located. `sgSpline` has no RTTI vftable
in `sldmodu.dll` at all, so at least one profile entity type is defined in another module or under
a different spelling.

---

## 7. Addresses for the rest of the `sg*` family

From `out/SerializeMap.json`, the `sg*` classes that own a slot-5 serialiser:

| class | `Serialize` | status here |
|---|---|---|
| `sgEntHandle` (+19 handle subclasses) | `0x4c5c91a0` | confirmed, §1 |
| `sgArc` | `0x4c5c6b10` | partial, §4 |
| `sgLine` | `0x4c5cc540` | partial, §3 |
| curve base (unnamed) | `0x4c5d1b60` | partial, §2 |
| `sgSketch` | `0x4c5d28c0` | container only, §5 |
| `sgPoint` | `0x4c5d0b70` | not dumped |
| `sgEllipse` | `0x4c5c8730` | not dumped |
| `sgParabola` | `0x4c5c7a30` | not dumped |
| `sgSpline` | — | no RTTI vftable in `sldmodu.dll` |
