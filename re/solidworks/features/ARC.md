<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Sketch arcs in `Contents/Config-0-ResolvedFeatures`

Scope: can a **partial** arc (an arc segment with a start and an end, as opposed to a full circle) be
located and read statically from the resolved-features lane, so that
`resolved.sketch_arcs()` / `patch_sketch_arcs()` can decode one and a donor can carry an
arc-bearing profile?

**Historical answer: no; superseded in part by `ARC_LAYOUT.md`.** This static pass did not locate the
partial arc's radius, centre, and endpoints in the record family it could segment. The later authored
differential located the arc representation. Kit still has no arbitrary partial-arc feature program,
so those source histories fail closed; there is no donor library or donor fallback.

Corpus: `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024` (57 parts) plus
`examples/Random/**` (53 parts) = **110** parts with a resolved-features lane and a
`swXmlContents/KeyWords`. Tools in this directory; nothing under `src/` was changed for the
investigation itself.

---

## 1. What the coordinate record is, and what it is not

`GRAMMAR.md` §5.1 fixes the record: an 18-byte prefix (`double 1.0`, `double 0.0`, `u16 30`), then
`double x`, `double y` in metres, then a 4-byte trailer read as `u16 role`, `u16 class`.
`resolved.sketch_coordinates()` enumerates them.

The trailer taxonomy over all 110 parts (`groups.py` → `groups.txt`):

| role | class | count | reading                                                        |
| ---- | ----- | ----- | -------------------------------------------------------------- |
| 0    | 2     | 3764  | free point                                                     |
| 0    | 1     | 2464  | free point on a line-backed entity                             |
| 0    | 0     | 1841  | free point, unattributed                                       |
| 2    | 2     | 1764  | point **constrained on a curve**                               |
| 6    | 0     | 1552  |                                                                |
| 8    | 1     | 1330  |                                                                |
| 0    | 4     | 674   |                                                                |
| 1    | 0     | 503   |                                                                |
| 0    | 3     | 432   |                                                                |
| …    |       |       | 28 further pairs, all ≤ 233, every one of them with `role = 0` |

The decisive negative is here: **there is no `class` value that marks an arc.** Every one of the
1764 curve-constrained points is `class = 2`, the same value a free point carries, and the 28
long-tail `class` values all appear with `role = 0`, i.e. on free points. So the record cannot say
"I am an arc rim point" as opposed to "I am a line endpoint that happens to sit on a circle".

## 2. The full circle is decodable, and that part is confirmed

A circle is a free centre point followed by an on-curve point at exactly **17°**; the radius is
`hypot(dx, dy)`. `radii.py` cross-checks that against `KeyWords` ground truth:

```
diametral dimensions  578/817 matched a 17deg circle group
```

70.7% of every `<MOD-DIAM>` dimension in the corpus resolves to a centre/17°-point pair with
radius = value/2, across 110 production parts authored by other people in other SOLIDWORKS
versions. The remaining 29% are diameters on cylindrical **faces** (hole wizard, revolve results),
not sketch circles, so they have no sketch group to match. This corrects the standing note that the
17° convention is an artefact of COM `CreateCircleByRadius`: it is SOLIDWORKS' own canonical circle
representation, and `sketch_arcs()` reads production circles, not just authored ones.

## 3. The partial arc is not in the coordinate stream — three independent proofs

### 3.1 Radial dimensions do not resolve

```
radial dimensions      20/362 matched a 17deg circle group
```

A `R<value>` dimension is applied to an arc or a fillet. Only **5.5%** of them resolve to a circle
group. If a partial arc were stored as a centre plus a defining rim point the way a circle is, the
radial hit rate would track the diametral one. It does not.

### 3.2 The "centre + start + end" hypothesis is refuted outright

The natural guess is that an arc is three consecutive coordinate records: a centre, then two
on-curve points at equal radius (the endpoints). The corpus contains exactly **52** such
equal-radius groups, and

```
equal-radius pairs: 52, of which one point is at 17deg: 52
```

**every single one** contains a point at exactly 17°, and in every one the other point sits at
exactly 0°, 180° or 360°:

```
BLOQUE V8.SLDPRT              r=42.9000  a0=180.0000  a1=17.0000  sweep=197.0000
CIGUEÑAL.SLDPRT               r=32.0000  a0=  0.0000  a1=17.0000  sweep= 17.0000
CUBIERTA DE TURBINA 1.SLDPRT  r=24.7650  a0=180.0000  a1=17.0000  sweep=197.0000
```

So these are not arcs. They are a circle (centre + its 17° defining point) together with one extra
curve-constrained point pinned to the circle's horizontal diameter — a coincidence or a dimension
witness. There is no group in 110 parts whose two on-curve points are both at arbitrary angles.
The hypothesis has zero supporting instances and 52 refuting ones.

### 3.3 The radius value exists in the lane, but nothing locates it

`scan_radius_doubles.py` searches the whole lane for a `float64` equal to each radial dimension in
metres, on the 20 smaller arc-bearing parts:

```
radial dimension values found as a float64 in the lane: 68/72
```

The value _is_ stored — with **3 to 11 candidate offsets per value** and no anchor to pick the right
one, and, critically, without the centre or the endpoints anywhere in the coordinate stream. A
radius alone does not place an arc. Writing one blind would move geometry.

## 4. Where the arc actually lives, and why that is out of reach

`classes.py` inventories the class definitions in every lane. `.rescratch/v8/vocabulary.txt` lists
185 `mo*` classes and no `sg*` classes at all, because that census filtered on the `mo` prefix. The
lane also carries **1134** `sg*` class definitions:

```
100  sgSketch          96  sgArcHandle       93  sgLineHandle      93  sgCircleDim
100  sgPointHandle     93  sgEntHandle       91  sgPntPntDist      73  sgLLDist
 71  sgPntLineDist     55  sgAnglDim         29  sgOffsetDim        9  sgSplineHandle
  9  sg3DPlaneHandle    5  sgSkOffsetDim      3  sgSlot_c           1  sgEllipseHandle
```

`sgArcHandle` is defined in **96 of 110** parts, so arcs are serialized as `sgArcHandle` objects.
Dissecting the first such object (`firstobjects.py`, on the smallest arc-bearing part,
`examples/Random/Pistons/Piston_ring.SLDPRT`, 14 109 bytes) shows the object body is 64 bytes of
base-class data followed by a nested `ff ff 1f 00 03` entity record; the coordinate record that
`sketch_coordinates()` finds sits _inside_ that nested record. The arc's own parameters are in the
`sgArcHandle` body, whose byte extent cannot be computed without the per-class `Serialize` layout.

That is exactly the keystone `GRAMMAR.md` §8 item 1 records as unsolved: without object
segmentation the object boundaries are unknown, so a field at a fixed offset inside `sgArcHandle`
cannot be located, and the su_CArchive class-reference token that would let the _second_ and later
`sgArcHandle` objects be found cannot be computed either (§2.3 — the map index depends on the
object count before the definition).

## 5. What was left alone, deliberately

- `resolved.sketch_arcs()` and `patch_sketch_arcs()` keep the centre + 17°-point circle rule
  unchanged. §2 upgrades the confidence in that rule from "COM-authored only" to "production
  corpus, 578 dimensions"; it does not change a byte of behaviour.

* No `arc` or `polyline+arc` profile was added to the historical donor library.
* The old matcher declined `PartDesignExample.FCStd`'s `Pad`. The current writer also declines that
  history, for a different architectural reason: no complete typed program yet expresses its three
  lines and one arc, and donor streams are prohibited.

## 6. What would lift it

In priority order, and all of it needs a SOLIDWORKS session, not more static work:

1. **Author the differential family by COM**: one sketch, one arc, swept 30°/90°/180°/270°, then the
   same arc at two radii and two centres, on an otherwise identical part. Diffing those pins the
   arc record's field layout relative to the `sgArcHandle` definition directly, the way
   `.rescratch/corpus2` pinned the extrude depth. Six parts is enough.
2. **Object segmentation** (`WINDBG.md`), which lifts this and items 2, 6 and 7 of `GRAMMAR.md` §8
   at the same time.

Until one of those lands, an arc profile has no decoder and no donor, and Kit should keep saying so.

## 7. Tools

```
.rescratch/arc/
  ARC.md                    this document
  classes.py  classes.txt   class-definition inventory per prefix, all 110 parts
  pick.py     pick.txt      arc-bearing parts by lane size
  markers.py                entity-record dump via native._parse_markers
  firstobjects.py           hex + float64 dump of the first object of a named class
  groups.py   groups.txt    trailer (role, class) histogram and equal-radius group census
  radii.py    radii.txt     KeyWords radial/diametral dimensions vs 17-degree circle groups
  scan_radius_doubles.py    radius values searched as float64 across the whole lane
  probe_arcs2.txt           group-shape census from the pre-existing .rescratch/probe_arcs2.py
```
