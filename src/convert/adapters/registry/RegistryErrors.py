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
from typing import Any as AnyValue

from interchange import Capability


# registry failures share one public base so callers can catch contract violations uniformly
class RegistryError(RuntimeError):
    locals()["__slots__"] = ()


# missing adapter failures remain distinct so discovery fallbacks can continue safely
class NotFoundError(RegistryError):
    locals()["__slots__"] = ()


# discovery failures preserve package context while separating import and registration errors
class DiscoveryError(RegistryError):
    locals()["__slots__"] = ()


# ambiguous selections remain distinct so callers can request an explicit format
class AmbiguousError(RegistryError):
    locals()["__slots__"] = ()


# capability loss carries structured evidence so conversion can fail before output mutation
class CapLossError(RegistryError):
    locals()["__slots__"] = ("FormatId", "DroppedCaps")

    # structured fields let callers inspect the rejected format and exact lost capabilities
    def __init__(
        SelfValue,
        FormatId: str | None = None,
        DroppedCaps: frozenset[Capability] | None = None,
        **NamedValues: AnyValue,
    ) -> None:
        AllowedNames = {"format_id", "dropped"}
        UnknownNames = tuple(
            NameText for NameText in NamedValues if NameText not in AllowedNames
        )
        if UnknownNames:
            raise TypeError(
                "CapabilityLossError() got an unexpected keyword argument "
                f"{UnknownNames[0]!r}"
            )
        if FormatId is not None and "format_id" in NamedValues:
            raise TypeError("CapabilityLossError() got multiple values for 'format_id'")
        if DroppedCaps is not None and "dropped" in NamedValues:
            raise TypeError("CapabilityLossError() got multiple values for 'dropped'")
        FormatId = NamedValues.get("format_id", FormatId)
        DroppedCaps = NamedValues.get("dropped", DroppedCaps)
        if FormatId is None:
            raise TypeError(
                "CapabilityLossError() missing required argument 'format_id'"
            )
        if DroppedCaps is None:
            raise TypeError("CapabilityLossError() missing required argument 'dropped'")
        if not isinstance(FormatId, str):
            raise TypeError("format id must be a string")
        if not isinstance(DroppedCaps, frozenset) or any(
            not isinstance(CapabilityData, Capability) for CapabilityData in DroppedCaps
        ):
            raise TypeError("dropped must be a frozenset of Capability values")
        SelfValue.FormatId = FormatId
        SelfValue.DroppedCaps = DroppedCaps
        NameValues = ", ".join(
            sorted(CapabilityData.value for CapabilityData in DroppedCaps)
        )
        super().__init__(f"{FormatId} cannot preserve capabilities: {NameValues}")

    # legacy fields remain readable because error handling is part of the public api
    def __getattr__(SelfValue, FieldName: str) -> object:
        AliasMap = {"format_id": "FormatId", "dropped": "DroppedCaps"}
        if FieldName in AliasMap:
            return object.__getattribute__(SelfValue, AliasMap[FieldName])
        raise AttributeError(FieldName)


# public registry exception name remains stable because callers import it directly
globals()["AdapterRegistryError"] = RegistryError

# public missing exception name remains stable because callers distinguish selection failures
globals()["AdapterNotFoundError"] = NotFoundError

# public discovery exception name remains stable because package loading failures are recoverable
globals()["AdapterDiscoveryError"] = DiscoveryError

# public ambiguity exception name remains stable because callers can retry with explicit formats
globals()["AmbiguousAdapterError"] = AmbiguousError

# public loss exception name remains stable because callers inspect its structured evidence
globals()["CapabilityLossError"] = CapLossError

setattr(
    CapLossError,
    "__signature__",
    CallSignature(
        (
            SigParam(
                "format_id",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="str",
            ),
            SigParam(
                "dropped",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="frozenset[Capability]",
            ),
        ),
        return_annotation="None",
    ),
)
