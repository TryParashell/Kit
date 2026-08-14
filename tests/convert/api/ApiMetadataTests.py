# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib.metadata import distribution as GetPackage

import tomllib as TomlLib

from convert import convert as ConvertLegacy
from tests.convert.api.ApiTestPaths import KRootPath


# one sdk entry point prevents competing command surfaces from drifting apart
def CheckEntryPoint() -> None:
    EntryPoints = GetPackage("kit").entry_points
    assert [
        (ItemData.group, ItemData.name, ItemData.value) for ItemData in EntryPoints
    ] == [("kit", "convert", "convert:convert")]
    assert next(iter(EntryPoints)).load() is ConvertLegacy


# package metadata must remain private and complete because this sdk is internally distributed
def CheckMetadata() -> None:
    MetadataData = TomlLib.loads(
        (KRootPath / "pyproject.toml").read_text(encoding="utf-8")
    )
    ProjectData = MetadataData["project"]
    assert ProjectData["name"] == "kit"
    assert ProjectData["classifiers"][0] == "Private :: Do Not Upload"
    assert ProjectData["entry-points"] == {"kit": {"convert": "convert:convert"}}
    assert "scripts" not in ProjectData
    assert "gui-scripts" not in ProjectData
    assert ProjectData["license"] == "LicenseRef-PolyForm-Strict-1.0.0"
    assert ProjectData["license-files"] == ["LICENSE"]
    assert ProjectData["urls"]["Repository"] == "https://github.com/TryParashell/Kit"
    assert MetadataData["tool"]["hatch"]["build"]["targets"]["sdist"]["include"] == [
        "/LICENSE",
        "/README.md",
        "/pyproject.toml",
        "/src",
        "/uv.lock",
    ]
    ReadmeText = (KRootPath / ProjectData["readme"]).read_text(encoding="utf-8")
    for SuffixText in (".SLDPRT", ".SLDASM", ".FCStd", ".CATPart", ".CATProduct"):
        assert SuffixText in ReadmeText
    assert "Internal use only" in ReadmeText


# readme guarantees remain tested because reversible defaults and strict mode define public behavior
def CheckReadme() -> None:
    ReadmeText = (KRootPath / "README.md").read_text(encoding="utf-8")
    assert "convert(source, destination)" in ReadmeText
    assert "allow_carrier=False" in ReadmeText
    assert "without requiring CAD software" in ReadmeText
