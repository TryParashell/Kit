# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Protocol

from convert.adapters.registry import AdapterRegistry


# engine initialization accepts every coordinator exposing the concrete registry state
class EngineState(Protocol):
    registry: AdapterRegistry


# dependency injection keeps adapter discovery replaceable without cad application coupling
def InitEngineMut(SelfValue: EngineState, RegistryData: AdapterRegistry) -> None:
    SelfValue.registry = RegistryData
