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


# legacy callers retain these arc spellings so one protocol pins their static types
class SweepCompat(TypeProtocol):

    # compatibility callers retain the original centre property spelling
    @property
    def centre_mm(self) -> tuple[float, float]:
        return CastValue(tuple[float, float], getattr(self, "CentreMm"))

    # compatibility callers retain the original start point spelling
    @property
    def start_mm(self) -> tuple[float, float]:
        return CastValue(tuple[float, float], getattr(self, "StartMm"))

    # compatibility callers retain the original end point spelling
    @property
    def end_mm(self) -> tuple[float, float]:
        return CastValue(tuple[float, float], getattr(self, "EndMm"))

    # compatibility callers retain the original radius property spelling
    @property
    def radius_mm(self) -> float:
        return CastValue(float, getattr(self, "RadiusMm"))

    # compatibility callers retain the original end radius spelling
    @property
    def end_radius_mm(self) -> float:
        return CastValue(float, getattr(self, "EndRadiusMm"))

    # compatibility callers retain the original consistency predicate spelling
    @property
    def consistent(self) -> bool:
        return CastValue(bool, getattr(self, "IsConsistent"))

    # compatibility callers retain the original consistency alias spelling
    @property
    def Consistent(self) -> bool:
        return CastValue(bool, getattr(self, "IsConsistent"))

    # compatibility callers retain the original start angle spelling
    @property
    def start_angle_degrees(self) -> float:
        return CastValue(float, getattr(self, "StartAngle"))

    # compatibility callers retain the original end angle spelling
    @property
    def end_angle_degrees(self) -> float:
        return CastValue(float, getattr(self, "EndAngleDegrees"))

    # compatibility callers retain the original sweep method signature exactly
    def sweep_angle_degrees(self, Counterclockwise: bool) -> float:
        return CastValue(float, getattr(self, "SweepAngle")(Counterclockwise))
