<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

<p align="center">
  <img alt="nda" src="https://github.com/TryParashell/Kit/blob/00c5d0b1f2dcab1a84348d39f900f9e952a7bac8/files/nda.png">
</p>

# Kit

Kit by Parashell is an internal CAD interchange SDK for translating part geometry, parametric history, sketches, configurations, assemblies, component references, transforms, mates and more through one shared document model.

## Internal use only

Kit is confidential Parashell software. Do not publish it to PyPI or distribute it outside Parashell. The package metadata includes PyPI's private-package rejection classifier as an additional safeguard.

Kit does not import, launch, or automate SOLIDWORKS, FreeCAD, CATIA, OpenCascade, or any other CAD application. Every format is read and written by parsing and serializing its container directly, so conversion runs without requiring CAD software on the machine.

## Architecture

Every conversion follows one route:

```text
source file -> reader adapter -> CadDocument -> writer adapter -> destination file
```

## Converting

`convert(source, destination)` reads the source, builds a `CadDocument`, and writes the destination format inferred from its suffix:

```python
from convert import convert

result = convert("bracket.SLDPRT", "bracket.FCStd")
```

The returned `ConversionResult` carries the document, the write result, and the attestation describing which capabilities survived the round trip.

### Default reversible swaps

By default a conversion is reversible.

### Strict mode

`strict=True` is the default. The reader rejects a document whose declared structure and decoded content disagree instead of silently degrading it. Pass `strict=False` to accept a partial decode of a damaged or unrecognized container.

### Refusing carriers

Pass `allow_carrier=False` to require a genuine native translation:

```python
convert("bracket.FCStd", "bracket.SLDPRT", allow_carrier=False)
```

The write then fails rather than falling back to embedding the source document, which is how you assert that the destination is a real parametric file in its own format.

## Supported formats

- SOLIDWORKS `.SLDPRT` and `.SLDASM`
- FreeCAD `.FCStd`
- CATIA V5 `.CATPart` and `.CATProduct`
