<p align="center">
  <img alt="nda" src="https://github.com/TryParashell/Kit/blob/00c5d0b1f2dcab1a84348d39f900f9e952a7bac8/files/nda.png">
</p>

# Kit

Kit by Parashell is an internal CAD interchange SDK for translating part geometry, parametric history, sketches, configurations, assemblies, component references, transforms, mates and more through one shared document model.

## Internal use only

Kit is confidential Parashell software. Do not publish it to PyPI or distribute it outside Parashell. The package metadata includes PyPI's private-package rejection classifier as an additional safeguard.

Kit does not import, launch, or automate SOLIDWORKS, FreeCAD, CATIA, OpenCascade, or any other CAD application. Conversion runs without CAD software installed.

## Architecture

Every conversion follows one route:

```text
source file -> reader adapter -> CadDocument -> writer adapter -> destination file
```

## Supported formats

- SOLIDWORKS `.SLDPRT` and `.SLDASM`
- FreeCAD `.FCStd`
- CATIA V5 `.CATPart` and `.CATProduct`
