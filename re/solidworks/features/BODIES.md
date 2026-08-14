# Multi-body FreeCAD documents and the SOLIDWORKS donor path

`donor_match` used to decline outright whenever a document built more than one solid body. That is
too blunt for `PartDesignExample.FCStd`, and too permissive would be worse. This records the
evidence the new rule is built on and the exact rule that shipped.

## 1. What the document actually holds

`probe.py` on `sandbox/sampleFiles/PartDesignExample.FCStd`:

```
bodies
  freecad:body:Body     name='Body'       tip Pocket002   PartDesign::Body object 1
  freecad:body:Body001  name='Endmill006' tip Revolution  PartDesign::Body object 79

timeline
  0 Pad         extrusion  create  sketch Sketch      deps [Sketch, Sketch, Body]
  1 Endmill005  native             -                  deps [Body001]
  2 Revolution  revolution         sketch Sketch004   deps [Sketch004, Sketch004, Body001]
  3 Stock       native             -                  deps [Model]
  4 Pocket      extrusion  cut     sketch Sketch001   deps [Sketch001, Sketch001, Pad, Body]
  5 Pocket001   extrusion  cut     sketch Sketch003   deps [Sketch003, Sketch003, Pocket, Body]
  6 Pocket002   extrusion  cut     sketch Sketch002   deps [Sketch002, Sketch002, Pocket001, Body]
  7 Clone       native             -                  deps [Pocket002]
```

So `Body` is `Pad → Pocket → Pocket001 → Pocket002`, and `Body001` is a single `Revolution` whose
profile `Sketch004` is the 2.5 mm × 50 mm silhouette of a 5 mm four-flute endmill. `Endmill005` is
the CAM tool-bit object; its `BitBody` property links `Body001`. `Stock` is the Path job stock
blank. `Clone` is a Draft clone of `Pocket002`.

## 2. The distinction, stated without reference to names

The signal is **what consumes the body**, and there are two different shapes of consumption in this
one document, which is what makes it a usable discriminator rather than a coincidence:

* `Endmill005` declares **`Body001`** — the *body object itself* — as a dependency. The body exists
  to be a tool bit. Nothing downstream treats it as part geometry.
* `Clone` declares **`Pocket002`** — a *feature* — as a dependency. It consumes a result, it does not
  own the body.

`Body` is named as a dependency only by its own solid features (`Pad`, `Pocket*` all declare
`Body`, because a PartDesign feature belongs to its Body). Those are solid features, so they are not
evidence of anything.

Hence: **a solid body is ancillary when a timeline feature that Kit already classifies as non-solid
declares that body as a dependency.** A CAM tool bit, a stock blank, or any Path/Draft artefact that
owns a whole body is caught. A clone or a Path operation that consumes a feature is not, so it
cannot demote the designed part.

## 3. The rule that shipped

In `donor_match._body_partition`:

1. Build each body's feature chain from `Body.final_feature_id` and `FeatureStep.input_feature_ids`.
   Keep the bodies whose chain holds at least one solid feature — those are the candidates.
2. **If there is fewer than two candidates, the single candidate is the model body.** No
   consumption test is applied. This is deliberate: a document with one body that some Draft or
   Path object happens to own is still that body, and refusing it would drop geometry Kit
   translates correctly today.
3. With two or more candidates, split them: ancillary if a non-solid timeline feature names the
   body, model otherwise.
4. Exactly one model body → translate its chain; every solid feature of every ancillary body is
   recorded as `unexpressed`, which the writer reports as
   `unexpressed timeline entry <name> (<kind>) building body <body>` under
   `sldprt.donor_partial`.
5. Two or more model bodies → decline `the document builds N separate solid bodies`. Two genuinely
   designed bodies are two pieces of designed geometry and Kit has no donor for that topology.
6. Zero model bodies with at least one ancillary → decline
   `every one of the N solid bodies the document builds feeds a non-model feature, so none of them
   is the part`. Better to refuse than to guess which artefact is the part.

Nothing is ever silently dropped: an ancillary body's features are named in the diagnostics, and
`vendor_loadable` is unaffected because the primary body is expressed in full.

## 4. Effect on `PartDesignExample.FCStd`

Two of the three decline reasons are gone. `Body001`/`Revolution` is recorded as unexpressed rather
than vetoing, so the revolution decline and the two-body decline both disappear, and the only
remaining reason is the arc in `Pad`'s profile:

```
sldprt.donor_declined: native SOLIDWORKS feature records were not written because
  Pad: sketch Sketch uses unsupported geometry ArcGeometry
```

Note that this is the *honest* order of events: the revolve donors exist and are wired
(`revolve_full`, `boss_revcut`), but they are `measured=False`, so had the Revolution stayed in the
primary chain it would have declined on the measurement gate instead. The multi-body rule removed it
for the right reason — a CAM tool bit is not part of the designed part — not to dodge that gate.

## 5. Tools

```
.rescratch/bodies/
  Bodies.md    this document
  probe.py     compact bodies / timeline / sketches / planes dump for an FCStd
  attrs.py     raw FreeCAD attributes carried on bodies and timeline steps
  params.py    the Parameter records a single feature owns
```
