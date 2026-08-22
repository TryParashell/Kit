# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# component definitions describe reusable nodes independently from their occurrences
@ModelDataMut(
    DefaultMap={
        "document_id": "",
        "configuration_name": "",
        "configuration_id": "",
        "bounding_box": None,
        "body_ids": (),
        "mesh_ids": (),
        "source_path": "",
        "source_format_id": "",
        "source_sha256": "",
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class ComponentDef(ModelBase):
    id: str
    name: str
    kind: ComponentKind | str
    document_id: str
    configuration_name: str
    configuration_id: str
    bounding_box: BoundingBox | None
    body_ids: tuple[str, ...]
    mesh_ids: tuple[str, ...]
    source_path: str
    source_format_id: str
    source_sha256: str
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        EntityKind: ClassVar[ComponentKind | str]
        DocumentId: ClassVar[str]
        ConfigurationName: ClassVar[str]
        ConfigurationId: ClassVar[str]
        BoundingBox: ClassVar[BoundingBox | None]
        BodyIds: ClassVar[tuple[str, ...]]
        MeshIds: ClassVar[tuple[str, ...]]
        SourcePath: ClassVar[str]
        SourceFormatId: ClassVar[str]
        SourceDigest: ClassVar[str]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
