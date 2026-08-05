# Sketch arc layout in `Contents/Config-0-ResolvedFeatures` — recovered by runtime differential

Supersedes the negative result in `ARC.md` §3/§4. `ARC.md` concluded a partial arc could not be
located statically; that was correct for the static corpus, and it is now solved by COM-authoring a
differential family in SOLIDWORKS 2025 and byte-diffing the lane. No Ghidra decompilation of
`sgArc`/`sgLine` was needed.

Reproduce: `uv run python .rescratch/arc/author_arcs.py`, `author_sweep.py`, then
`find_arc_fields.py`, `layout_arcs.py`, `diff_sweep.py`, `verify_layout.py`, `check_reader.py`.

---

## 1. The differential family

Nine parts, each one boss extrusion on the Front Plane, authored with
`ISketchManager::Create3PointArc` and `AddToDB = True` (without `AddToDB`, SOLIDWORKS' auto-relation
inference silently re-solves the sketch, which is why an earlier attempt produced three parts with
identical volumes). Every part's authored volume matches the analytic expectation to <1e-6 mm³, and
the arc's centre, endpoints and radius are read back from `ISketchArc` and recorded in
`out/author_arcs.json` / `out/author_sweep.json` as ground truth.

| family | varies | fixed |
|---|---|---|
| `ARC_h20/h15/h10/h5/h0` | arc centre x (20, 15, 10, 5, 0 mm) and therefore the radius | all four profile vertices |
| `ARC_v12/v8` | the chord half-height (12, 8 mm) and therefore the radius | arc centre |
| `SWEEP_minor` / `SWEEP_major` | the sweep only (120° vs 240°) | centre, both endpoints, both vertices |

Every part's lane is exactly **10864** bytes (10268 for the `SWEEP` pair), so the records are
value-only differences and the diff is unambiguous.

## 2. The layout

An arc is **not** a self-contained record. It is:

* the arc **centre**, stored as an ordinary `GRAMMAR.md` §5.1 sketch-coordinate record — the 18-byte
  prefix `000000000000f03f00000000000000001e00`, `float64 x`, `float64 y` in metres, then the 4-byte
  trailer — whose trailer is `role = 0`, **`geometry_class = 1`**;
* the arc **endpoints**, which are not stored separately at all: they are the ordinary
  `role = 0, geometry_class = 2` profile-vertex records of the neighbouring entities.

`geometry_class = 1` is therefore the discriminator `ARC.md` §1 looked for and did not find. The
1-byte diffs `ARC.md` would have seen are exactly this: `0.01` and `0.005` differ in a single byte of
their IEEE-754 representation, so a value change here is a 1-byte run, not an 8-byte run.

**The radius is not stored.** An exhaustive `float64` search over every stream of all nine parts
finds the authored radius nowhere for `ARC_h15/h10/h5/h0/v12/v8` (`out/find_arc_fields.json`); it
appears only in `ARC_h20`, where the radius happens to equal an unrelated 10 mm value. The radius is
derived from centre-to-endpoint.

Layout, measured on `ARC_h10` (`out/layout_arcs.json`), sketch = 3 lines + 1 arc authored in chain
order:

```
6119  coord  x=  20.000  y=  10.000  role=0 class=2    line 1 start
6139  class definition  sgLineHandle
6167  class definition  sgArcHandle
6312  coord  x= -20.000  y=  10.000  role=0 class=2    line 2 start
6474  coord  x= -20.000  y= -10.000  role=0 class=2    line 3 start
6636  coord  x=  20.000  y= -10.000  role=0 class=2    arc start
6798  coord  x=  10.000  y=   0.000  role=0 class=1    ARC CENTRE
```

The `class = 2` records are the **start point of each entity in chain order**. The arc is the last
entity, so its start is the last `class = 2` record before the centre and its end is the first
`class = 2` record of that contiguous run. Verified on all nine parts, endpoints and radius exact
(`check_reader.py`: 9/9, 0 failures).

## 3. The sweep flag

`SWEEP_minor` and `SWEEP_major` share the same centre and the same two endpoints and differ only in
which of the two possible arcs is taken. Diffing their lanes (`diff_sweep.py`) leaves exactly one
semantic difference inside the sketch:

```
run 6738..6742 (4 bytes)  sgArcHandle+571   minor = 01 00 00 00   major = ff ff ff ff
```

An `i32` holding **`+1` for counter-clockwise, `-1` for clockwise**, measured from the arc's stored
start to its stored end. The two other differing runs in that region (6480, 6488) are low-order bytes
of the centre's own near-zero epsilon and carry no meaning.

**This offset is not a general locator.** `sgArcHandle+571` = `centre + 264` holds for the
1-line + 1-arc `SWEEP` topology but not for the 3-line + 1-arc `ARC_h` topology, where
`centre + 264` reads `2097151`. The flag's position depends on the entity's position in the sketch's
object chain, and pinning that needs the per-object segmentation of `.rescratch/trace/`. So the flag
is **readable in a known topology but not generally locatable**, and the writer therefore treats
handedness as **inherit-only**: it is declared on the donor from the authoring, folded into the donor
profile key (`-ccw` / `-cw`), and validated end to end by the measured volume.

## 4. What the writer does with this

`resolved.SweptArc` / `resolved.swept_arcs()` decode centre, both endpoints and the derived radius.
`FeatureEdit.swept_arc_centres_mm` writes only the **centre**; the endpoints are already written as
profile vertices by `corners_mm`, so a swept arc adds exactly one patchable point.

`_verify_features` re-reads the patched stream and rejects the patch unless
`|start − centre| == |end − centre|`. That turns any vertex-ordering mistake into a decline instead
of silently wrong geometry, which is the guard that makes the inherit-only handedness safe.

Regression evidence: `swept_arcs()` finds **zero** arcs in all 28 existing donor streams, so the
full-circle 17° path in `sketch_arcs()` is untouched. It reads real production arcs — e.g.
`Alternator.SLDPRT` r = 20 mm, `Oil pan.SLDPRT` two arcs at r = 15 mm — which the 17° rule could not
see.

## 5. Files

```
.rescratch/arc/
  ARC_LAYOUT.md          this document
  author_arcs.py         the centre/chord differential family (5 + 2 parts)
  author_sweep.py        the minor/major sweep pair
  probe_author.py        first-failure diagnosis: CreateArc vs Create3PointArc
  probe_variants.py      proves Create3PointArc + AddToDB is the working authoring path
  find_arc_fields.py     exhaustive float64 search for centre/radius/endpoints in every stream
  layout_arcs.py         annotated coordinate-record and class-record listing per part
  diff_arcs.py           lane byte diff, run + float64 report
  diff_streams.py        which container streams change per differential
  diff_sweep.py          the minor/major diff that isolates the sweep flag
  probe_direction.py     +-1 i32 census around the arc centre
  verify_layout.py       direction-offset generality check (negative: not a general locator)
  check_reader.py        resolved.swept_arcs() against the authored ground truth, 9/9
  parts/*.SLDPRT         the nine authored parts
  out/*.json             ground truth and machine-readable findings
```
