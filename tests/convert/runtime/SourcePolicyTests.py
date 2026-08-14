# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import ast as AstLib

from tests.convert.runtime.RuntimeAstRules import CheckNode
from tests.convert.runtime.RuntimeRules import KSourcePath


# production imports and calls stay inside the portable offline runtime boundary
def CheckDeps() -> None:
    for SourcePath in KSourcePath.rglob("*.py"):
        SyntaxTree = AstLib.parse(
            SourcePath.read_text("utf-8"),
            filename=str(SourcePath),
        )
        for NodeData in AstLib.walk(SyntaxTree):
            CheckNode(SourcePath, NodeData)


# executable pass statements stay prohibited because production paths must never contain stubs
def CheckNoPass() -> None:
    for SourcePath in KSourcePath.rglob("*.py"):
        SourceBytes = SourcePath.read_bytes()
        SyntaxTree = AstLib.parse(SourceBytes, filename=str(SourcePath))
        assert not any(
            isinstance(NodeData, AstLib.Pass)
            for NodeData in AstLib.walk(SyntaxTree)
        ), SourcePath


# every production module retains the legal notice required by repository licensing
def CheckHeaders() -> None:
    ExpectedLines = (
        "# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0",
        "# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin",
    )
    for SourcePath in KSourcePath.rglob("*.py"):
        SourceLines = SourcePath.read_text(encoding="utf-8").splitlines()
        assert tuple(SourceLines[: len(ExpectedLines)]) == ExpectedLines, SourcePath


# wheel source stays limited to the two intentional public production packages
def CheckLayout() -> None:
    PackageNames = {
        SourcePath.name
        for SourcePath in KSourcePath.iterdir()
        if SourcePath.is_dir() and any(SourcePath.rglob("*.py"))
    }
    assert PackageNames == {"convert", "interchange"}
