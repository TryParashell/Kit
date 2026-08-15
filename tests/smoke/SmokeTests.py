# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert import available_adapters as AvailableAdapters
from interchange import CadDocument
from interchange import CadSource


# needed because smoke tests must prove packages import before expensive suites
def TestPkgImports() -> None:
    assert (
        CadDocument(
            Source=CadSource(FormatId="smoke", FilePath=None, SourceDigest=None),
            Configurations=(),
            Parameters=(),
            SupportPlanes=(),
            Sketches=(),
            Selections=(),
            FeatureTimeline=(),
            Bodies=(),
        ).schema_version
        == "1.0"
    )


# needed because smoke tests must prove adapter discovery remains publicly available
def TestRegistry() -> None:
    AdapterNames = {AdapterInfo.name for AdapterInfo in AvailableAdapters()}
    assert "Kit interchange JSON" in AdapterNames
