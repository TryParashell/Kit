# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange import Capability


# registry failures share one public base so callers can catch contract violations uniformly
class RegistryError(RuntimeError):
    __slots__ = ()


# missing adapter failures remain distinct so discovery fallbacks can continue safely
class NotFoundError(RegistryError):
    __slots__ = ()


# discovery failures preserve package context while separating import and registration errors
class DiscoveryError(RegistryError):
    __slots__ = ()


# ambiguous selections remain distinct so callers can request an explicit format
class AmbiguousError(RegistryError):
    __slots__ = ()


# capability loss carries structured evidence so conversion can fail before output mutation
class CapLossError(RegistryError):
    __slots__ = ("FormatId", "DroppedCaps")

    # structured fields let callers inspect the rejected format and exact lost capabilities
    def __init__(
        self,
        format_id: str,
        dropped: frozenset[Capability],
    ) -> None:
        self.FormatId = format_id
        self.DroppedCaps = dropped
        NameValues = ", ".join(
            sorted(CapabilityData.value for CapabilityData in dropped)
        )
        super().__init__(f"{format_id} cannot preserve capabilities: {NameValues}")

    # legacy fields remain readable because error handling is part of the public api
    @property
    def format_id(self) -> str:
        return self.FormatId

    # capability evidence remains public because callers inspect exact preservation loss
    @property
    def dropped(self) -> frozenset[Capability]:
        return self.DroppedCaps


# public registry exception name remains stable because callers import it directly
AdapterRegistryError = RegistryError

# public missing exception name remains stable because callers distinguish selection failures
AdapterNotFoundError = NotFoundError

# public discovery exception name remains stable because package loading failures are recoverable
AdapterDiscoveryError = DiscoveryError

# public ambiguity exception name remains stable because callers can retry with explicit formats
AmbiguousAdapterError = AmbiguousError

# public loss exception name remains stable because callers inspect its structured evidence
CapabilityLossError = CapLossError
