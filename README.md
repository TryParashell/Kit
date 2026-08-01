<p align="center">
  <img alt="nda" src="https://github.com/TryParashell/Kit/blob/f91eb51d6e23db26301929c273afa25a4669bfb8/files/nda.png">
</p>

# Kit

Kit is a CAD interchange SDK built for translating messy feature trees with ease. Yes, you heard that right, Kit allows you to do anything from FreeCAD to Solidworks, CATIA to Solidworks, NX to Creo and more.

## Other info

This does not import, launch, or automate SolidWorks, FreeCAD, CATIA, NX, OpenCascade, or any 3rd party application.

## Architecture

Every conversion follows one route:

```text
source file -> reader adapter -> CadDocument -> writer adapter -> destination file
```

## Supported formats:
- .SLDPRT
- .SLDASM
- .FCStd
- .FCAsm
- .CATPart
- .CATProduct
