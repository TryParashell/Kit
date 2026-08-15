# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.document.models.DocumentCaps import GetRetainedCaps, InferCaps
from interchange.document.models.DocumentError import DocumentError
from interchange.document.models.DocumentFilter import FilterDocument
from interchange.document.models.DocumentMetadata import AddWrapperMeta, GetSemanticMeta
from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentPayload import GetPayloadIds
from interchange.document.behavior.DocumentMethods import BindDocumentMut
from interchange.compatibility.PythonCompat import BindCompatMut
from interchange.compatibility.PublicMetadata import BindFunctionMut, BindNameMut
from inspect import Signature as FuncSig
from inspect import Parameter as FuncParam

BindCompatMut((CadDocument,), {__name__: globals()})
BindDocumentMut(CadDocument)

BindNameMut(
    DocumentError,
    __name__,
    "CadDocumentValidationError",
    globals(),
)

BindFunctionMut(
    FilterDocument,
    __name__,
    "filter_document",
    {
        "document": "CadDocument",
        "include_brep": "bool",
        "include_tessellation": "bool",
        "keep_payload_records": "bool",
        "return": "CadDocument",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
            FuncParam("include_brep", FuncParam.KEYWORD_ONLY, annotation="bool"),
            FuncParam(
                "include_tessellation", FuncParam.KEYWORD_ONLY, annotation="bool"
            ),
            FuncParam(
                "keep_payload_records", FuncParam.KEYWORD_ONLY, annotation="bool"
            ),
        ),
        return_annotation="CadDocument",
    ),
    globals(),
)
BindFunctionMut(
    InferCaps,
    __name__,
    "infer_capabilities",
    {
        "document": "CadDocument",
        "roundtrip_metadata": "bool",
        "return": "frozenset[Capability]",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
            FuncParam(
                "roundtrip_metadata",
                FuncParam.KEYWORD_ONLY,
                default=False,
                annotation="bool",
            ),
        ),
        return_annotation="frozenset[Capability]",
    ),
    globals(),
)
BindFunctionMut(
    GetRetainedCaps,
    __name__,
    "retained_capabilities",
    {
        "document": "CadDocument",
        "capabilities": "frozenset[Capability]",
        "include_brep": "bool",
        "include_tessellation": "bool",
        "return": "frozenset[Capability]",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
            FuncParam(
                "capabilities",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="frozenset[Capability]",
            ),
            FuncParam("include_brep", FuncParam.KEYWORD_ONLY, annotation="bool"),
            FuncParam(
                "include_tessellation", FuncParam.KEYWORD_ONLY, annotation="bool"
            ),
        ),
        return_annotation="frozenset[Capability]",
    ),
    globals(),
)
BindFunctionMut(
    GetSemanticMeta,
    __name__,
    "semantic_metadata",
    {
        "metadata": "Mapping[str, Any]",
        "return": "Mapping[str, Any]",
    },
    FuncSig(
        (
            FuncParam(
                "metadata",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="Mapping[str, Any]",
            ),
        ),
        return_annotation="Mapping[str, Any]",
    ),
    globals(),
)
BindFunctionMut(
    GetPayloadIds,
    __name__,
    "source_payload_indexes",
    {
        "document": "CadDocument",
        "return": "frozenset[int]",
    },
    FuncSig(
        (
            FuncParam(
                "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
            ),
        ),
        return_annotation="frozenset[int]",
    ),
    globals(),
)
BindFunctionMut(
    AddWrapperMeta,
    __name__,
    "with_wrapper_metadata",
    {
        "metadata": "Mapping[str, Any]",
        "keys": "Iterable[str]",
        "return": "Mapping[str, Any]",
    },
    FuncSig(
        (
            FuncParam(
                "metadata",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="Mapping[str, Any]",
            ),
            FuncParam(
                "keys",
                FuncParam.POSITIONAL_OR_KEYWORD,
                annotation="Iterable[str]",
            ),
        ),
        return_annotation="Mapping[str, Any]",
    ),
    globals(),
)

CadDocumentValidationError = DocumentError
filter_document = FilterDocument
infer_capabilities = InferCaps
retained_capabilities = GetRetainedCaps
semantic_metadata = GetSemanticMeta
source_payload_indexes = GetPayloadIds
with_wrapper_metadata = AddWrapperMeta


# document consumers need one intentional facade while implementations remain independently reviewable
__all__ = (
    "CadDocument",
    "CadDocumentValidationError",
    "filter_document",
    "infer_capabilities",
    "retained_capabilities",
    "semantic_metadata",
    "source_payload_indexes",
    "with_wrapper_metadata",
)
