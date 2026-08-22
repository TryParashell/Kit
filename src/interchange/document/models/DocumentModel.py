# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.assembly.AssemblyData import (
    AssemblyData,  # lgtm[py/unsafe-cyclic-import]
)
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.document.behavior.DocumentBehavior import (  # lgtm[py/cyclic-import]
    DocumentApi,
)
from interchange.document.models.DocumentRoot import DocumentRoot
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBody import DesignBody
from interchange.mesh.SurfaceMesh import SurfaceMesh
from interchange.core.ModelBase import ModelBase
from interchange.payloads.PayloadRecord import BrepPayload
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordDiagnostic import Diagnostic
from interchange.records.RecordSource import CadSource
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter


# portable cad exchange needs one immutable root connecting every neutral model domain
@MakeDataClass(frozen=True, slots=True)
class CadDocument(DocumentRoot, DocumentApi, ModelBase):
    source: CadSource
    configurations: tuple[Configuration, ...]
    parameters: tuple[Parameter, ...]
    support_planes: tuple[SupportPlane, ...]
    sketches: tuple[Sketch, ...]
    selections: tuple[Selection, ...]
    feature_timeline: tuple[FeatureStep, ...]
    bodies: tuple[DesignBody, ...]
    meshes: tuple[SurfaceMesh, ...] = ()
    brep_payloads: tuple[BrepPayload, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    capabilities: frozenset[Capability] = frozenset()
    metadata: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    units: UnitSystem = UnitSystem.KMillimeter
    schema_version: str = "1.0"
    assembly: AssemblyData | None = None
    brep: BrepModel | None = None

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Source(self) -> CadSource:
        return self.source

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Configurations(self) -> tuple[Configuration, ...]:
        return self.configurations

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Parameters(self) -> tuple[Parameter, ...]:
        return self.parameters

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def SupportPlanes(self) -> tuple[SupportPlane, ...]:
        return self.support_planes

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Sketches(self) -> tuple[Sketch, ...]:
        return self.sketches

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Selections(self) -> tuple[Selection, ...]:
        return self.selections

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def FeatureTimeline(self) -> tuple[FeatureStep, ...]:
        return self.feature_timeline

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Bodies(self) -> tuple[DesignBody, ...]:
        return self.bodies

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Meshes(self) -> tuple[SurfaceMesh, ...]:
        return self.meshes

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def BrepPayloads(self) -> tuple[BrepPayload, ...]:
        return self.brep_payloads

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Diagnostics(self) -> tuple[Diagnostic, ...]:
        return self.diagnostics

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Capabilities(self) -> frozenset[Capability]:
        return self.capabilities

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Metadata(self) -> TypeMap[str, object]:
        return self.metadata

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Units(self) -> UnitSystem:
        return self.units

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def SchemaVersion(self) -> str:
        return self.schema_version

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def Assembly(self) -> AssemblyData | None:
        return self.assembly

    # pascal compatibility keeps existing adapters typed during lowercase contract migration
    @property
    def BrepModel(self) -> BrepModel | None:
        return self.brep
