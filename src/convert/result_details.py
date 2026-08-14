# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from inspect import Parameter as SigParam
from inspect import Signature as CallSignature

from interchange import Capability

from .adapters import CapabilityTransfer as TransferInfo


# property metadata must match the historical owner even though behavior remains inherited
def SetPropMetaMut(GetterValue, PublicName: str, ReturnType: str) -> property:
    setattr(GetterValue, "__annotations__", {"return": ReturnType})
    setattr(GetterValue, "__module__", "convert.engine")
    setattr(GetterValue, "__name__", PublicName)
    setattr(GetterValue, "__qualname__", f"ConversionResult.{PublicName}")
    setattr(
        GetterValue,
        "__signature__",
        CallSignature(
            (SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),),
            return_annotation=ReturnType,
        ),
    )
    return property(GetterValue)


# transfer details stay delegated so the result record remains a focused value object
class ResultDetails:
    locals()["__slots__"] = ()

    # callers need preservation evidence without navigating the nested writer result
    def GetTransfers(SelfValue) -> tuple[TransferInfo, ...]:
        return getattr(SelfValue, "output").transfers

    locals()["transfers"] = SetPropMetaMut(
        GetTransfers, "transfers", "tuple[CapabilityTransfer, ...]"
    )

    # callers need loss evidence beside the conversion summary for immediate gating
    def GetDropped(SelfValue) -> frozenset[Capability]:
        return getattr(SelfValue, "output").dropped

    locals()["dropped"] = SetPropMetaMut(GetDropped, "dropped", "frozenset[Capability]")

    # callers need external requirements exposed where conversion outcomes are inspected
    def GetNeeds(SelfValue) -> tuple[str, ...]:
        return getattr(SelfValue, "output").requirements

    locals()["requirements"] = SetPropMetaMut(
        GetNeeds, "requirements", "tuple[str, ...]"
    )
