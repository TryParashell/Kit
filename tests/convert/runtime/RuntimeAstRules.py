# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import ast as AstLib
from pathlib import Path as FilePath

from tests.convert.runtime.RuntimeRules import (
    KAllowedRoots,
    KDynamicImportPath,
    KEnvAttrs,
    KForbiddenAttrs,
    KForbiddenNames,
    KForbiddenRoots,
)


# direct imports need one shared boundary check so forbidden dependencies cannot drift
def CheckImports(SourcePath: FilePath, NodeData: AstLib.AST) -> None:
    if not isinstance(NodeData, AstLib.Import):
        return
    RootNames = {AliasData.name.split(".", 1)[0] for AliasData in NodeData.names}
    assert RootNames <= KAllowedRoots, (SourcePath, RootNames - KAllowedRoots)
    assert not RootNames & KForbiddenRoots, (SourcePath, RootNames & KForbiddenRoots)


# imported symbols need separate validation because relative imports have different roots
def CheckFromImport(SourcePath: FilePath, NodeData: AstLib.AST) -> None:
    if not isinstance(NodeData, AstLib.ImportFrom) or not NodeData.module:
        return
    RootName = NodeData.module.split(".", 1)[0]
    if NodeData.level == 0:
        assert RootName in KAllowedRoots, (SourcePath, RootName)
    assert RootName not in KForbiddenRoots, (SourcePath, RootName)
    if NodeData.module == "importlib":
        for AliasData in NodeData.names:
            if AliasData.name == "import_module":
                assert SourcePath == KDynamicImportPath, SourcePath
                assert AliasData.asname == "ImportModule", SourcePath


# executable calls need syntax checks because import boundaries alone cannot block process access
def CheckCalls(SourcePath: FilePath, NodeData: AstLib.AST) -> None:
    if not isinstance(NodeData, AstLib.Call):
        return
    if isinstance(NodeData.func, AstLib.Name):
        assert NodeData.func.id not in KForbiddenNames, (SourcePath, NodeData.func.id)
        if NodeData.func.id == "import_module":
            assert SourcePath == KDynamicImportPath, SourcePath
    if isinstance(NodeData.func, AstLib.Attribute):
        assert NodeData.func.attr not in KForbiddenAttrs, (
            SourcePath,
            NodeData.func.attr,
        )


# environment access needs explicit checks because ordinary operating system imports remain allowed
def CheckEnvAccess(SourcePath: FilePath, NodeData: AstLib.AST) -> None:
    if isinstance(NodeData, AstLib.Attribute) and isinstance(
        NodeData.value, AstLib.Name
    ):
        if NodeData.value.id == "os":
            assert NodeData.attr not in KEnvAttrs, (SourcePath, NodeData.attr)
    if isinstance(NodeData, AstLib.ImportFrom) and NodeData.module == "os":
        ImportedNames = {AliasData.name for AliasData in NodeData.names}
        assert not ImportedNames & KEnvAttrs, (
            SourcePath,
            ImportedNames & KEnvAttrs,
        )


# one dispatcher keeps the production tree walk independent from individual syntax policies
def CheckNode(SourcePath: FilePath, NodeData: AstLib.AST) -> None:
    CheckImports(SourcePath, NodeData)
    CheckFromImport(SourcePath, NodeData)
    CheckCalls(SourcePath, NodeData)
    CheckEnvAccess(SourcePath, NodeData)
