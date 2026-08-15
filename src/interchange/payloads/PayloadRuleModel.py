# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.payloads.PayloadRoles import PayloadRole


# legacy payload inference needs declarative evidence that remains independently testable
@ModelDataMut(
    DefaultMap={
        "FormatIds": frozenset[str](),
        "Kinds": frozenset[str](),
        "Schemas": frozenset[str](),
        "SourceSuffixes": frozenset[str](),
    }
)
class PayloadRule(ModelBase):
    ValueRole: PayloadRole
    FileExtension: str
    FormatIds: frozenset[str]
    Kinds: frozenset[str]
    Schemas: frozenset[str]
    SourceSuffixes: frozenset[str]
