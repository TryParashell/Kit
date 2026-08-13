# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from inspect import Signature as FuncSig

from .python_compat_methods import BindAliasMut, MakeParam


# assembly callers retain historical method reflection while canonical implementations stay compliant
def BindAssemblyMut(AssemblyType: type, MatrixType: type) -> None:
    BindAliasMut(
        AssemblyType,
        "GetDefinition",
        "definition",
        {"entity_id": "str", "return": "ComponentDefinition"},
        FuncSig(
            (MakeParam("self"), MakeParam("entity_id", AnnotValue="str")),
            return_annotation="ComponentDefinition",
        ),
    )
    BindAliasMut(
        AssemblyType,
        "GetDocument",
        "document",
        {"entity_id": "str", "return": "Any"},
        FuncSig(
            (MakeParam("self"), MakeParam("entity_id", AnnotValue="str")),
            return_annotation="Any",
        ),
    )
    BindAliasMut(
        AssemblyType,
        "GetChildren",
        "children",
        {"definition_id": "str", "return": "tuple[ComponentInstance, ...]"},
        FuncSig(
            (MakeParam("self"), MakeParam("definition_id", AnnotValue="str")),
            return_annotation="tuple[ComponentInstance, ...]",
        ),
    )
    BindAliasMut(
        MatrixType,
        "GetRows",
        "rows",
        {"return": "tuple[tuple[float, float, float, float], ...]"},
        FuncSig(
            (MakeParam("self"),),
            return_annotation="tuple[tuple[float, float, float, float], ...]",
        ),
    )
    BindAliasMut(
        MatrixType,
        "IsFinite",
        "is_finite",
        {"return": "bool"},
        FuncSig((MakeParam("self"),), return_annotation="bool"),
    )
    BindAliasMut(
        MatrixType,
        "TransformPoint",
        "transform_point",
        {
            "point": "tuple[float, float, float]",
            "return": "tuple[float, float, float]",
        },
        FuncSig(
            (
                MakeParam("self"),
                MakeParam("point", AnnotValue="tuple[float, float, float]"),
            ),
            return_annotation="tuple[float, float, float]",
        ),
    )
