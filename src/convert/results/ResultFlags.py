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


# property metadata must match the historical owner even though behavior remains inherited
def SetPropMetaMut(GetterValue, PublicName: str) -> property:
    setattr(GetterValue, "__annotations__", {"return": "bool"})
    setattr(GetterValue, "__module__", "convert.engine")
    setattr(GetterValue, "__name__", PublicName)
    setattr(GetterValue, "__qualname__", f"ConversionResult.{PublicName}")
    setattr(
        GetterValue,
        "__signature__",
        CallSignature(
            (SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),),
            return_annotation="bool",
        ),
    )
    return property(GetterValue)


# outcome predicates stay grouped because they all delegate writer attestations unchanged
class ResultFlags:
    locals()["__slots__"] = ()

    # application gating belongs on the conversion outcome users already inspect
    def IsAppUsable(SelfValue) -> bool:
        return getattr(SelfValue, "output").application_usable

    locals()["application_usable"] = SetPropMetaMut(IsAppUsable, "application_usable")

    # vendor loadability remains distinct because usable output requires both attestations
    def IsVendorLoad(SelfValue) -> bool:
        return getattr(SelfValue, "output").vendor_loadable

    locals()["vendor_loadable"] = SetPropMetaMut(IsVendorLoad, "vendor_loadable")

    # round trip safety remains visible because capability preservation is a primary contract
    def IsRoundtrip(SelfValue) -> bool:
        return getattr(SelfValue, "output").roundtrip_safe

    locals()["roundtrip_safe"] = SetPropMetaMut(IsRoundtrip, "roundtrip_safe")

    # lossless status remains delegated so writer evidence has one authoritative calculation
    def IsLossless(SelfValue) -> bool:
        return getattr(SelfValue, "output").near_lossless

    locals()["near_lossless"] = SetPropMetaMut(IsLossless, "near_lossless")
