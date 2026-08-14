# Real-world SOLIDWORKS corpus: ground truth

Source corpus: `Kit/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024`
57 `.SLDPRT` + 6 `.SLDASM`, authored in SOLIDWORKS 2020-2024, `swVersion="14000"`.
Census tooling: `Kit/.rescratch/census.py` -> `Kit/.rescratch/census/census.txt`, `PerFile.json`.

## 1. `swXmlContents/KeyWords` is plain XML and is the cheapest authoritative census

Every part carries a `KeyWords` stream shaped like:

```xml
<Keywords id="1602171509" Name="BIELA">
  <Configuration id="0" Name="Predeterminado" Type="ConfigurationManager" Material="..."/>
  <Extrusion id="188" Name="Saliente-Extruir2" Dissectable="true" DissectableChildren="39" DissectableRoot="true">
    <Dimension Name="D1">18</Dimension>
  </Extrusion>
  <Extrusion id="35" Name="Saliente-Extruir1" Type="Boss-Extrude">
    <Dimension Name="D1">38</Dimension>
  </Extrusion>
  <Feature id="231" Name="Chaflan1" Type="Chamfer"/>
  ...
</Keywords>
```

Consequences:

- `id` is the same feature id as the binary `Config-0-ResolvedFeatures` name record and the tree node.
- `<Dimension Name="Dn">value</Dimension>` gives the authored dimension in **millimetres as text**. This is an
  independent cross-check for every depth we decode out of the binary stream, for free, with no COM.
- `Type` is absent on some nodes (then the element tag is the type) and localised on others
  (`Feature:Direccional`, `Feature:Notas`) because the authoring UI language was Spanish. Never key behaviour
  off the localised `Name`; key off `id` + element tag + `Type` when present.

## 2. Feature-flag words: Kit's constants are wrong

`Core.py` had `BOSS_FLAGS = 0x40000140` / `CUT_FLAGS = 0x400201CA`. Across all 63 corpus files the observed
tree-node flag words are:

| flags | count | meaning |
|---|---|---|
| `0x40000000` | 1327 | folder / non-solid node |
| `0xC0000000` | 1289 | reference plane, sketch |
| `0xC0000140` | 235 | **boss extrude** |
| `0xC00201CA` | 197 | **cut extrude** |
| `0xC0000001` | 54 | fillet / chamfer |
| `0x40004003` | 16 | |
| `0x40004404` | 15 | |
| `0x400201CA` | 3 | cut extrude, bit31 clear |
| `0x40004002` | 1 | |
| `0x40000140` | 1 | boss extrude, bit31 clear |

Bit 31 (`0x80000000`) is **not** part of the feature kind — it varies for the same kind
(`0x40000140` and `0xC0000140` are both boss extrudes; `0x400201CA` and `0xC00201CA` are both cut extrudes).
Kit's constants matched only 1 boss and 3 cuts in the whole corpus, i.e. the locator missed ~99% of real
features. Mask bit 31 before classifying; keep the raw word for round-tripping.

Verified by name in `BIELA.SLDPRT`: `Saliente-Extruir1/2/3` (boss) are `0xC0000140`,
`Cortar-Extruir1/2/3` (cut) are `0xC00201CA`, `Chaflan1..4` are `0xC0000001`.

## 3. Modeling operations actually used, by file coverage

Only rows that are real modeling operations. `f` = number of distinct files containing it.

| operation | count | files | Kit support today |
|---|---|---|---|
| Sketch | 688 | 57 | rectangle profiles only |
| Extrusion (untyped) | 356 | 50 | rectangle boss only |
| Plane | 284 | 57 | Front only |
| Fillet | 86 | 32 | none |
| Boss-Extrude | 65 | 46 | rectangle, blind/midplane, Front |
| Chamfer | 56 | 30 | none |
| HoleWizard | 38 | 21 | none |
| Mirror | 36 | 16 | none |
| 3DSketch | 30 | 21 | none |
| LPattern | 23 | 6 | none |
| Cut-Extrude | 18 | 12 | none |
| CirPattern | 16 | 9 | none |
| Revolve | 15 | 11 | none |
| Cut-Revolve | 15 | 11 | none |
| Axis | 14 | 11 | none |
| LocalLPattern | 12 | 2 | none |
| Sweep | 11 | 5 | none |
| Hole Thread | 11 | 3 | none |
| Loft | 10 | 10 | none |
| Cut-Sweep | 9 | 6 | none |
| VarFillet | 9 | 5 | none |
| AdvancedHole | 6 | 4 | none |
| Shell | 5 | 4 | none |
| Cut-Loft | 5 | 5 | none |
| Helix/Spiral | 4 | 4 | none |
| Body-Delete/Keep | 3 | 3 | none |
| Sheet-Metal Master | 2 | 2 | none |
| CompCurve | 362 | 4 | none |

## 4. Resolved-stream class names worth knowing (230 distinct total)

Operation-bearing classes and their corpus counts:

`moExtrusion_c` 43, `moICE_c` 49, `Fillet_c` 31, `Chamfer_c` 28, `moHoleWzd_c` 21,
`moMirrorPattern_c` 14, `moCirPattern_c` 9, `moRevCut_c` 9, `moRevolution_c` 8,
`moBlend_c` 10 (loft), `mo3DProfileFeature_c` 24 (3D sketch), `moRefAxis_c` 11,
`moRevEndSpec_c` 14, `moHelix_c`/`moSweep_c` appear in the long tail.

Supporting classes: `moProfileFeature_c` 54, `moSketchChain_c` 53, `moEndSpec_c` 53,
`moFromEndSpec_c` 53, `moLengthParameter_c` 55, `moAngleParameter_c` 45,
`sgArcHandle` 54, `sgLineHandle` 52, `sgCircleDim` 54, `sgPointHandle` 60.

`sgArcHandle` at 54/60 files means **arc and circle sketch entities are more common than lines**.
Kit's `sketch_points` only finds the `sgPointHandle` 18-byte signature, so circular profiles currently
yield zero points.

## 5. New container generation

This corpus is `_MO_VERSION_14000` (and `_DL_VERSION_9000/11000/13000/14000`), whereas the earlier
58-file corpus was `13000`/`18000`. Container handling is unaffected (it is generation-agnostic),
which is positive evidence for the version-agnosticism claim.

Multi-configuration parts exist here: `Contents/Config-579`, `Config-962`, `Config-970` lanes
alongside `Config-0`. `Contents/Config-N-GhostPartition` (55 files) is a lane Kit does not model.

## 6. Confirmed live decoder defect

`uv run python -m pytest tests/convert/solidworks/core/SolidworksAdapterTests.py::test_entire_local_solidworks_corpus_decodes`

fails on `BIELA.SLDPRT` with:

```
sketch sldprt:sketch:39 references missing plane;  sketch sldprt:sketch:196 references missing plane;
sketch sldprt:sketch:205 references missing plane; sketch sldprt:sketch:215 references missing plane;
sketch sldprt:sketch:242 references missing plane
```

Those ids are real tree nodes (`Croquis2/3/4/5/6`). Each is sketched on a face or on `Plano1` (id 38),
not on a default reference plane, so the decoder emits a sketch whose `support_plane_id` points at a
plane it never created.

## 7. Test baseline to preserve

`uv run python -m pytest tests -q --ignore=tests/convert/formats/SwapsTests.py --ignore=tests/convert/formats/RandomAssemblyTests.py`
=> `8 failed, 808 passed, 8 skipped`. The 8:

- `ApiTests.py::test_readme_describes_default_reversible_swaps_and_strict_mode`
- `CatiaAssemblyTests.py::test_catproduct_to_embedded_fcstd_structural_roundtrip`
- `FreecadAssemblyTests.py::test_fcstd_assembly_has_component_links_placements_and_mates`
- `FreecadBrepTests.py::test_supplied_solidworks_breps_pass_only_the_proven_native_gate`
- `SolidworksTests.py::test_protocol_literals_have_one_source_definition`
- `SolidworksAdapterTests.py::test_entire_local_solidworks_corpus_decodes`  <- new, caused by this corpus
- `SolidworksAssemblyTests.py::test_assembly_capabilities_reflect_the_decoded_document`
- `SolidworksAssemblyTests.py::test_mate_list_discovery_uses_structure_when_the_stream_is_renamed`

Never let this count increase.
