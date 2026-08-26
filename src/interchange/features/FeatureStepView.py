# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.enums.EnumFeatures import FeatureKind


# feature walkers read identity dependency order through one typed view
class FeatureStepView:
    __slots__ = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return CastValue(str, getattr(self, "name"))

    # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> FeatureKind | str:
        return CastValue(FeatureKind | str, getattr(self, "kind"))

    # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return CastValue(int, getattr(self, "order"))

    # input list preserves feature dependency order for rebuilds
    @property
    def InputFeatureIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "input_feature_ids"))

    # optional sketch link keeps sketch driven features traceable
    @property
    def SketchId(self) -> str | None:
        return CastValue(str | None, getattr(self, "sketch_id"))

    # selection list keeps user picked references replayable on reload
    @property
    def SelectionIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "selection_ids"))
