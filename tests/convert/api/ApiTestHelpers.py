# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import ast as AstLib
from pathlib import Path as FilePath
from convert.adapters.registry.AdapterDiscovery import GetPackageItems


# package enumeration stays shared because catalog and structure tests need identical discovery scope
def ListFormatPacks() -> tuple[str, ...]:
    return tuple(
        ModuleName
        for ModuleName, IsPackage in GetPackageItems("convert.adapters")
        if IsPackage
    )


# adapter ownership mapping proves each format package contributes concrete implementations
def GetPackNames(
    AdapterValues: tuple[object, ...],
    PackageNames: tuple[str, ...],
) -> set[str]:
    return {
        PackageName
        for AdapterData in AdapterValues
        for PackageName in PackageNames
        if type(AdapterData).__module__ == PackageName
        or type(AdapterData).__module__.startswith(PackageName + ".")
    }


# api tree collection lets structure tests inspect every split composition module consistently
def ListApiTrees(RootPath: FilePath) -> tuple[tuple[FilePath, AstLib.Module], ...]:
    TreeValues: list[tuple[FilePath, AstLib.Module]] = []
    ApiFolder = RootPath / "src" / "convert"
    for SourcePath in sorted((ApiFolder / "api").glob("*.py")):
        SyntaxTree = AstLib.parse(
            SourcePath.read_text(encoding="utf-8"),
            filename=str(SourcePath),
        )
        TreeValues.append((SourcePath, SyntaxTree))
    return tuple(TreeValues)
