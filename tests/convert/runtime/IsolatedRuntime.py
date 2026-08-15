# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# isolated execution proves the wheel needs no cad application or external runtime hook
KIsolatedRuntime = r"""
import io
from pathlib import Path
import sys

blocked_imports = frozenset(
    {
        "FreeCAD",
        "FreeCADGui",
        "NXOpen",
        "OCC",
        "OCP",
        "Part",
        "Sketcher",
        "adsk",
        "aiohttp",
        "cadquery",
        "cffi",
        "clr",
        "comtypes",
        "ctypes",
        "ftplib",
        "httpx",
        "lxml",
        "multiprocessing",
        "numpy",
        "pycatia",
        "pythoncom",
        "requests",
        "runpy",
        "scipy",
        "socket",
        "ssl",
        "subprocess",
        "urllib",
        "urllib3",
        "websockets",
        "win32com",
    }
)


class ImportBlocker:
    def find_spec(self, fullname, path=None, target=None):
        root = fullname.partition(".")[0]
        if root in blocked_imports:
            raise RuntimeError(f"blocked runtime import: {fullname}")
        return None


def audit(event, arguments):
    blocked = (
        event == "os.system"
        or event.startswith("os.spawn")
        or event.startswith("socket.")
        or event.startswith("subprocess.")
        or event.startswith("ctypes.")
    )
    if blocked:
        raise RuntimeError(f"blocked runtime operation: {event}")


sys.meta_path.insert(0, ImportBlocker())
sys.addaudithook(audit)
sys.path.insert(0, sys.argv[1])

from convert import available_adapters, convert, open_document, write_document

root = Path(sys.argv[2])
output = Path(sys.argv[3])
adapters = {adapter.format_id for adapter in available_adapters()}
assert adapters == {
    "catia.v5",
    "freecad.fcstd",
    "interchange.json",
    "solidworks.sldprt",
}
cases = (
    (root / "examples" / ".SLDPRT" / "example.SLDPRT", ".FCStd"),
    (output / "conversion_0.FCStd", ".CATPart"),
    (root / "examples" / ".CATPart" / "Banjo.CATPart", ".SLDPRT"),
    (
        root / "examples" / "Random" / "V8_engine.FCStd",
        ".CATProduct",
    ),
    (
        root
        / "examples"
        / ".CATProduct"
        / "Brake_Pedal_Assembly - Backup 2.CATProduct",
        ".SLDASM",
    ),
)
for index, (source, suffix) in enumerate(cases):
    destination = output / f"conversion_{index}{suffix}"
    result = convert(source, destination)
    assert result.output.path == destination.resolve()
    assert result.output.bytes_written == destination.stat().st_size
    assert result.requirements == ()
    assert result.dropped == frozenset()
    assert open_document(destination).validate() == ()

source_document = open_document(cases[0][0])
buffer = io.BytesIO()
written = write_document(
    source_document,
    buffer,
    destination_format="interchange.json",
)
assert written.path is None
assert written.bytes_written == len(buffer.getvalue())
assert open_document(
    buffer.getvalue(), source_format="interchange.json"
) == source_document
"""
