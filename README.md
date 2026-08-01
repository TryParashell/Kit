# Kit

Kit is a pure-Python CAD translation SDK built around a format-neutral document graph. Readers decode native files once. Writers consume the same graph, so adding CATIA, NX, FreeCAD, or SLDPRT support does not create pairwise translators.

The first implemented path reads modern SLDPRT containers without SolidWorks and writes an editable FreeCAD document without FreeCAD. It preserves configurations, parameters, sketches, constraints, support planes, ordered feature dependencies, selections, provenance, topology metadata, and embedded Parasolid transmit data.

## Runtime boundary

The package does not import, launch, or automate SolidWorks, FreeCAD, CATIA, NX, OpenCascade, CadQuery, or another CAD application. CAD applications are used only in the development test suite as independent output verifiers.

## Outputs

- `.cadjson` stores the complete neutral document losslessly.
- `.FCStd` stores a native FreeCAD XML property graph with editable sketches and feature history.
- Embedded Parasolid partition and delta payloads are preserved byte-for-byte inside the converted artifact and can be extracted as `.x_b` files.

The direct FCStd writer marks computational objects for recomputation. FreeCAD evaluates the B-rep from the editable history when the document is opened and recomputed.

## Architecture

Every conversion follows one route:

```text
source file -> reader adapter -> CadDocument -> writer adapter -> destination file
```

The neutral model and adapter contract are documented in [docs/architecture.md](docs/architecture.md) and [docs/adapter-authoring.md](docs/adapter-authoring.md).

## Current SLDPRT replay scope

The direct decoder supports the modern compressed container, native feature names and object order, planar line and circle sketches, construction geometry, dimensional constraints, coincident reference planes, one-direction blind join and cut extrusions, terminal circular-edge fillets, configurations, and embedded Parasolid payloads. Unsupported or ambiguous replay semantics produce explicit diagnostics or a conversion error instead of guessed geometry.
