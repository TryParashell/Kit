# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import ClassVar, TYPE_CHECKING

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
    if TYPE_CHECKING:
        ValueRole: ClassVar[PayloadRole]
        FileExtension: ClassVar[str]
        FormatIds: ClassVar[frozenset[str]]
        Kinds: ClassVar[frozenset[str]]
        Schemas: ClassVar[frozenset[str]]
        SourceSuffixes: ClassVar[frozenset[str]]
