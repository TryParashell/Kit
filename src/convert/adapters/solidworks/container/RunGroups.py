# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass as Dataclass


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroupCount:
    At: int
    Back: int
    Width: int
    Lead: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroupCountA:
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    Count: int
    Lead: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroupVariant:
    Slot: int
    Last: bool
    StopGroups: bool
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    ChildClasses: tuple[str, ...]
    Run: int
    RunsByVersion: Mapping[int, int]
    Trailer: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroupTrailer:
    Versions: tuple[int, ...]
    PredicateAt: int
    PredicateWidth: int
    Values: tuple[int, ...]
    Trailer: int


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class RunGroup:
    name: str
    repeat: int
    count_back: int
    count_width: int
    CountByChildClass: Mapping[str, RunGroupCount]
    CountVariants: tuple[RunGroupCountA, ...]
    slots: tuple[str, ...]
    element: tuple[int, ...]
    element_by_version: Mapping[int, tuple[int, ...]]
    ElementRunVariants: tuple[RunGroupVariant, ...]
    trailer: int
    TrailerVariants: tuple[RunGroupTrailer, ...]
    note: str

    # this definition exists because focused behavior needs one stable owner
    def ElemRuns(self, MoVersion: int | None) -> tuple[int, ...]:
        if MoVersion is not None:
            Gated = self.element_by_version.get(MoVersion)
            if Gated is not None:
                return Gated
        return self.element

    element_runs = ElemRuns
