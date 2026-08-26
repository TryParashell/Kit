# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.assembly.AssemblyEnums import MateKind


# constraint consumers read identity and scope through one typed view
class ConstraintView:
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
    def EntityKind(self) -> MateKind | str:
        return CastValue(MateKind | str, getattr(self, "kind"))

    # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return CastValue(str, getattr(self, "owner_definition_id"))

    # referenced entity ids keep mate scope explicit and verifiable
    @property
    def EntityIds(self) -> tuple[str, ...]:
        return CastValue(tuple[str, ...], getattr(self, "entity_ids"))

    # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return CastValue(int, getattr(self, "order"))
