# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert import available_adapters
from interchange import CadDocument
from interchange import CadSource


# this definition exists because the blocking CI smoke suite needs a fast package import check
def TestPublicPackagesImport() -> None:
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


# this definition exists because the blocking CI smoke suite needs a fast adapter registry check
def TestAdapterRegistryListsFormats() -> None:
    AdapterNames = {Item.name for Item in available_adapters()}
    assert "Kit interchange JSON" in AdapterNames
