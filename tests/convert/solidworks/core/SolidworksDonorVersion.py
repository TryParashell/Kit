# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json as JsonLib
from pathlib import Path as FilePath


# committed provenance keeps archive regression gates independent from machine local traces
def GetDonorVer(FixtureRoot: FilePath, TraceVersion: int | None) -> int | None:
    if TraceVersion is not None:
        return TraceVersion
    Versions = {
        Version
        for MetaPath in FixtureRoot.glob("*/meta.json")
        if isinstance(
            Version := JsonLib.loads(MetaPath.read_text(encoding="utf-8")).get(
                "mo_version"
            ),
            int,
        )
        and not isinstance(Version, bool)
    }
    return Versions.pop() if len(Versions) == 1 else None
