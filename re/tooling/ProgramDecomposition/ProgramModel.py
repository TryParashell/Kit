# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
from pathlib import Path as PathInfo
from typing import Any as AnyInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class ProgramData:
    VariantPath: str
    SourcePath: PathInfo
    SourceText: str
    OwnerName: str
    OpsName: str
    Streams: tuple[tuple[str, tuple[tuple[int, int, str, str, AnyInfo], ...]], ...]
    PublicNames: tuple[str, ...]
    ByteStats: tuple[tuple[str, int, str], ...]


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class MethodData:
    GroupPath: str
    OwnerSites: tuple[tuple[object, str], ...]
    StreamOps: tuple[tuple[str, tuple[tuple[int, int, object, str, AnyInfo], ...]], ...]


# needed to keep reverse engineering responsibilities isolated and maintainable
KHeaderText = "# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0\n# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin\n#\n# This SPDX license identifier and copyright notice must not be\n# removed, altered, or obscured. Doing so is a material breach of\n# the PolyForm Strict License 1.0.0 and voids all licenses granted\n# to you under it immediately and permanently.\n"

# needed to keep reverse engineering responsibilities isolated and maintainable
KOwnerNames = ("FieldOwners", "KFieldOwners")

# needed to keep reverse engineering responsibilities isolated and maintainable
KOperationNames = (
    "StreamPrograms",
    "ConfigOps",
    "KConfigOps",
    "ResolvedOps",
    "KResolvedOps",
    "AnnotationOps",
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KSingleStreams = {
    "ConfigOps": "Configuration",
    "KConfigOps": "Configuration",
    "ResolvedOps": "ResolvedFeatures",
    "KResolvedOps": "ResolvedFeatures",
    "AnnotationOps": "AnnotationManager",
}
