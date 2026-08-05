# SOLIDWORKS revolve — `Contents/Config-0-ResolvedFeatures` field map

Static corpus analysis only. **SOLIDWORKS was never launched**; no COM, no `tests/oracle`, no
debugger. The independent ground truth is `swXmlContents/KeyWords`, which is plain XML in every
part and carries the feature id, the feature name and the revolve angle.

Corpus: **111 `.SLDPRT`** under `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024` (57 parts),
`examples/Random/**` (53 parts) and `examples/.SLDPRT` (1 part). **40 parts** contain revolves,
**67 revolve features** in total (**39** revolved bosses, **28** revolved cuts).

Everything here builds on `.rescratch/grammar/GRAMMAR.md`, `.rescratch/corpus/REPORT.md` (report 1)
and `.rescratch/corpus2/REPORT.md` (report 2) and does not restate them.

Reproduce with `uv run python .rescratch/revolve/probe_revolve.py`; it writes
`.rescratch/revolve/inventory.json`. The intermediate `scan_*.py` scripts and their `*.txt`
outputs in this directory are the working evidence.

---

## 0. Summary

| finding | status |
|---|---|
| revolves and revolved cuts share the generic tree flag word `0x40000000` — there is **no** distinct revolve flag | **CONFIRMED**, 67/67 |
| the revolve angle is a `D1` dimension-scalar record holding a `float64` in **RADIANS** | **CONFIRMED**, 67/67 against `KeyWords` |
| the angle has exactly **3** copies, at scalar `+{0, +513, +537}`, all same-signed | **CONFIRMED**, 67/67 byte-exact |
| the authored angle sits at `moAngleParameter_c` marker `+56` = record data `+32` | **CONFIRMED**, 19/19 first instances |
| `moRevEndSpec_c` is a 52-byte **constant** across the whole corpus, so the end-condition code and the reverse flag cannot be located | **OPAQUE** — needs SOLIDWORKS authoring |
| the extrude anchors (scalar−824/−818, scalar−721/−715) do **not** transfer to revolves | **CONFIRMED** as not applicable |
| the axis source is a `<u32 feature id><u32 time_t>` pair at `end-spec-object − 145` (sketch) or `− 131` (reference axis) | **CONFIRMED**, 56 + 11 = 67/67 |
| *which* entity inside the sketch is the centerline | **OPAQUE** |
| `moRevolution_c` and `moRevCut_c` are genuinely distinct classes; boss ↔ cut changes the class set | **CONFIRMED** |
| revolve profiles use the same sketch-coordinate record as extrudes, but the role/class trailer takes undecoded values and the 17° circle rule does not generalise | **PARTIAL** |
| every revolve part in the corpus is `swVersion` 13000 or 14000, never 18000 | **CONFIRMED** — see §9 |

---

## 1. The `KeyWords` oracle

A revolve is **not** an `<Extrusion>` element. It is a `<Feature>` with `Type="Revolve"` or
`Type="Cut-Revolve"`:

```xml
<Feature id="144" Name="Revolve1" Type="Revolve"><Dimension Name="D1">360°</Dimension></Feature>
```

* `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/10MM x 20MM x 13MM head 316 Stainless Steel Socket Head Screw.SLDPRT`
  carries `Revolve1` id 144 and `Revolve2` id 256, both `360°`.
* `examples/Random/Addons/Idle_pulley.SLDPRT` carries `Revolve1` id 50, `360.00°`.

Localisation affects the `Name` only (`Revolución1`, `Cortar-Revolución1`); `Type` stays English.
The angle text always ends in `°` and is written either `360°` or `360.00°`, so a reader must strip
the degree sign and tolerate both forms. `swXmlContents/Features` carries no revolve data at all —
only the document/configuration header — and `docProps/*.xml` carries none either.

**Every revolve in the corpus is 360°.** That is the single biggest limitation of this work: with no
angle variation, anything that could only be pinned by varying the angle stays unpinned. What *can*
be pinned is the absolute value, because 2π and 360.0 are trivially distinguishable as `float64`.

---

## 2. Tree-flag word — CONFIRMED, and it refutes a distinct revolve flag

Every revolve tree node is the ordinary tree-node name record of GRAMMAR.md §4:

```
<u16 class-ref> ff fe ff <u8 units> <utf16le name> 00 00 00 00 <u32 flags> <u32 feature id>
```

Across all 67 revolve features the flags word at `name_text_end + 4` is **`0x40000000`, with no
exceptions** (`inventory.json` → `summary.distinct_tree_flags`), and the id at `name_text_end + 8`
equals the `KeyWords` `id` in **67/67**.

Compare the extrudes in the same corpus (`.rescratch/v8/flagmap.txt`): boss `0xC0000140`,
cut `0xC00201CA`. Masked with `0x7FFFFFFF` those are `0x40000140` and `0x400201CA`.

So the brief's suspicion is **confirmed, not refuted**: a revolve gets the same masked flag word as
a folder or a sketch. Two consequences:

1. The flags word cannot classify a revolve, and it cannot distinguish a revolved boss from a
   revolved cut. The class set (§6) and the name string are the only signals.
2. `0x40000000` is `resolved.SKETCH_FLAGS`, so the existing reader silently treats every revolve
   node as a *sketch*. See §8 defect 1.

Observed but not load-bearing: the `0x80000000` UI-expanded bit is **clear** on every revolve node
while it is set on the extrude nodes in the same parts. GRAMMAR.md §4.1 already establishes that
bit as UI state with no geometry meaning, so this is a coincidence of how these documents were
saved, not a field.

---

## 3. The angle — CONFIRMED

### 3.1 It is a dimension-scalar record, in radians

The revolve angle uses exactly the mechanism report 2 §6.2 established for extrude depth: a name
record whose text is followed **immediately** by the 22-byte `DIMENSION_SCALAR_HEADERS[0]`
(`0000000000000040 ffffffff 00000000 fffeff 000000`), then the value as a little-endian `float64`.
The scalar is named **`D1`** in 67/67 cases.

The value is in **RADIANS**, not degrees and not the metres-like scaling the extrude depth uses:

| part | lane offset | raw `float64` | `degrees(raw)` | `KeyWords` |
|---|---|---|---|---|
| `examples/Random/Addons/Idle_pulley.SLDPRT` | **8608** | `6.2831853071796` | 360.000000 | `360.00°` |
| `examples/Random/Addons/Belt_tensioner.SLDPRT` | **33761** | `6.2831853071796` | 360.000000 | `360.00°` |

`degrees(raw)` equals the `KeyWords` angle in **67/67** features
(`summary.angle_matches_keywords`). An exhaustive byte-aligned `float64` scan of every lane found
**zero** occurrences of `360.0` anywhere, and 2π instead. The stored value is `6.2831853071796`,
which is 2π rounded to 14 significant figures, i.e. SOLIDWORKS re-derives it from the decimal
degree value rather than from a `float64` 2π constant. A reader must therefore compare with a
tolerance, not for bit equality.

`AUTHORED`. This is the parameter.

### 3.2 Location: `moAngleParameter_c` marker + 56

For the first (class-marked) instance of `moAngleParameter_c` the value offset minus the marker
offset is **56** in **19/19** cases (`summary.angle_marker_relative_first_instance`). That is
record-data-start `+32`, exactly parallel to the extrude depth at `moLengthParameter_c` marker `+57`
= data `+32`; the one-byte difference is only the class-name length (`moAngleParameter_c` is 18
characters, `moLengthParameter_c` is 19).

Record layout, from `examples/Random/Addons/Idle_pulley.SLDPRT` marker **8552**, record span 1084
bytes (full hex dump in `.rescratch/revolve/angleparam.txt`):

```
+0    ff ff 01 00                 wNewClassTag + schema 1
+4    12 00                       class-name length 18
+6    "moAngleParameter_c"
+24   04 80                       class reference to the string-handle class
+26   ff fe ff 02                 unicode string tag, 2 units
+30   "D1"                        UTF-16LE
+34   <22-byte DIMENSION_SCALAR_HEADERS[0]>
+56   float64                     AUTHORED angle, RADIANS
+64   ...                         annotation witness geometry, metres, plus flags
+569  float64                     DERIVED angle copy 1   (= scalar +513)
+593  float64                     DERIVED angle copy 2   (= scalar +537)
```

As in report 2 §6.4, marker-relative addressing only works for the first instance. Later revolves
have no `moAngleParameter_c` marker; for them the correct locator is the ordinal position among
dimension-scalar records, taking the first scalar after the revolve's tree node. That rule produced
a scalar for **67/67** features with zero misses.

### 3.3 Exactly three copies: scalar + {0, +513, +537}

All three hold the **same signed value** (no sign flips, unlike the extrude's `(+,+,−,−,+,+)`).
Verified byte-exact in **67/67** features (`summary.angle_copy_check.angle_copies_verified`, zero
failures). The `+513`/`+537` pair is 24 bytes apart, exactly like the extrude's `+560`/`+584` pair,
and both copies fall inside the same `moAngleParameter_c` object.

There is no fourth copy: in **37 of 40** parts the total number of 2π `float64` in the entire lane
equals exactly `3 × revolve count`. The three exceptions (`CUBIERTA.SLDPRT` 12 vs 9,
`RUEDA DE TURBINA.SLDPRT` 13 vs 9, `TURBINA.SLDPRT` 10 vs 9) carry extra unrelated 2π values —
those parts also contain full-circle circular patterns — so counting 2π is not a locator, but the
scalar-record rule is.

`+513` and `+537` are **DERIVED CACHE**: the angular annotation's own geometry. Per the measured
extrude rule in GRAMMAR.md §6, a stale derived cache is safe and a wrong one is not, so a writer
that changes the angle should leave both copies alone until they have been characterised against a
non-360° revolve.

### 3.4 Annotation classes

`moDisplayAngularDim_c` occurs in **36 of 40** revolve parts and `moDisplayRevolveDim_c` in
**19 of 40**. `moDisplayRevolveDim_c` is therefore optional and its absence does not affect the
angle scalar. Both are **DERIVED CACHE**. In 22 of 40 parts the class defined immediately after
the `moRevEndSpec_c` record is `moDisplayAngularDim_c`, which is how the end-spec record's exact
72-byte extent was established.

---

## 4. `moRevEndSpec_c` — a constant record; end condition and direction are OPAQUE

### 4.1 The record

```
ff ff 01 00  0e 00  "moRevEndSpec_c"          20-byte class definition (first instance only)
01 00 00 00                                   u32 = 1
00 × 24
7b 14 ae 47 e1 7a 84 3f                       float64 0.01   (= 10 mm)
7b 14 ae 47 e1 7a 84 3f                       float64 0.01   (= 10 mm)
00 × 8
```

52 data bytes; 72 bytes total for the first instance, 54 for later instances (a 2-byte class
reference plus the same 52 data bytes).

**These 52 bytes are byte-identical in all 40 parts and all 67 objects.** Verified by hashing a
96-byte window at every `moRevEndSpec_c` class marker: the 17 distinct windows differ only from
byte 72 onward, i.e. in the *next* object (`.rescratch/revolve/endspec.txt`).

### 4.2 What that means, stated plainly

Because the record never varies, **no end-condition code byte and no direction/reverse flag can be
located by differential analysis.** The corpus exercises exactly one revolve configuration:
full 360°, one direction, no thin feature. Candidates, all **UNVERIFIED**:

* the `u32 = 1` at data `+0` could be the end-condition or the revolve-type code;
* the two `float64 = 0.01` at data `+28` and `+36` look like a thin-feature / second-direction
  thickness default of 10 mm.

The extrude anchoring does **not** transfer. For the extrude, the flag bytes sit at a fixed
distance from the depth scalar (report 2 §6.3: scalar−824/−818 for feature 1, scalar−721/−715
later). For revolves the distance from the end-spec object to the angle scalar takes **12 distinct
values** across the corpus — 603, 617, 641, 664, 688, 751, 755, 765, 769, 775, 785, 794, 814, 816,
840, 860 (`.rescratch/revolve/anchor.txt`) — so there is no fixed anchor in either direction. Do
not port the extrude constants.

Closing this gap needs SOLIDWORKS-side authoring of a small differential family: a 90° revolve, a
270° revolve, a reversed revolve, a mid-plane / two-direction revolve, and a thin-feature revolve.
That is exactly the verification run to schedule.

### 4.3 The one thing the record is good for: a locator

Searching the lane for the 52-byte constant enumerates the revolve end-spec objects, **including
the unmarked later instances**. The count equals the revolve count in **40/40 parts with zero
mismatches** (`probe_revolve.py`, `end_spec_objects`). This is the revolve equivalent of report 2
§6.2's ordinal-scalar trick, and everything in §5 is anchored on it.

Distinguishing the first instance from a later one is exact, not heuristic: if the 20 bytes
preceding the data are the literal class definition `ff ff 01 00 0e 00 "moRevEndSpec_c"`, the object
token is `data − 20`; otherwise it is `data − 2` (a class reference).

---

## 5. The axis of revolution — CONFIRMED as a reference, OPAQUE as a definition

Anchor: `token` = the start of the `moRevEndSpec_c` object as defined in §4.3.

Two **mutually exclusive** slots, each holding a `<u32 feature id><u32 unix time_t>` pair:

| slot | referenced node | count | meaning |
|---|---|---|---|
| `token − 145` | a **sketch** tree node | **56** of 67 | the axis is a construction line inside that sketch |
| `token − 131` | a **reference-axis** tree node (`Eje`/`Axis`, flags `0xC0000000`) | **11** of 67 | the axis is a reference-axis feature |

56 + 11 = 67. Every revolve matches exactly one slot; none matches both; none matches neither
(`summary.axis_kinds`). The two offsets are 18 bytes apart, and 18 is the size difference between
the two sub-object encodings — the same "first instance carries the class declaration" effect
GRAMMAR.md §2.1 describes.

Evidence:

* `examples/Random/Addons/Idle_pulley.SLDPRT` — end-spec data at 7920, first instance, token 7900.
  At **7755** (= token − 145): `1a 00 00 00` = 26 = the id of tree node `Sketch1`, followed by
  `be 0f b9 61` = `time_t` 1639387582. This part has no reference axis at all.
* `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/RUEDA DE TURBINA.SLDPRT` — three revolve
  objects at 69165 (first instance, token 69145), 138859 (token 138857) and 177564 (token 177562).
  At **69014**, **138726** and **177431** (each = token − 131): `2e 00 00 00` = 46 = the id of tree
  node `Eje1`, each followed by `time_t` 0x5c39a692.
* `examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/CUBIERTA.SLDPRT` is the mixed case:
  `Cortar-Revolución1` uses the sketch slot, `Cortar-Revolución2` and `Cortar-Revolución3` use the
  reference-axis slot (`Eje1`, id 193).

### 5.1 What is authorable and what is not

* **Authorable / patchable:** the `u32` id itself. Repointing a revolve at a *different existing*
  reference axis or a *different existing* sketch is a 4-byte write at a locatable offset. The
  companion `time_t` is the same "any plausible value works" field GRAMMAR.md §3.1 documents.
* **Not authorable:** *which* entity inside the referenced sketch is the centerline. That is an
  intra-sketch entity reference and nothing in this analysis reaches it. A writer can only inherit
  the donor's choice.
* **Not authorable:** the geometry of the axis when it comes from a face. `moSurfaceAxisData_c`
  (7 of 40 revolve parts) is "axis from a cylindrical face" definition data belonging to the axis
  *feature*, and the face reference behind it is opaque in exactly the way report 2 §3/§7
  established for extrude face supports. `moTwoPtsAxisData_c` (1 part) is "axis through two
  points". `moRefAxis_c` (10 parts) is the reference-axis tree feature itself and
  `moCompRefAxis_c` (10 parts) its component wrapper.
* **Not used by any revolve in this corpus:** a temporary or principal axis. `moTempAxisRef_w`
  occurs in 26 of the 40 revolve parts but never at either slot; it belongs to the circular
  patterns those parts also contain. So the "revolve about a temporary axis" case is
  **unrepresented**, not decoded.

---

## 6. `moRevolution_c` vs `moRevCut_c` — genuinely distinct classes

This is the sharpest structural difference from the extrude, and it is unambiguous.

| | parts (of the 40 revolve parts) |
|---|---|
| `moRevolution_c` present | **30** |
| `moRevCut_c` present | **17** |
| `moRevolution_c` only | **23** |
| `moRevCut_c` only | **10** |
| both present | **7** |

23 + 10 + 7 = 40. Restricted to the V8 production corpus alone (17 of its 57 parts contain
revolves) the counts are `moRevolution_c` in 11 parts and `moRevCut_c` in 11 parts, matching the
brief exactly.

All ten parts carrying only `moRevCut_c` and no `moRevolution_c` —
`PISTÓN.SLDPRT`, `Engine_Block.SLDPRT`, `Journal_bearig_crank.SLDPRT`,
`Journal_bearig_conrod.SLDPRT`, `Journal_bearig_camshaft.SLDPRT`, `CUBIERTA.SLDPRT`,
`CUBIERTA DE TURBINA 1.SLDPRT`, `CUIETA DE ENTRADA DE GASES.SLDPRT`,
`TAPA RECTANGULAR DE LA CUBIERTA DE LA TURBINA.SLDPRT`,
`TORNILLO CABEZA HEXAGONAL_RODAMIENTO.SLDPRT` — contain only revolved cuts, and the 23 parts
carrying only `moRevolution_c` (`Idle_pulley.SLDPRT`, the four `ARBOL DE LEVAS DE …` camshafts,
`Water_pump.SLDPRT`, `Camshaft.SLDPRT`, …) contain only revolved bosses. The class present tracks
the operation.

Contrast the extrude: there is no `moCut_c` anywhere in any corpus (report 2 §7.1), feature 1 is
always `moExtrusion_c` and features 2+ are always `moICE_c` regardless of boss or cut, and the
operation lives in an opaque flags word inside the body.

**Stated explicitly, because it drives the donor design:** boss ↔ cut for a revolve changes the
class set, therefore it changes the class-definition sequence, therefore it changes every
`su_CArchive` map index after the insertion point (GRAMMAR.md §2.3). **A revolved boss and a
revolved cut need separate donors. There is no byte flip between them.**

One honest caveat: I did not find a per-feature operation code. In a part that contains *both*
classes, the class table alone cannot tell you which class a given unmarked revolve object belongs
to. Attribution has to come from the tree-node name (`Revolve*` / `Revolución*` versus
`Cut-Revolve*` / `Cortar-Revolución*`), which is also the only signal `KeyWords` offers, via `Type`.

---

## 7. The profile sketch — PARTIAL

### 7.1 The record is the same

The 18-byte prefix `000000000000f03f00000000000000001e00`, `float64 x`, `float64 y` in **metres**,
then a 4-byte trailer, is present and decodes correctly in the revolve parts.
`resolved.sketch_coordinates` enumerates them without modification:
`Timing_belt_roller.SLDPRT` 16 records, `Journal_bearig_camshaft.SLDPRT` 29,
`Cylinder_head.SLDPRT` 482, `Engine_Block.SLDPRT` 994 (`.rescratch/revolve/versions.txt`).

Assigning each coordinate to the last sketch tree node before it partitions them per sketch, as
report 2 §6.4 found.

### 7.2 Three ways the extrude profile rules do **not** carry over

1. **The role/class trailer takes undecoded values.** Report 1/2 only established
   `role 0` = free point, `role 2` = point on a curve, `class 2` = point. Revolve profiles use
   `role` ∈ {0, 6, 8, 14, 24, 29} and `class` ∈ {0, 1, 2, 3, 5}
   (`.rescratch/revolve/refs.txt`, `profile point shapes`). Those extra values are **not decoded**.
2. **The rectangle corner order is not applicable.** No revolve profile in the corpus is a
   rectangle; they are production profiles of 5 to 38 coordinate records with lines, arcs and
   dimensions.
3. **The "circle = centre + a point at exactly 17°" rule does not generalise.**
   `resolved.sketch_arcs()`, which requires that 17° start angle, returns **0 arcs** in every
   revolve part tested, including `Journal_bearig_camshaft.SLDPRT` which does contain `sgArcHandle`
   records. 17° is an artefact of COM `CreateCircleByRadius`, not a property of the format. Arcs in
   a production revolve profile are therefore **unreadable** by the current arc decoder.

### 7.3 Two parts have no sketch geometry in this lane at all

`examples/Random/Addons/Idle_pulley.SLDPRT` and
`examples/Random/Addons/Power_steering_pump_pulley.SLDPRT` contain `moProfileFeature_c`,
`moSketchChain_c` and a `Sketch1` tree node, but **zero** sketch-coordinate records and **zero**
`sg*` geometry classes in `Contents/Config-0-ResolvedFeatures`. Whatever holds their sketch
geometry, it is not this lane. Several other parts are close to that state
(`10MM …Socket Head Screw.SLDPRT` has 29 coordinates but 0 `sg*` classes; the 6MM and 8MM screws
and `Spark_plug.SLDPRT` have 1). Any donor candidate must be screened for this.

---

## 8. Read-path defects in `decode_native_model` — not fixed, `src/` is another agent's

Full write-up with per-feature evidence in **`DECODER_DEFECTS.md`**; this is the summary.

Measured by `probe_revolve.py`, which runs `decode_native_model` on all 40 parts and compares each
revolve against the stream. Counters are in `inventory.json` → `decoder.counters`; the 54 itemised
findings are in `decoder.findings`.

**Defect 1 — `locate_features` drops every revolve. 67/67.**
`resolved.feature_kind(0x40000000)` returns `None` because `FEATURE_KIND_BY_FLAGS` has no revolve
entry, so `locate_features` never yields a revolve (`locate-features-drops-revolve: 67`,
`feature-kind-returns-none: 67`). Worse than a miss: `0x40000000` **is** `SKETCH_FLAGS`, so each
revolve node lands in the `profiles` list and `_last_node_in_range` can hand a revolve node to a
following extrude as that extrude's sketch. Parts that mix revolves and extrudes are the exposure:
`Cylinder_head.SLDPRT`, `Engine_Block.SLDPRT`, `VÁLVULA.SLDPRT`, `PISTÓN.SLDPRT`,
`Belt_tensioner.SLDPRT`. Since `patch_features` is built on `locate_features`, no revolve is
patchable through the public write path today.

**Defect 2 — `moRevEndSpec_c` is never read. 67/67.**
The revolve branch of `decode_native_model` hardcodes `direction_code=None` and
`termination_code=None` (`native.py`, the `_REVOLUTION_FEATURE_TYPES` block). `end-spec-not-read: 67`.
Given §4 this currently costs nothing semantic, but the record is not even located, so there is
nowhere to attach the end condition once it is decoded.

**Defect 3 — the axis is unresolved for 54 of 67 revolves.**
`_revolution_axis_marker()` returns a marker only when the *most recent* sketch contains **exactly
one** construction line, and it inspects `latest_sketch` rather than the sketch the stream actually
names. `axis-unresolved: 54`. All **11** reference-axis revolves are in that 54 and can never be
resolved by this heuristic by construction, because their axis is a reference-axis feature and not
a sketch line: `RUEDA DE TURBINA.SLDPRT` (`Cortar-Revolución1/2`, `Revolución1`),
`TURBINA.SLDPRT` (`Cortar-Revolución1`, `Revolución1/2`), `CUBIERTA.SLDPRT`
(`Cortar-Revolución2/3`), `CUBIERTA DE TURBINA 1.SLDPRT`, `CUIETA DE ENTRADA DE GASES.SLDPRT`,
`TAPA RECTANGULAR DE LA CUBIERTA DE LA TURBINA.SLDPRT`. The stream states the answer explicitly at
`token − 131` / `token − 145` (§5); the decoder does not look there. The 13 that do resolve resolve
by heuristic, and I have no static way to confirm the line it picked is the centerline.

**Defect 4 — the two derived angle copies are invisible. 67/67.**
`NativeOperation.depth_copies` is empty for every revolve (`_depth_copies` is only called on the
extrude branch), so `scalar+513` and `scalar+537` are not modelled at all
(`angle-copies-not-modelled: 67`). Leaving them stale is the correct behaviour per GRAMMAR.md §6,
but the write path cannot see them, so it cannot even assert that it left them stale.

**Defect 5 — `native_end` runs to end-of-stream for 6 of 67 revolve operations.**
`native_end=feature.native_end or len(resolved)` on the revolve branch. Harmless for reading,
wrong for slicing — the same class of defect report 1 §9.8 recorded for extrudes.

**Not a defect, recorded for accuracy.** The angle is decoded **correctly**: `angle_degrees` is
360.0 for all 67 revolves, zero `angle-missing` and zero `angle-wrong`, and `_bind_dimension`
converts the XML degrees to radians and binds them to the **correct** native scalar offset in
**67/67** (`angle-native-offset-correct: 67`). Two qualifications: the value on
`NativeOperation.angle_degrees` is sourced from `KeyWords`, not from the stream, so a part whose
`KeyWords` lacks the `<Dimension>` child would silently lose an angle the stream still holds; and
the bound native offset is exposed on `NativeFeature.dimensions`, not on `NativeOperation`, so the
operation-level view a writer would use has no angle offset. Also `profile_id` matched the
preceding sketch node in 67/67 — no defect there. Finally, `_REVOLUTION_FEATURE_TYPES` contains
`"revolution"` and `"revcut"`, which never occur; the live `KeyWords` values are `Revolve` and
`Cut-Revolve`. Dead entries, harmless.

---

## 9. Limits of this work

1. **All 67 revolves are 360°.** No angle variation, so nothing that depends on varying the angle
   is pinned: not the end-condition code, not the direction flag, not the sign rule for the two
   derived copies, not the relationship between the angle and the annotation witness geometry.
2. **`moRevEndSpec_c` is constant**, so §4's field guesses are guesses. This needs SOLIDWORKS.
3. **Every revolve part is `swVersion` 13000 (23 parts) or 14000 (17 parts).** There is **no**
   18000 revolve part in the corpus, while the extrude field map, the skeletons and the existing
   donor library are all 18000. The archive-layer grammar clearly still holds across these versions
   — every locator in this document works on both — but a legacy document is **upgraded** when
   SOLIDWORKS 2025 opens it, which rewrites the stream. See `donor_spec.md` §2.
4. **Intra-sketch entity references are opaque**, so the centerline cannot be chosen, only inherited.
5. **Revolve about a temporary/principal axis is unrepresented** in the corpus.
6. **Thin-feature, two-direction and mid-plane revolves are unrepresented.**
7. **No revolve profile is a rectangle or a COM-authored circle**, so the two profile shapes the
   extrude writer can author do not exist for revolves in this corpus.
8. Everything in GRAMMAR.md §8 still blocks adding a revolve to an arbitrary tree: object
   segmentation is unsolved, so map-index renumbering is unsolved, so feature count is bounded by
   the available donors.

## 10. Files

```
.rescratch/revolve/
  REVOLVE.md            this document
  DECODER_DEFECTS.md    the read-path bug list, with file and feature evidence
  inventory.md          the inventory, human-readable
  inventory.json        the inventory plus the decoder comparison, machine-readable
  donor_spec.md         the donor specification for donor_library.py
  probe_revolve.py      the reproducible probe: inventory + field extraction + decoder check
  make_inventory_md.py  renders inventory.md from inventory.json
  scan_inventory.py     class and name-record census over all 111 parts
  scan_keywords.py      KeyWords / Features dumps
  scan_angles.py        exhaustive float64 search for the angle in degrees and radians
  scan_summary.py       flag-word and angle-encoding summary
  scan_records.py       per-part class, tree-node and dimension-scalar tables
  scan_fields.py        per-revolve angle, copies and end-spec pairing
  scan_report.py        renders the field report
  scan_endspec.py       moRevEndSpec_c constancy proof and 2pi counting
  scan_axis.py          axis class sets and the end-spec signature locator
  scan_anchor.py        anchor-distance histograms
  scan_hex.py           annotated hex dumps around the end-spec object
  scan_refs.py          id+timestamp reference enumeration
  scan_slot.py          the axis slot partition
  scan_angleparam.py    moAngleParameter_c hex layout
  scan_profile.py       profile geometry per part
  scan_versions.py      swVersion and geometry-presence screen
  *.txt                 the outputs of the above, kept as evidence
```
