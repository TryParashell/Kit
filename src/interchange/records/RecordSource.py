# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut


# source identity anchors every portable document to original bytes and application
@ModelDataMut
class CadSource(ModelBase):
    format_id: str
    path: str
    sha256: str
    container_version: str = ""
    application_version: str = ""
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def FormatId(self) -> str:
        return self.format_id

    @property
    def FilePath(self) -> str:
        return self.path

    @property
    def SourceDigest(self) -> str:
        return self.sha256

    @property
    def ContainerVersion(self) -> str:
        return self.container_version

    @property
    def ApplicationVersion(self) -> str:
        return self.application_version

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
