# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordSource import CadSource


# the canonical document fixture keeps domain tests independent from test modules
def BuildDocument() -> CadDocument:
    PlaneValue = SupportPlane("plane:xy", "XY", Transform())
    EntityValue = SketchEntity(
        "sketch:1:line:1",
        "line",
        LineGeometry(PlaneVector(0.0, 0.0), PlaneVector(10.0, 0.0)),
    )
    SketchValue = Sketch("sketch:1", "Sketch1", PlaneValue.EntityId, (EntityValue,))
    FeatureValue = FeatureStep(
        "feature:1", "Boss1", FeatureKind.KExtrusion, 0, sketch_id=SketchValue.id
    )
    BodyValue = DesignBody("body:1", "Body", FeatureValue.EntityId)
    return CadDocument(
        source=CadSource("test", "memory", "0" * 64),
        configurations=(Configuration("config:default", "Default", True),),
        parameters=(),
        support_planes=(PlaneValue,),
        sketches=(SketchValue,),
        selections=(),
        feature_timeline=(FeatureValue,),
        bodies=(BodyValue,),
        capabilities=frozenset(
            {Capability.KParamHistory, Capability.KEditableSketches}
        ),
    )
