# Kit

Kit is  CAD interchange SDK built for translating messy feature trees with ease. Yes, you heard that right, Kit allows you to do anything from FreeCAD to Solidworks, CATIA to Solidworks, NX to Creo and more.

## Other info

This does not import, launch, or automate SolidWorks, FreeCAD, CATIA, NX, OpenCascade, or any 3rd party application.

## Architecture

Every conversion follows one route:

```text
source file -> reader adapter -> CadDocument -> writer adapter -> destination file
```

The neutral model and adapter contract are documented in [docs/architecture.md](docs/architecture.md) and [docs/adapter-authoring.md](docs/adapter-authoring.md).

## Supported formats:
- .SLDPRT
- .SLDASM
- .FCStd
- .FCAsm
- .CATPart
- .CATProduct
