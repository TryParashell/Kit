# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters import AdapterInfo
from convert.api.ApiContext import KAdapterRegistry


# public discovery merges read and write formats so callers see one deterministic catalog
def ListAdapters() -> tuple[AdapterInfo, ...]:
    AdapterMap = {
        AdapterData.info.format_id: AdapterData.info
        for AdapterData in KAdapterRegistry.readers()
    }
    AdapterMap.update(
        {
            AdapterData.info.format_id: AdapterData.info
            for AdapterData in KAdapterRegistry.writers()
        }
    )
    return tuple(AdapterMap[FormatId] for FormatId in sorted(AdapterMap))
