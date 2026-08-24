# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.registry.RegistryBinding import AdapterBinding


# fresh registries start empty because applications need isolated transactional state
class RegistrySeed:
    BindingMap: dict[str, AdapterBinding]
    AliasMap: dict[str, str]

    # empty isolated state supports independent applications tests and transactional discovery
    def __init__(self) -> None:
        super().__init__()
        self.BindingMap = {}
        self.AliasMap = {}
