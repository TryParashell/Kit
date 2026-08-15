# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters import AdapterRegistry
from convert.engine import ConversionEngine


# one discovery factory keeps the public composition root independent from format packages
def BuildRegistry() -> AdapterRegistry:
    RegistryData = AdapterRegistry()
    RegistryData.introspect()
    return RegistryData


# one shared registry keeps public discovery and conversion selections consistent
KAdapterRegistry = BuildRegistry()

# one shared engine keeps public operations on the same introspected adapter set
KConvertEngine = ConversionEngine(KAdapterRegistry)


# compatibility callers need access to the already introspected shared registry
def GetRegistry() -> AdapterRegistry:
    return KAdapterRegistry
