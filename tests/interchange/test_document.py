from __future__ import annotations

import pytest

from interchange import (
    Body,
    CadDocument,
    CadDocumentValidationError,
    CadSource,
    Capability,
    Configuration,
    FeatureKind,
    FeatureStep,
    LineGeometry,
    Sketch,
    SketchEntity,
    SupportPlane,
    Transform,
    Vector2,
)


def document() -> CadDocument:
    plane = SupportPlane("plane:xy", "XY", Transform())
    entity = SketchEntity(
        "sketch:1:line:1",
        "line",
        LineGeometry(Vector2(0.0, 0.0), Vector2(10.0, 0.0)),
    )
    sketch = Sketch("sketch:1", "Sketch1", plane.id, (entity,))
    feature = FeatureStep(
        "feature:1", "Boss1", FeatureKind.EXTRUSION, 0, sketch_id=sketch.id
    )
    body = Body("body:1", "Body", feature.id)
    return CadDocument(
        source=CadSource("test", "memory", "0" * 64),
        configurations=(Configuration("config:default", "Default", True),),
        parameters=(),
        support_planes=(plane,),
        sketches=(sketch,),
        selections=(),
        feature_timeline=(feature,),
        bodies=(body,),
        capabilities=frozenset(
            {Capability.PARAMETRIC_HISTORY, Capability.EDITABLE_SKETCHES}
        ),
    )


def test_json_roundtrip_is_lossless() -> None:
    source = document()
    restored = CadDocument.from_json(source.to_json())
    assert restored == source
    assert isinstance(restored.capabilities, frozenset)
    assert isinstance(restored.feature_timeline, tuple)


def test_forward_feature_dependency_is_rejected() -> None:
    source = document()
    first = FeatureStep(
        "feature:0",
        "Invalid",
        FeatureKind.EXTRUSION,
        0,
        input_feature_ids=("feature:1",),
    )
    second = FeatureStep("feature:1", "Later", FeatureKind.EXTRUSION, 1)
    invalid = CadDocument(
        source=source.source,
        configurations=source.configurations,
        parameters=(),
        support_planes=source.support_planes,
        sketches=(),
        selections=(),
        feature_timeline=(first, second),
        bodies=(Body("body:1", "Body", second.id),),
    )
    with pytest.raises(CadDocumentValidationError, match="forward dependency"):
        invalid.assert_valid()
