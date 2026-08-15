# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange import CadDocument
from interchange import CadSource
from interchange import Capability
from interchange import Configuration
from interchange import DesignBody
from interchange import FeatureKind
from interchange import FeatureStep
from interchange import LineGeometry
from interchange import PlaneVector
from interchange import Sketch
from interchange import SketchEntity
from interchange import SupportPlane
from interchange import Transform


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
        "feature:1", "Boss1", FeatureKind.KExtrusion, 0, SketchId=SketchValue.EntityId
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
