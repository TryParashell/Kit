# `Core.py` findings: feature flag words and the arc/circle record

Scope: `src/convert/adapters/solidworks/resolved/Core.py` and `tests/convert/solidworks/resolved/SolidworksResolvedTests.py` only.
Evidence corpus: `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024` (57 parts, 54 with
`Contents/Config-0-ResolvedFeatures`), plus `.rescratch/corpus2` for the byte-identity round trips.

## 1. Bit 31 is not part of the feature kind

Classification is now `flags & FEATURE_FLAGS_MASK` with `FEATURE_FLAGS_MASK = 0x7FFFFFFF`, so
`0xC0000140` and `0x40000140` both classify as boss and `0xC00201CA`/`0x400201CA` both as cut.
`FeatureLayout.flags` still carries the raw word, so nothing about round-tripping changed.
`FEATURE_KIND_BY_FLAGS` keeps its name and is keyed on masked words; `feature_kind(flags)` and
`is_tree_node_flags(flags)` do the masking. Every previously exported name still exists, and
`BOSS_FLAGS`/`CUT_FLAGS`/`SKETCH_FLAGS`/`PLANE_FLAGS` keep their old values (the masked boss word *is*
`0x40000140`, so no value had to change).

## 2. What the `0x40004xxx` words are

Cross-referenced the tree-node `feature_id` of every node whose flags word has a non-zero nibble in
`0x0000F000` against the `swXmlContents/KeyWords` `id` attribute, over the whole corpus
(`.rescratch/probe_flags_arcs.py`). Result — unambiguous, zero unmatched ids:

| flags | KeyWords `Type` | count | kind assigned |
|---|---|---|---|
| `0x40004003` | `Sweep` 10, `Cut-Sweep` 6 | 16 | `sweep` |
| `0x40004002` | `Sweep` 1 | 1 | `sweep` |
| `0x40004404` | `Loft` 10, `Cut-Loft` 5 | 15 | `loft` |
| `0xC0000001` | `Chamfer` / `Fillet` | 54 | `round` |

Sample evidence: `Turbo Tube.SLDPRT` id 64/189/210 `Barrer1..3` = `Sweep`, id 234/240
`Cortar-Barrer1..2` = `Cut-Sweep`, all `0x40004003`; id 45 `Recubrir3` = `Loft` and id 48
`Cortar-Recubrir1` = `Cut-Loft`, both `0x40004404`; `RESORTE DE VÁLVULA.SLDPRT` id 45 `Barrer1` =
`Sweep` is the single `0x40004002`.

Named constants: `SWEEP_FLAGS = 0x40004003`, `SWEEP_SINGLE_PROFILE_FLAGS = 0x40004002`,
`LOFT_FLAGS = 0x40004404`, `ROUND_FLAGS = 0x40000001`.

Important limitation found: the flags word does **not** distinguish the additive from the subtractive
variant. `Sweep` and `Cut-Sweep` share `0x40004003`, `Loft` and `Cut-Loft` share `0x40004404`, so the
kinds are `sweep`/`loft` rather than `sweep`/`cut-sweep`. Add/remove has to come from another field
(unresolved, see section 5).

## 3. Depth attribution was also wrong, and is fixed

Finding the features was only half the defect. The old pairing walked a cursor over `D*` dimension
scalars and took the first one before the *next* feature, which on real files picks up the preceding
**sketch's** dimensions. On `BIELA.SLDPRT` that gave feature id 35 a depth of 158.7186 mm instead of
38 mm.

The stream is strictly ordered `sketch node → sketch geometry → feature node → feature dimension`
(verified with `.rescratch/probe_layout_order.py`). The scalar for a feature is therefore the first
`D*` scalar with `feature.offset < value_offset < next_feature.offset`. With that rule BIELA decodes:

| id | kind | decoded | `KeyWords` `<Dimension Name="D1">` |
|---|---|---|---|
| 35 | boss | 38.0 | 38 |
| 188 | boss | 18.0 | 18 |
| 204 | boss | 30.7 | 30.7 |
| 214 | cut | 46.7 | 46.7 |
| 228 | cut | 5.0 | 5 |
| 250 | cut | 9.0 | 9 |
| 231/236/253/256 | round | 2.0/1.0/1.0/2.0 | Chaflán1..4 D1 = 2/1/1/2 |

Sketch attribution changed the same way: the sketch of a feature is the last non-feature tree node
between the previous feature and this one, instead of an ordinal-indexed lookup keyed off an English
`"Sketch"` name prefix. BIELA now reports `Croquis1/2/3/4/5/6` against ids 25/39/196/205/215/242, and
the chamfers correctly report no sketch. This removes the localised-name dependency
(`SKETCH_NAME_PREFIX` is retained as a public name but no longer drives behaviour).

## 4. The arc/circle record layout

Sketch geometry in the resolved stream is a run of fixed-shape coordinate markers. Each marker is:

```
offset  size  content
-18     8     double 1.0            (weight, constant)
-10     8     double 0.0            (constant)
 -2     2     0x1e 0x00             coordinate tag
  0     8     double x, metres
  8     8     double y, metres
 16     1     role      0 = free, 2 = lies on a curve
 17     1     0
 18     1     class     2 = point, 1 = circle/arc entity
 19     1     0
```

`SKETCH_COORDINATE_PREFIX` is the 18 bytes at `-18..0`; the existing `SKETCH_POINT_PREFIX` is the same
bytes, and the existing `SKETCH_POINT_SUFFIX` (`00 00 02 00`) is exactly `role=0, class=2`, so
`sketch_points()` returns byte-for-byte the same results as before — it is now expressed as
`role == SKETCH_FREE_ROLE and geometry_class == SKETCH_POINT_CLASS`.

A circle is two consecutive markers: a centre marker, then a marker with `role == 2` and
`class == 2` whose direction from the centre is exactly 17°. That is the rule `sketch_arcs()`
implements; radius is `hypot(dx, dy)`, and the record stores no explicit radius, exactly as
`circle_radius_mm` / `circle_circumference_point_mm` already assumed. The angle test is applied with a
1e-6 degree tolerance, which is what makes the pairing self-verifying.

How it was proved:

1. `CIRCLECUT_r4.SLDPRT` vs `CIRCLECUT_r6.SLDPRT` (same model, authored radius 4 mm vs 6 mm) differ at
   only one coordinate: `0x2DC0`, decoding to (3.82522, 1.16949) and (5.73783, 1.75424) mm — 17° at
   r = 4 and r = 6. The marker at `0x2D32`, 142 bytes earlier, is (0, 0) with `class = 1`. The
   `ffff0100 0b00 "sgArcHandle"` class-name record sits immediately after that pair at `0x2DD4`.
2. `BIELA.SLDPRT` `Croquis1` (id 25) has authored `<MOD-DIAM>44.4` and `<MOD-DIAM>35.6`; the rule
   decodes r = 22.2 and r = 17.8 from the two pairs at `0x1B94/0x1C22` and `0x1DD3/0x1E61`.
   `Croquis4` (id 205, `<MOD-DIAM>9`) decodes 4.5 twice, `Croquis6` (id 242, `<MOD-DIAM>2.5`)
   decodes 1.25.
3. Corpus-wide (`.rescratch/probe_circles.py`): 487 circles across 49 of 54 parts, and 437 of the 487
   decoded radii (89.7 %) are exactly equal to an authored `<MOD-DIAM>`/`R` value in the same file.
   The remainder are undimensioned circles (radius driven by relations/patterns), not decode errors —
   they still satisfy the 17° reconstruction identity.

Write-back: `patch_sketch_arcs(data, {index: radius_mm})` and `FeatureEdit.radii_mm` both rewrite only
the rim point, as `centre + (r·cos17°, r·sin17°)` computed from the centre doubles read out of the
buffer, then re-locate and verify the radius and the arc offsets exactly as `patch_features` already
did for corners and depths. `FeatureLayout.arcs`, `FeatureLayout.radii_mm` and an arc-aware
`bounds_mm` are how a circular profile now reports usable geometry (`CIRCLECUT_r4` feature 1: 0 points,
1 arc, r = 4, bounds (-4, -4, 4, 4)).

## 5. Found but NOT fixed

- **Add vs remove for sweep and loft.** `0x40004003`/`0x40004404` are shared by the boss and cut
  variants. Kit reports `sweep`/`loft` without polarity.
- **General (non-full-circle) arcs.** Arc start/end points are also `role = 2` markers, but their
  centre is not the adjacent marker. Grouping a centre with the two following on-curve points gives
  49 candidate arcs corpus-wide and **zero** of their radii match an authored `R` dimension, so that
  pairing is wrong. Arc trim state is presumably held in the `sgArcHandle` instance body that
  references entity indices; not decoded. `sketch_arcs()` therefore emits full circles only
  (`sweep_angle_degrees == 360`), and does not invent arc endpoints.
- **9 circles with an on-curve centre.** Of 487, nine have `role = 2` on the centre marker
  (circles whose centre is constrained onto another entity, e.g. `Turbo Tube` r = 3.33/3.5). They pass
  the 17° test but have no authored dimension to confirm them. They are reported.
- **`reverse_offset` / `end_condition_offset` on authored files.** These are still fixed byte distances
  back from the depth scalar (824/818 for the first feature, 721/715 later), calibrated on Kit-written
  and `corpus2` streams. On the authored corpus the anchors do not hold, so `reversed` and
  `end_condition_code` are not trustworthy there. Untouched — recalibrating them is a separate job and
  no test depends on the authored values.
- **The sketch-support decoder defect from GROUND_TRUTH §6 is unrelated to this module** and still
  fails (`test_entire_local_solidworks_corpus_decodes`): BIELA sketches 39/196/205/215/242 sit on a
  face or on `Plano1` (id 38), and `Adapter.py`/`Native.py` emit a `support_plane_id` for a plane they
  never create. That code is owned elsewhere.
- **Multi-configuration lanes** (`Contents/Config-579/962/970`, `Config-N-GhostPartition`) are still
  ignored; only `Config-0` is located.

## 6. Verification

- `uv run python -m pytest tests/convert/solidworks/resolved/SolidworksResolvedTests.py -q` → 55 passed (was 43).
- `uv run python -m pytest tests/convert/solidworks/core/SolidworksTests.py tests/convert/solidworks/core/SolidworksWriterTests.py
  tests/convert/solidworks/core/SolidworksAdapterTests.py -q` → 2 failed, 132 passed. Both failures are the
  GROUND_TRUTH §7 baseline ones (`test_protocol_literals_have_one_source_definition`, caused by
  `Native.py` duplicating the `Contents/DisplayLists` literal, and
  `test_entire_local_solidworks_corpus_decodes`). No new failures.
- The four SOLIDWORKS-verified byte-identity round trips in `PROVEN_ROUND_TRIPS` still reproduce the
  patched artefacts byte for byte.
- `black --check` and `ruff check` clean on both files; zero comments, zero docstrings.
