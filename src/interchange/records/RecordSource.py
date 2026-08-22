# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar
from typing import Mapping as TypeMap
from typing import TYPE_CHECKING

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut


# source identity anchors every portable document to original bytes and application
@ModelDataMut(
    DefaultMap={"container_version": "", "application_version": ""},
    FactoryMap={"attributes": FreezeMapping},
)
class CadSource(ModelBase):
    format_id: str
    path: str
    sha256: str
    container_version: str
    application_version: str
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        FormatId: ClassVar[str]
        FilePath: ClassVar[str]
        SourceDigest: ClassVar[str]
        ContainerVersion: ClassVar[str]
        ApplicationVersion: ClassVar[str]
        Attributes: ClassVar[TypeMap[str, object]]
