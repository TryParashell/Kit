# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.assembly.TransformMatrix import TransformMatrix


# placement consumers read identity and transform state through one typed view
class InstanceView:
    __slots__ = ()

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return CastValue(str, getattr(self, "id"))

    # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return CastValue(str, getattr(self, "name"))

    # definition link keeps shared geometry deduplicated across many instances
    @property
    def DefinitionId(self) -> str:
        return CastValue(str, getattr(self, "definition_id"))

    # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return CastValue(str, getattr(self, "owner_definition_id"))

    # local transform keeps world placement composable through parent chains
    @property
    def Transform(self) -> TransformMatrix:
        return CastValue(TransformMatrix, getattr(self, "transform"))

    # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return CastValue(int, getattr(self, "order"))

    # bom reference keeps purchased part identities aligned with cad data
    @property
    def ReferenceNumber(self) -> str:
        return CastValue(str, getattr(self, "reference_number"))

    # configuration label keeps variant identity visible without resolving parameters
    @property
    def ConfigurationName(self) -> str:
        return CastValue(str, getattr(self, "configuration_name"))

    # configuration id keeps variant references stable across renames
    @property
    def ConfigurationId(self) -> str:
        return CastValue(str, getattr(self, "configuration_id"))
