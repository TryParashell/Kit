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

from .assembly_data import AssemblyData
from .brep_model import BrepModel
from .common import FreezeMapping
from .document_behavior import DocumentApi
from .enum_document import Capability
from .enum_units import UnitSystem
from .feature_body import DesignBody
from .mesh import SurfaceMesh
from .model_base import ModelBase, ModelDataMut
from .payload_record import BrepPayload
from .record_config import Configuration
from .record_diagnostic import Diagnostic
from .record_source import CadSource
from .selection import Selection
from .sketch import Sketch
from .support_plane import SupportPlane
from .feature_step import FeatureStep
from .record_parameter import Parameter


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
