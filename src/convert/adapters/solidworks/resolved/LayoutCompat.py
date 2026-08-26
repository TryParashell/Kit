# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Protocol as TypeProtocol
from typing import cast as CastValue


# legacy callers retain these feature spellings so one protocol pins their static types
class LayoutCompat(TypeProtocol):

    # compatibility callers retain the original revolution predicate spelling
    @property
    def is_revolution(self) -> bool:
        return CastValue(bool, getattr(self, "IsRevolution"))

    # compatibility callers retain the original angle property spelling
    @property
    def angle_degrees(self) -> float | None:
        return CastValue(float | None, getattr(self, "AngleDegrees"))

    # compatibility callers retain the original corners property spelling
    @property
    def corners_mm(self) -> tuple[tuple[float, float], ...]:
        return CastValue(
            tuple[tuple[float, float], ...],
            getattr(self, "CornersMm"),
        )

    # compatibility callers retain the original radii property spelling
    @property
    def radii_mm(self) -> tuple[float, ...]:
        return CastValue(tuple[float, ...], getattr(self, "RadiiMm"))

    # compatibility callers retain the original bounds property spelling
    @property
    def bounds_mm(self) -> tuple[float, float, float, float] | None:
        return CastValue(
            tuple[float, float, float, float] | None,
            getattr(self, "BoundsMm"),
        )
