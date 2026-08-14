# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .common import FreezeMapping
from .model_base import ModelBase, ModelDataMut


# source identity anchors every portable document to original bytes and application
@ModelDataMut(
    DefaultMap={"ContainerVersion": "", "ApplicationVersion": ""},
    FactoryMap={"Attributes": FreezeMapping},
)
class CadSource(ModelBase):
    FormatId: str
    FilePath: str
    SourceDigest: str
    ContainerVersion: str
    ApplicationVersion: str
    Attributes: TypeMap[str, AnyValue]
