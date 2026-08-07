<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

<p align="center">
  <img alt="banner" src="https://github.com/TryParashell/Kit/blob/e93626c79ab6667753f9fccfe4d7c5245cbc457b/files/banner.png">
</p>

# Kit

Kit by Parashell is a source-available CAD interchange SDK for translating geometry, feature trees, assemblies and more between proprietary formats.

## *Currently* supported CAD software

- SOLIDWORKS
- Parashell
- FreeCAD

## *Planned* (in-order)

1. Fusion360
2. CATIA
3. NX
4. Rhino
5. Creo
6. AutoCAD

## Architecture

Every conversion follows one route:

```text
source file -> reader adapter -> (ORACLE) -> writer adapter -> destination file
```

## Converting

`convert(source, destination)` reads the source, builds a `CadDocument`, and writes the destination format inferred from its suffix:

```python
from kit import convert

result = convert("bracket.SLDPRT", "bracket.FCStd")
```

The returned `ConversionResult` carries the document, the write result, and the attestation describing which capabilities survived the round trip.

### Default reversible swaps

By default a conversion is reversible.

License: Polyform Strict 1.0.0