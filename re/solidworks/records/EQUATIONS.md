# `moRelMgr_c` — the equation list in `Contents/Config-0`

Read-only analysis of a licensed SOLIDWORKS 2025 install and of the `examples/` corpus. No
SOLIDWORKS binary was modified. Everything below is reproduced by
`.rescratch/eqn_layout.py`, `.rescratch/eqn_census.py` and `.rescratch/eqn_relation.py`, whose
raw output is `.rescratch/eqn_layout.txt`, `.rescratch/eqn_census.json` /
`.rescratch/eqn_census.txt` and `.rescratch/eqn_relation.txt`.

This is the read-side format that `native._parse_native_equations` scans for, described as a
record layout rather than as a scan, so it can be inverted by a writer.

---

## 1. Where the list lives

Equations live in `Contents/Config-0`, not in `Contents/Config-0-ResolvedFeatures`. The owner is
a single `moRelMgr_c` object. Its class definition is present in **108 / 108** corpus parts that
carry a `Contents/Config-0` stream, so every part has an equation manager whether or not it has
equations.

`moRelation_c` is defined in only **8 / 108** parts — exactly the parts that have at least one
equation. That is why `native._parse_native_equations` gates on
`{"moRelMgr_c", "moRelation_c"} <= class_names`: the manager alone proves nothing.

| part | `u16` at manager body `+0` | equations the reader recovers |
|---|---|---|
| `Random/Addons/Idle_pulley.SLDPRT` | 1 | 1 |
| `Random/Addons/Power_steering_pump_pulley.SLDPRT` | 1 | 1 |
| `Random/Crank/Crankshaft_bearing_cap.SLDPRT` | 1 | 1 |
| `Random/Cylinder_heads/Camshaft.SLDPRT` | 25 | 25 |
| `Random/Cylinder_heads/Spark_plug.SLDPRT` | 4 | 4 |
| `Random/Supercharger/Supercharger_housing.SLDPRT` | 3 | 3 |
| `Random/Supercharger/Throttle_housing.SLDPRT` | 6 | 6 |
| `Single Turbo …/BLOQUE V8.SLDPRT` | 1 | 1 |
| the other 100 parts | 0 | 0 |

**`count_u16 == parsed_count` in 108 / 108, zero mismatches.**

## 2. The manager record

The class definition is the ordinary `su_CArchive` form, so the body starts
`6 + len("moRelMgr_c")` = 16 bytes after the `ff ff` tag:

```
ff ff 01 00 0a 00 "moRelMgr_c"      class definition, map counter +2
u16 count                            number of relation objects that follow
count × <relation object>            the first is a class definition, the rest class references
… manager tail …
```

Measured directly. `Idle_pulley` (`Contents/Config-0` offset 3182):

```
3182  ff ff 01 00 0a 00 6d 6f 52 65 6c 4d 67 72 5f 63   ......moRelMgr_c
3198  01 00                                             count = 1
3200  ff ff 01 00 0c 00 6d 6f 52 65 6c 61 74 69 6f 6e   moRelation_c
      5f 63
```

The donor `arcboss_cut_cut_cut_through_rev` has no equations, and the same field reads zero:

```
3354  ff ff 01 00 0a 00 6d 6f 52 65 6c 4d 67 72 5f 63   ......moRelMgr_c
3370  00 00                                             count = 0
3372  00 00 ff fe ff 00 …                               manager tail, no relation object
```

Only **one** `moRelation_c` class definition exists per part no matter how many equations there
are — `Camshaft` has 25 relations and 1 definition. Relations 2..n are `0x8000|i` class
references, which is the increment rule `archive/SEGMENTATION.md` §3 records (`+2` for a
definition, `+1` for a reference).

## 3. The relation record

```
ff ff 01 00 0c 00 "moRelation_c"     (first relation only; later ones are 0x8000|i)
ff fe ff <u8 units>                  serialized string marker
<units × UTF-16LE>                   the equation source, verbatim
00                                   u8
02 00 00 00                          u32, value 2 in every relation of every part
00                                   u8
<moRelEquationSide_c object>
u16 1                                one side entry
<reference chain>                    dimension binding or global-variable binding
```

The six bytes `00 02 00 00 00 00` follow the string in **every** relation of all 8 parts. From
`.rescratch/eqn_relation.txt`, the bytes immediately after each equation string:

```
Idle_pulley       [0] '"D6@Sketch1"="D1@Sketch1"'    post 00 02 00 00 00 00 ff ff 01 00 13 00 moRelEquatio…
Spark_plug        [0] '"D8@Sketch2"="D7@Sketch2"'    post 00 02 00 00 00 00 ff ff 01 00 13 00 moRelEquatio…
Spark_plug        [1] '"D9@Sketch2"="D7@Sketch2"'    post 00 02 00 00 00 00 84 80 01 00 86 80 …
Throttle_housing  [0] '"D3@Sketch1"="D2@Sketch1"'    post 00 02 00 00 00 00 ff ff 01 00 13 00 moRelEquatio…
Camshaft          [0] '"d"= 8'                       post 00 02 00 00 00 00 ff ff 01 00 13 00 moRelEquatio…
BLOQUE V8         [0] '"1ç5"=10'                     post 00 02 00 00 00 00 ff ff 01 00 13 00 moRelEquatio…
```

`84 80` / `4c 80` / `4b 80` are the class references that replace the `moRelEquationSide_c`
definition from the second relation onwards.

### The string

`SERIALIZED_STRING_MARKER` is `ff fe ff`, then a `u8` count of UTF-16 code units, then the text.
`Idle_pulley` carries `ff fe ff 19` at offset 3218, `0x19` = 25 units, and the 50 bytes at 3222
decode to `"D6@Sketch1"="D1@Sketch1"` — 25 characters. Total span 54 bytes, which is exactly the
`ProvenanceSpan` the read path reports for `sldprt:parameter:26:D6`
(`equation:3218`, `Contents/Config-0`, offset 3218, length 54).

The grammar the reader accepts is `native._EQUATION`:
`^"([^"\r\n]+)"\s*=\s*(\S(?:.*\S)?)$`. Both forms occur in the corpus:

* **dimension equation** — LHS contains `@`: `"D6@Sketch1"="D1@Sketch1"`.
* **global variable** — LHS has no `@`: `"d"= 8`, `"r1"= 18`, `"1ç5"=10`.

The `\s*` after `=` is load bearing: `Camshaft` and `BLOQUE V8` write `"d"= 8` with a space.

### The two reference chains

The side entry binds the LHS to a real object, and the chain differs by LHS kind. Both were
observed as complete class sequences immediately after the manager:

| LHS kind | class chain after `moRelEquationSide_c` | parts |
|---|---|---|
| dimension | `moRelDimension_c` → `moDimRefWrapper_c` → `moSkDimHandleValG2_c` | `Idle_pulley`, `Spark_plug`, `Throttle_housing` |
| global variable | `moRelGlobalVar_c` → `moGlobalVarRefWrapper_c` → `moCompGlobalVar_c` (+ `moRelOperator_c`, `moRelValue_c`) | `Camshaft`, `BLOQUE V8` |

`moDimRefWrapper_c` carries the dimension's current value as a `float64` **in metres**:
`Idle_pulley` holds `7b 14 ae 47 e1 7a 74 3f` = `0.005`, and `D6@Sketch1` is 5 mm.
`Throttle_housing` relation 3 holds `ec 51 b8 1e 85 eb 91 3f` = `0.0175`.
`moSkDimHandleValG2_c` then opens with `2d 80 02 00 …`, a class reference plus a `u16` — the
persistent handle that names *which* dimension. That handle is the part a writer has to be able
to mint, and it is not yet decoded.

## 4. What this does and does not license a writer to do

Recovered and safe to rely on:

* the manager is always present, so no new folder object is needed;
* the count field is `u16` at manager body `+0`, verified 108/108;
* the equation text is an ordinary `su_CArchive` serialized string, so **rewriting an existing
  equation's text is length-agnostic** — `su_CArchive` has no absolute offsets, and replacing a
  string with one of a different length neither moves a map index nor invalidates a token;
* the per-relation trailer is the constant `00 02 00 00 00 00`.

Not recovered, and blocking a from-scratch equation writer:

* **the `moSkDimHandleValG2_c` handle.** A dimension equation is only meaningful if its side
  entry resolves to a dimension that exists in the written file. The handle body starts
  `2d 80 02 00` in every dimension-bound relation observed, but the bytes that select *which*
  dimension are not decoded, and there is no corpus pair that isolates them.
* **inserting a relation where there was none.** Adding a `moRelation_c` adds class definitions
  and objects to `Contents/Config-0`, which shifts every later map index in that stream.
  `archive/SEGMENTATION.md` §3 and `archive/MULTISTREAM.md` §2 show the renumbering is solved
  **only** for streams that have been traced under cdb; a runtime trace is required per stream,
  and `Contents/Config-0` is load-critical (`MULTISTREAM.md` §4). So growing the relation list of
  an arbitrary donor's `Config-0` statically is not currently sound.

The consequence for the write path: an equation can be carried natively today only by a donor
that already contains a relation of the right kind, whose text is then rewritten in place. A
donor with *n* spare relations supports at most *n* equations, and dimension-bound relations can
only be retargeted once the handle is decoded — global-variable relations are the tractable case,
because their LHS is a name the string itself carries.

## 5. Unresolved: the scattered duplicates in `Camshaft`

`_parse_native_equations` scans the whole stream and de-duplicates by source text. In the four
single-manager parts the recovered offsets sit in one contiguous block behind the manager. In
`Camshaft` they do not: the offsets are

```
4666, 5139, 5498, 5857, 17596, 18233, 29705, 30334, 30971, 42443, 43080, 54552, …
```

with strides alternating between ~360–640 and ~11 500. `Contents/Config-0` also holds
`moPMarkRecord_c` objects (undo snapshots), so the large strides are consistent with repeated
snapshots each carrying their own relation list. The `count_u16 == parsed_count` agreement for
`Camshaft` is therefore **not** proof that the front block holds 25 relations; it is agreement
between a count and a de-duplicated scan. A writer must not assume the manager list is the only
place an equation string appears, and must not assume the *k*-th recovered offset is the *k*-th
entry of the manager list. Resolving this needs one cdb trace of `Contents/Config-0` on
`Camshaft`, with the tooling in `re/tooling/windbg/`.
