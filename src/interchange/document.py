# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .document_caps import GetRetainedCaps, InferCaps
from .document_error import DocumentError
from .document_filter import FilterDocument
from .document_identity import GetIdFields, GetIdGroups
from .document_metadata import AddWrapperMeta, GetSemanticMeta
from .document_model import CadDocument
from .document_payload import GetPayloadIds
from .document_methods import BindDocumentMut
from .python_compat import BindCompatMut
from inspect import Signature as FuncSig
from inspect import Parameter as FuncParam

# historical defining module identity preserves direct imports and existing pickle payloads
BindCompatMut((CadDocument,), {__name__: globals()})
BindDocumentMut(CadDocument)

DocumentError.__name__ = "CadDocumentValidationError"
DocumentError.__qualname__ = "CadDocumentValidationError"
DocumentError.__module__ = __name__

globals().update(
    {
        "CadDocumentValidationError": DocumentError,
        "filter_document": FilterDocument,
        "infer_capabilities": InferCaps,
        "retained_capabilities": GetRetainedCaps,
        "semantic_metadata": GetSemanticMeta,
        "source_payload_indexes": GetPayloadIds,
        "with_wrapper_metadata": AddWrapperMeta,
    }
)

FilterDocument.__module__ = __name__
InferCaps.__module__ = __name__
GetRetainedCaps.__module__ = __name__
GetSemanticMeta.__module__ = __name__
GetPayloadIds.__module__ = __name__
AddWrapperMeta.__module__ = __name__

FilterDocument.__name__ = "filter_document"
FilterDocument.__qualname__ = "filter_document"
InferCaps.__name__ = "infer_capabilities"
InferCaps.__qualname__ = "infer_capabilities"
GetRetainedCaps.__name__ = "retained_capabilities"
GetRetainedCaps.__qualname__ = "retained_capabilities"
GetSemanticMeta.__name__ = "semantic_metadata"
GetSemanticMeta.__qualname__ = "semantic_metadata"
GetPayloadIds.__name__ = "source_payload_indexes"
GetPayloadIds.__qualname__ = "source_payload_indexes"
AddWrapperMeta.__name__ = "with_wrapper_metadata"
AddWrapperMeta.__qualname__ = "with_wrapper_metadata"

FilterDocument.__annotations__ = {
    "document": "CadDocument",
    "include_brep": "bool",
    "include_tessellation": "bool",
    "keep_payload_records": "bool",
    "return": "CadDocument",
}
InferCaps.__annotations__ = {
    "document": "CadDocument",
    "roundtrip_metadata": "bool",
    "return": "frozenset[Capability]",
}
GetRetainedCaps.__annotations__ = {
    "document": "CadDocument",
    "capabilities": "frozenset[Capability]",
    "include_brep": "bool",
    "include_tessellation": "bool",
    "return": "frozenset[Capability]",
}
GetSemanticMeta.__annotations__ = {
    "metadata": "Mapping[str, Any]",
    "return": "Mapping[str, Any]",
}
GetPayloadIds.__annotations__ = {
    "document": "CadDocument",
    "return": "frozenset[int]",
}
AddWrapperMeta.__annotations__ = {
    "metadata": "Mapping[str, Any]",
    "keys": "Iterable[str]",
    "return": "Mapping[str, Any]",
}

FilterDocument.__signature__ = FuncSig(
    (
        FuncParam(
            "document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"
        ),
        FuncParam("include_brep", FuncParam.KEYWORD_ONLY, annotation="bool"),
        FuncParam("include_tessellation", FuncParam.KEYWORD_ONLY, annotation="bool"),
        FuncParam("keep_payload_records", FuncParam.KEYWORD_ONLY, annotation="bool"),
    ),
    return_annotation="CadDocument",
)
InferCaps.__signature__ = FuncSig(
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
)
GetRetainedCaps.__signature__ = FuncSig(
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
        FuncParam("include_tessellation", FuncParam.KEYWORD_ONLY, annotation="bool"),
    ),
    return_annotation="frozenset[Capability]",
)
GetSemanticMeta.__signature__ = FuncSig(
    (
        FuncParam(
            "metadata", FuncParam.POSITIONAL_OR_KEYWORD, annotation="Mapping[str, Any]"
        ),
    ),
    return_annotation="Mapping[str, Any]",
)
GetPayloadIds.__signature__ = FuncSig(
    (FuncParam("document", FuncParam.POSITIONAL_OR_KEYWORD, annotation="CadDocument"),),
    return_annotation="frozenset[int]",
)
AddWrapperMeta.__signature__ = FuncSig(
    (
        FuncParam(
            "metadata", FuncParam.POSITIONAL_OR_KEYWORD, annotation="Mapping[str, Any]"
        ),
        FuncParam("keys", FuncParam.POSITIONAL_OR_KEYWORD, annotation="Iterable[str]"),
    ),
    return_annotation="Mapping[str, Any]",
)


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
