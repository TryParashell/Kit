# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange import Capability


# policy consumers read acceptance limits and usability flags through one typed view
class ResultPolicy:
    __slots__ = ()

    # legacy callers need dropped capability access as a typed set
    @property
    def DroppedCaps(self) -> frozenset[Capability]:
        return CastValue(frozenset[Capability], getattr(self, "dropped"))

    # legacy callers need output requirements to retain their immutable sequence type
    @property
    def Requirements(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "requirements"))

    # legacy callers need application usability as a statically visible predicate
    @property
    def IsAppUsable(self) -> bool:
        return CastValue(bool, getattr(self, "application_usable"))

    # legacy callers need vendor loadability as a statically visible predicate
    @property
    def IsVendorLoadable(self) -> bool:
        return CastValue(bool, getattr(self, "vendor_loadable"))
