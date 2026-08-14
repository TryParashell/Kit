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

from interchange.assembly.AssemblyData import AssemblyData
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.document.behavior.DocumentBehavior import DocumentApi
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureBody import DesignBody
from interchange.mesh import SurfaceMesh
from interchange.core.ModelBase import ModelBase, ModelDataMut
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
@ModelDataMut(
    DefaultMap={
        "Meshes": (),
        "BrepPayloads": (),
        "Diagnostics": (),
        "Capabilities": frozenset(),
        "Units": UnitSystem.KMillimeter,
        "SchemaVersion": "1.0",
        "Assembly": None,
        "BrepModel": None,
    },
    FactoryMap={"Metadata": FreezeMapping},
)
class CadDocument(DocumentApi, ModelBase):
    Source: CadSource
    Configurations: tuple[Configuration, ...]
    Parameters: tuple[Parameter, ...]
    SupportPlanes: tuple[SupportPlane, ...]
    Sketches: tuple[Sketch, ...]
    Selections: tuple[Selection, ...]
    FeatureTimeline: tuple[FeatureStep, ...]
    Bodies: tuple[DesignBody, ...]
    Meshes: tuple[SurfaceMesh, ...]
    BrepPayloads: tuple[BrepPayload, ...]
    Diagnostics: tuple[Diagnostic, ...]
    Capabilities: frozenset[Capability]
    Metadata: TypeMap[str, AnyValue]
    Units: UnitSystem
    SchemaVersion: str
    Assembly: AssemblyData | None
    BrepModel: BrepModel | None
