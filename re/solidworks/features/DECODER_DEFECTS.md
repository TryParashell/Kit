# Read-path defects: revolves in `src/convert/adapters/solidworks/`

**Nothing in `src/` was modified.** This is a defect list for the agent that owns `src/`.

Measured by `uv run python .rescratch/revolve/probe_revolve.py`, which runs
`decode_native_model(keywords, resolved, resolved_stream=lane)` on all 40 revolve-bearing corpus
parts and compares each of the 67 revolve features against the resolved-features stream. Raw
counters and the 54 itemised findings are in `inventory.json` → `decoder`.

```
angle-copies-not-modelled            67 / 67
angle-native-offset-correct          67 / 67   (not a defect)
end-spec-not-read                    67 / 67
locate-features-drops-revolve        67 / 67
feature-kind-returns-none            67 / 67
axis-unresolved                      54 / 67
native-end-is-end-of-stream           6 / 67
```

Zero `operation-missing`, zero `angle-missing`, zero `angle-wrong`, zero `profile-mismatch`.

---

## D1 — `locate_features()` drops every revolve, and mis-files it as a sketch

**Where:** `resolved.py`, `FEATURE_KIND_BY_FLAGS` / `feature_kind()` / `locate_features()`.

`feature_kind(0x40000000)` returns `None`, because the map has entries for extrude boss
(`0x40000140`), extrude cut (`0x400201CA`), fillet, sweep and loft, but nothing for a revolve.
Every revolve tree node in the corpus carries flags `0x40000000` (67/67, `REVOLVE.md` §2), so
`locate_features()` yields no revolve at all: `locate-features-drops-revolve: 67`,
`feature-kind-returns-none: 67`.

The second-order effect is worse than the miss. `0x40000000` **is** `SKETCH_FLAGS`, and
`is_tree_node_flags()` accepts it, so each revolve node is admitted to the tree and then sorted into
the `profiles` list. `_last_node_in_range()` picks the last profile node before a feature, so in a
part where a revolve precedes an extrude, the extrude gets the **revolve's** node handed to it as
its sketch, and `_points_in_range` / `_arcs_in_range` then collect the wrong coordinate span.

Exposed parts (revolves and extrudes in the same lane): `examples/Random/Cylinder_heads/Cylinder_head.SLDPRT`,
`examples/Random/Engine_Block.SLDPRT`, `examples/Random/Addons/Belt_tensioner.SLDPRT`,
`examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/VÁLVULA.SLDPRT`,
`examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/PISTÓN.SLDPRT`.
`Belt_tensioner.SLDPRT` is the clearest single case: tree order is `Sketch1`(26) → `Revolve1`(50,
flags `0x40000000`, node offset 31628) → `Fillet1`(68) → `Sketch2`(86) → `Boss-Extrude2`(108) → …
so the revolve node sits in the profile list between two real sketches.

Because `patch_features()` and `donor_library.patch_donor()` are both built on `locate_features()`,
**no revolve is reachable through the public write path today.**

**Not a one-line fix.** Adding `0x40000000` to `FEATURE_KIND_BY_FLAGS` would reclassify every folder
and every collapsed sketch as a revolve. The discriminator has to be the class set
(`moRevolution_c` / `moRevCut_c`) plus the tree-node name, or the `KeyWords` `Type` attribute — not
the flags word. `REVOLVE.md` §2 and §6 set out what is available.

---

## D2 — `moRevEndSpec_c` is never located or read

**Where:** `native.py`, the `_REVOLUTION_FEATURE_TYPES` branch of `decode_native_model`.

The branch constructs `NativeOperation(... direction_code=None, termination_code=None ...)`
unconditionally, and `_end_spec()` is never called for a revolve. `end-spec-not-read: 67`.

Given that `moRevEndSpec_c` is a 52-byte constant across the whole corpus (`REVOLVE.md` §4) this
costs nothing semantic *today* — there is no value to lose. It costs structurally: the record is not
even located, so there is nowhere to attach the end condition, the direction flag or the
thin-feature thickness once a SOLIDWORKS run decodes them. The locator is cheap and exact: search
for `u32 1` + 24 zero bytes + `float64 0.01` + `float64 0.01` + 8 zero bytes; the hit count equals
the revolve count in 40/40 parts with zero mismatches.

Do **not** reach for the extrude anchors here. `FIRST_FEATURE_REVERSE_DISTANCE = 824` etc. are
depth-scalar-relative and the revolve's angle-scalar-to-end-spec distance takes 12 distinct values
across the corpus (`REVOLVE.md` §4.2).

---

## D3 — the axis is unresolved for 54 of 67 revolves, and unresolvable for 11 by construction

**Where:** `native.py`, `_revolution_axis_marker()` and its caller.

```python
def _revolution_axis_marker(sketch: NativeSketch | None) -> NativeMarker | None:
    ...
    return candidates[0] if len(candidates) == 1 else None
```

Two problems. It only accepts a sketch that contains **exactly one** construction line
(`profile_role == 2`, `semantic == "line"`), so any profile sketch with a second construction line
returns `None`; and it is passed `latest_sketch`, the most recently decoded sketch, rather than the
sketch the stream actually names as the axis source.

Result: `axis_marker_offset is None` for **54 of 67** revolves (`axis-unresolved: 54`).

The **11** reference-axis revolves are all inside that 54 and can never be resolved by this
heuristic, because their axis is a reference-axis *feature*, not a sketch line:

| part | feature | axis node | id | axis-id offset | end-spec object |
|---|---|---|---|---|---|
| `RUEDA DE TURBINA.SLDPRT` | `Cortar-Revolución1` | `Eje1` | 46 | 69014 | 69145 |
| `RUEDA DE TURBINA.SLDPRT` | `Cortar-Revolución2` | `Eje1` | 46 | 138726 | 138857 |
| `RUEDA DE TURBINA.SLDPRT` | `Revolución1` | `Eje1` | 46 | 177431 | 177562 |
| `TURBINA.SLDPRT` | `Cortar-Revolución1` | `Eje1` | 52 | 110732 | 110863 |
| `TURBINA.SLDPRT` | `Revolución1` | `Eje1` | 52 | 202812 | 202943 |
| `TURBINA.SLDPRT` | `Revolución2` | `Eje1` | 52 | 227262 | 227393 |
| `CUBIERTA.SLDPRT` | `Cortar-Revolución2` | `Eje1` | 193 | 156117 | 156248 |
| `CUBIERTA.SLDPRT` | `Cortar-Revolución3` | `Eje1` | 193 | 300319 | 300450 |
| `CUBIERTA DE TURBINA 1.SLDPRT` | `Cortar-Revolución1` | `Eje1` | 205 | 148763 | 148894 |
| `CUIETA DE ENTRADA DE GASES.SLDPRT` | `Cortar-Revolución1` | `Eje1` | 205 | 148810 | 148941 |
| `TAPA RECTANGULAR DE LA CUBIERTA DE LA TURBINA.SLDPRT` | `Cortar-Revolución1` | `Eje1` | 205 | 149372 | 149503 |

All eleven are V8 parts, lane `Contents/Config-0-ResolvedFeatures`, and every axis-id offset is
exactly `end-spec object − 131`. The per-feature offsets for all 67 revolves are in `inventory.md`.

The stream states the answer explicitly, and the decoder does not look there. Per `REVOLVE.md` §5:
a `<u32 feature id><u32 time_t>` pair at `end-spec-object − 145` names a **sketch** (56/67) and at
`− 131` names a **reference axis** (11/67), and the partition is exact — 56 + 11 = 67, no overlap,
no misses. Replacing the heuristic with that lookup makes the axis *source* deterministic for every
revolve in the corpus.

What it still will not give you is *which* line inside the sketch is the centerline. That is an
intra-sketch entity reference and it is opaque. Note also that the 13 revolves the current heuristic
*does* resolve are resolved by guesswork, and there is no static way to confirm the line it picked
is the centerline — so those 13 are unverified, not correct.

---

## D4 — the two derived angle copies are not modelled

**Where:** `native.py`; `_depth_copies()` is only called on the extrude branch.

`NativeOperation.depth_copies` is empty for all 67 revolves
(`angle-copies-not-modelled: 67`). The angle has exactly three copies at `scalar + {0, +513, +537}`,
verified byte-exact in 67/67 (`REVOLVE.md` §3.3).

Leaving `+513` and `+537` stale is the **correct** behaviour per the measured extrude rule in
GRAMMAR.md §6 — a stale derived cache is safe, a wrong one is not. The defect is that the write path
cannot see them, so it cannot assert that it left them stale, and it has no place to put the sign
rule once a non-360° revolve exists to derive it from.

---

## D5 — `native_end` runs to end-of-stream for 6 of 67 revolve operations

**Where:** `native.py`, revolve branch: `native_end=feature.native_end or len(resolved)`.

`native-end-is-end-of-stream: 6`. Harmless for reading, wrong for slicing — the same class of defect
report 1 §9.8 recorded for the extrude operation. `native_offset` was never found to be past the
revolve's own end-spec object (`native-offset-after-end-spec: 0`), so only the upper bound is wrong.

---

## Correct behaviour, recorded so nobody "fixes" it

* **The angle is right.** `NativeOperation.angle_degrees` is 360.0 for all 67 revolves; zero
  `angle-missing`, zero `angle-wrong`.
* **`_bind_dimension` is right.** It converts the `KeyWords` degrees to radians and binds them to
  the **correct** native scalar offset in **67/67** (`angle-native-offset-correct: 67`). This is the
  one place the revolve read path already agrees with the stream byte for byte.
* **`profile_id` is right.** It matched the sketch tree node immediately preceding the revolve in
  67/67 (`profile-mismatch: 0`).

Two qualifications on the angle, both real but neither a bug today:

1. `NativeOperation.angle_degrees` is sourced from `KeyWords`, not from the stream. A part whose
   `KeyWords` lacks the `<Dimension Name="D1">` child would silently lose an angle the stream still
   holds at a known offset.
2. The bound native offset lives on `NativeFeature.dimensions`, not on `NativeOperation`. The
   operation-level view — the one a writer would use — has no angle offset and no angle copies, so
   a revolve write path cannot be built on `NativeOperation` as it stands.

Finally, cosmetic: `_REVOLUTION_FEATURE_TYPES = {"revolve", "revolution", "cut-revolve", "revcut"}`
contains two entries that never occur. The live `KeyWords` `Type` values in the whole corpus are
exactly `Revolve` and `Cut-Revolve`.
