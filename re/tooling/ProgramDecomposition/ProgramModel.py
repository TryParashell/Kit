# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


# generators share one immutable representation so every renderer sees identical recovered data
@dataclass(frozen=True, slots=True)
class ProgramData:
    VariantPath: str
    SourcePath: Path
    SourceText: str
    OwnerName: str
    OpsName: str
    Streams: tuple[tuple[str, tuple[tuple[int, int, str, str, Any], ...]], ...]
    PublicNames: tuple[str, ...]
    ByteStats: tuple[tuple[str, int, str], ...]


# grouped serializers need their exact sites beside every variant specific operation table
@dataclass(frozen=True, slots=True)
class MethodData:
    GroupPath: str
    OwnerSites: tuple[tuple[object, str], ...]
    StreamOps: tuple[tuple[str, tuple[tuple[int, int, object, str, Any], ...]], ...]


# generated sources must carry the repository notice without renderer specific copies
KHeaderText = """# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.
"""


# every legacy program uses exactly one owner table spelling from this closed set
KOwnerNames = ("FieldOwners", "KFieldOwners")


# every legacy program uses exactly one operation table spelling from this closed set
KOperationNames = (
    "StreamPrograms",
    "ConfigOps",
    "KConfigOps",
    "ResolvedOps",
    "KResolvedOps",
    "AnnotationOps",
)


# single stream tables need stable internal keys while assembly retains native stream names
KSingleStreams = {
    "ConfigOps": "Configuration",
    "KConfigOps": "Configuration",
    "ResolvedOps": "ResolvedFeatures",
    "KResolvedOps": "ResolvedFeatures",
    "AnnotationOps": "AnnotationManager",
}
