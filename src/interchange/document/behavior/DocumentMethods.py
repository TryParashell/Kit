# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from inspect import Parameter as FuncParam
from typing import Mapping as TypeMap
from typing import TypeAlias

from interchange.document.validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.behavior.DocumentLookup import FindEntity
from interchange.compatibility.PythonCompatMethods import (
    BindAliasMut,
    BindDirectMut,
    BindStaticMut,
    CompatParam,
    MakeLegacySig,
)


# document compatibility rows share one concrete shape so empty metadata remains typed
CompatMethod: TypeAlias = tuple[
    str,
    str,
    TypeMap[str, str],
    tuple[CompatParam, ...],
    str,
]

# method contracts stay declarative because exact historical reflection spans several split behaviors
KDocumentMethods: tuple[CompatMethod, ...] = (
    ("ToMapping", "to_dict", {}, (), "dict[str, WireData]"),
    (
        "FromMapping",
        "from_dict",
        {"value": "Mapping[str, WireData]"},
        (("value", "Mapping[str, WireData]"),),
        "CadDocument",
    ),
    (
        "ToJson",
        "to_json",
        {"indent": "int | None"},
        (("indent", "int | None", 2, FuncParam.KEYWORD_ONLY),),
        "str",
    ),
    (
        "FromJson",
        "from_json",
        {"source": "str"},
        (("source", "str"),),
        "CadDocument",
    ),
    (
        "WriteJson",
        "write_json",
        {"path": "str | Path"},
        (("path", "str | Path"),),
        "Path",
    ),
    (
        "ReadJson",
        "read_json",
        {"path": "str | Path"},
        (("path", "str | Path"),),
        "CadDocument",
    ),
    ("GetErrors", "validate", {}, (), "tuple[str, ...]"),
    ("AssertValid", "assert_valid", {}, (), "None"),
    (
        "GetParameter",
        "parameter",
        {"entity_id": "str"},
        (("entity_id", "str"),),
        "Parameter",
    ),
    (
        "GetSketch",
        "sketch",
        {"entity_id": "str"},
        (("entity_id", "str"),),
        "Sketch",
    ),
    (
        "GetFeature",
        "feature",
        {"entity_id": "str"},
        (("entity_id", "str"),),
        "FeatureStep",
    ),
    (
        "GetPlane",
        "plane",
        {"entity_id": "str"},
        (("entity_id", "str"),),
        "SupportPlane",
    ),
)


# document callers retain historical methods while implementation remains split by responsibility
def BindDocumentMut(DocumentType: type) -> None:
    for (
        SourceName,
        LegacyName,
        ParamAnnots,
        ParamSpecs,
        ReturnAnnot,
    ) in KDocumentMethods:
        FirstName = (
            "cls" if SourceName in {"FromMapping", "FromJson", "ReadJson"} else "self"
        )
        AnnotMap = {**ParamAnnots, "return": ReturnAnnot}
        SignatureInfo = MakeLegacySig(
            ((FirstName,), *ParamSpecs),
            ReturnAnnot,
        )
        BindAliasMut(
            DocumentType,
            SourceName,
            LegacyName,
            AnnotMap,
            SignatureInfo,
        )
    BindDirectMut(
        DocumentType,
        GetAssemblyErrs,
        "_validate_assembly",
        {"ids": "Mapping[str, set[str]]", "return": "tuple[str, ...]"},
        MakeLegacySig(
            (("self",), ("ids", "Mapping[str, set[str]]")),
            "tuple[str, ...]",
        ),
    )
    BindStaticMut(
        DocumentType,
        FindEntity,
        "_lookup",
        {
            "items": "tuple[EntityType, ...]",
            "entity_id": "str",
            "label": "str",
            "return": "EntityType",
        },
        MakeLegacySig(
            (
                ("items", "tuple[EntityType, ...]"),
                ("entity_id", "str"),
                ("label", "str"),
            ),
            "EntityType",
        ),
    )
