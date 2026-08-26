# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from inspect import Signature as FuncSig

from interchange.compatibility.PythonCompatMethods import BindAliasMut, MakeParam


# brep callers retain historical validation reflection while canonical methods stay compliant
def BindBrepMut(ModelType: type) -> None:
    BindAliasMut(
        ModelType,
        "GetErrors",
        "validate",
        {
            "design_body_ids": "frozenset[str]",
            "return": "tuple[str, ...]",
        },
        FuncSig(
            (
                MakeParam("self"),
                MakeParam(
                    "design_body_ids",
                    DefaultValue=frozenset[str](),
                    AnnotValue="frozenset[str]",
                ),
            ),
            return_annotation="tuple[str, ...]",
        ),
    )
