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

from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# component definitions describe reusable nodes independently from their occurrences
@ModelDataMut
class ComponentDef(ModelBase):
    id: str
    name: str
    kind: ComponentKind | str
    document_id: str = ""
    configuration_name: str = ""
    configuration_id: str = ""
    bounding_box: BoundingBox | None = None
    body_ids: tuple[str, ...] = ()
    mesh_ids: tuple[str, ...] = ()
    source_path: str = ""
    source_format_id: str = ""
    source_sha256: str = ""
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

     # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> ComponentKind | str:
        return self.kind

     # owning document id keeps definitions linkable across container boundaries
    @property
    def DocumentId(self) -> str:
        return self.document_id

     # configuration label keeps variant identity visible without resolving parameters
    @property
    def ConfigurationName(self) -> str:
        return self.configuration_name

     # configuration id keeps variant references stable across renames
    @property
    def ConfigurationId(self) -> str:
        return self.configuration_id

     # cached bounds keep spatial filtering cheap for large assemblies
    @property
    def BoundingBox(self) -> BoundingBox | None:
        return self.bounding_box

     # body references keep solid topology reachable without embedding geometry
    @property
    def BodyIds(self) -> tuple[str, ...]:
        return self.body_ids

     # mesh references keep tessellation reachable without duplicating payloads
    @property
    def MeshIds(self) -> tuple[str, ...]:
        return self.mesh_ids

     # original path keeps provenance traceable back to the source container
    @property
    def SourcePath(self) -> str:
        return self.source_path

     # format id keeps multi format routing decisions possible downstream
    @property
    def SourceFormatId(self) -> str:
        return self.source_format_id

     # digest lets consumers detect source drift without rereading containers
    @property
    def SourceDigest(self) -> str:
        return self.source_sha256

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
