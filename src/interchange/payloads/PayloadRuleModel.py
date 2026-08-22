# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.payloads.PayloadRoles import PayloadRole

# one shared empty set keeps rule defaults free of repeated constructor calls
KEmptyKindSets: frozenset[str] = frozenset()


# legacy payload inference needs declarative evidence that remains independently testable
@ModelDataMut
class PayloadRule(ModelBase):
    role: PayloadRole
    file_extension: str
    format_ids: frozenset[str] = KEmptyKindSets
    kinds: frozenset[str] = KEmptyKindSets
    schemas: frozenset[str] = KEmptyKindSets
    source_suffixes: frozenset[str] = KEmptyKindSets

    @property
    def ValueRole(self) -> PayloadRole:
        return self.role

    @property
    def FileExtension(self) -> str:
        return self.file_extension

    @property
    def FormatIds(self) -> frozenset[str]:
        return self.format_ids

    @property
    def Kinds(self) -> frozenset[str]:
        return self.kinds

    @property
    def Schemas(self) -> frozenset[str]:
        return self.schemas

    @property
    def SourceSuffixes(self) -> frozenset[str]:
        return self.source_suffixes
