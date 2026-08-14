# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import replace as ReplaceData
from convert.adapters.solidworks.core.Native import HORIZONTAL_AXIS_SUBELEMENT as Subelement, NORMAL_AXIS_SUBELEMENT as SubelementA, VERTICAL_AXIS_SUBELEMENT as SubelementB, _matrix_frame as MatrixFrame, _plane_frame_block as PlaneFrameBlock, _plane_payload as PlanePayload, NativeMarker, NativeModel, NativeOperation, NativeSketch, expression_equation_texts as ExpressionEquationTexts, native_axis_bindings as NativeAxisBindings, operation_axis_subelement as OperationAxisSubelement
from interchange import CadDocument, CadSource, Expression, Parameter, ParameterRole, ParameterValue, SupportPlane, Transform, UnitSystem, ValueKind, Vector3 as VectorThree

# keeps this focused behavior isolated so regressions remain immediately visible
def Document(Parameters: tuple[Parameter, ...]) -> CadDocument:
    return CadDocument(source=CadSource('freecad.fcstd', 'Metadata.FCStd', '0' * 64), configurations=(), parameters=Parameters, support_planes=(), sketches=(), selections=(), feature_timeline=(), bodies=(), units=UnitSystem.MILLIMETER)

# keeps this focused behavior isolated so regressions remain immediately visible
def ParameterA(NameText: str, ItemValue: ParameterValue, SourceDoc: str | None) -> Parameter:
    return Parameter(id=f'freecad:parameter:{NameText}', name=NameText, value=ItemValue, role=ParameterRole.DRIVING, owner_id='freecad:object:Owner', expression=None if SourceDoc is None else Expression(SourceDoc, (), 'freecad'))

# keeps this focused behavior isolated so regressions remain immediately visible
def Plane(NameText: str, AxesInfo: tuple[VectorThree, VectorThree, VectorThree]) -> SupportPlane:
    return SupportPlane(id=f'freecad:plane:{NameText}', name=NameText, transform=Transform(VectorThree(0.0, 0.0, 0.0), AxesInfo[0], AxesInfo[1], AxesInfo[2]))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestEEERAB() -> None:
    DocumentA = Document((ParameterA('Sketch004.9', ParameterValue(5.0, ValueKind.LENGTH, 'mm'), '<<Attributes002>>.Diameter'),))
    assert ExpressionEquationTexts(DocumentA) == ('"Kit_Attributes002_Diameter"= 5mm', '"Kit_Sketch004_9"= "Kit_Attributes002_Diameter"')

# keeps this focused behavior isolated so regressions remain immediately visible
def TestEESORV() -> None:
    DocumentA = Document((ParameterA('LeadInFeed', ParameterValue(0.0, ValueKind.NUMBER, ''), 'HorizFeed'), ParameterA('LeadOutFeed', ParameterValue(0.0, ValueKind.NUMBER, ''), 'HorizFeed')))
    assert ExpressionEquationTexts(DocumentA) == ('"Kit_HorizFeed"= 0', '"Kit_LeadInFeed"= "Kit_HorizFeed"', '"Kit_LeadOutFeed"= "Kit_HorizFeed"')

# keeps this focused behavior isolated so regressions remain immediately visible
def TestEEDCS() -> None:
    DocumentA = Document((ParameterA('Width', ParameterValue(5.0, ValueKind.LENGTH, 'mm'), 'Length / 2'),))
    assert ExpressionEquationTexts(DocumentA) is None

# keeps this focused behavior isolated so regressions remain immediately visible
def TestEEDCRV() -> None:
    DocumentA = Document((ParameterA('A', ParameterValue(1.0, ValueKind.NUMBER, ''), 'Shared'), ParameterA('B', ParameterValue(2.0, ValueKind.NUMBER, ''), 'Shared')))
    assert ExpressionEquationTexts(DocumentA) is None

# keeps this focused behavior isolated so regressions remain immediately visible
def TestDWENNE() -> None:
    assert ExpressionEquationTexts(Document(())) == ()

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPFBIRBTD() -> None:
    PlaneA = Plane('XZ_Plane', (VectorThree(1.0, 0.0, 0.0), VectorThree(0.0, -2.220446049250313e-16, 1.0), VectorThree(0.0, -1.0, -2.220446049250313e-16)))
    Block = PlaneFrameBlock(PlaneA)
    assert Block is not None
    assert len(Block) == 121
    Frame = MatrixFrame(Block, 0, len(Block))
    assert Frame is not None
    IgnoredValue, IgnoredValue, Origin, Normal, UAxis, VAxis = Frame
    assert Origin == (0.0, 0.0, 0.0)
    assert Normal == (0.0, -1.0, 0.0)
    assert UAxis == (1.0, 0.0, 0.0)
    assert VAxis == (0.0, 0.0, 1.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestPFBRANOF() -> None:
    PlaneA = Plane('Skewed', (VectorThree(1.0, 0.0, 0.0), VectorThree(1.0, 1.0, 0.0), VectorThree(0.0, 0.0, 1.0)))
    assert PlaneFrameBlock(PlaneA) is None

# keeps this focused behavior isolated so regressions remain immediately visible
def TestAPPCADRF() -> None:
    PlaneA = Plane('XY_Plane001', (VectorThree(1.0, 0.0, 0.0), VectorThree(0.0, 1.0, 0.0), VectorThree(0.0, 0.0, 1.0)))
    Payload = PlanePayload(PlaneA)
    assert Payload.endswith(PlaneFrameBlock(PlaneA))
    Offset = len(Payload) - 121
    Frame = MatrixFrame(Payload, Offset, len(Payload))
    assert Frame is not None
    assert Frame[0] == Offset
    assert Frame[1] == 121
    assert Frame[3] == (0.0, 0.0, 1.0)
    assert Frame[4] == (1.0, 0.0, 0.0)
    assert Frame[5] == (0.0, 1.0, 0.0)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestAPPIEFANOF() -> None:
    PlaneA = Plane('Skewed001', (VectorThree(1.0, 0.0, 0.0), VectorThree(1.0, 1.0, 0.0), VectorThree(0.0, 0.0, 1.0)))
    assert PlanePayload(PlaneA) == b''

# keeps this focused behavior isolated so regressions remain immediately visible
def Marker(Offset: int, Semantic: str, Coordinates: tuple[float, float] | None, Endpoints: tuple[int, int] | None, ProfileRole: int) -> NativeMarker:
    return NativeMarker(offset=Offset, length=32, prefix='', native_kind=1, locus='', profile_role=ProfileRole, state=None, object_index=None, local_id=None, coordinates_mm=Coordinates, endpoint_indices=Endpoints, construction=ProfileRole == 2, semantic=Semantic)

# keeps this focused behavior isolated so regressions remain immediately visible
def Sketch(Markers: tuple[NativeMarker, ...]) -> NativeSketch:
    return NativeSketch(object_id=55, name='Sketch5', support_plane_id=3, native_offset=0, native_end=1, markers=Markers, profiles=(), dimensions=(), constraints=())

# keeps this focused behavior isolated so regressions remain immediately visible
def Operation(KindInfo: str) -> NativeOperation:
    return NativeOperation(object_id=60, name='Revolve1', kind=KindInfo, profile_id=55, dependencies=(), native_offset=0, native_end=1, length_mm=None, radius_mm=None, family_code=None, operation_code=None, schema_code=None, direction_code=None, termination_code=None, selection_offsets=(), selected_local_ids=())

# keeps this focused behavior isolated so regressions remain immediately visible
def TestEDITPSNA() -> None:
    SketchA = Sketch(())
    assert OperationAxisSubelement(Operation('join'), SketchA) == SubelementA
    assert OperationAxisSubelement(Operation('cut'), SketchA) == SubelementA
    assert OperationAxisSubelement(Operation('native'), SketchA) is None

# keeps this focused behavior isolated so regressions remain immediately visible
def TestRAIRFTPCL() -> None:
    Vertical = Sketch((Marker(0, 'circle', (0.0, -154.0), None, 1), Marker(32, 'circle', (0.0, -216.0), None, 1), Marker(64, 'line', None, (0, 1), 2)))
    assert OperationAxisSubelement(Operation('revolve_join'), Vertical) == SubelementB
    Horizontal = Sketch((Marker(0, 'circle', (-20.0, 4.0), None, 1), Marker(32, 'circle', (20.0, 4.0), None, 1), Marker(64, 'line', None, (0, 1), 2)))
    assert OperationAxisSubelement(Operation('revolve_cut'), Horizontal) == Subelement
    Skewed = Sketch((Marker(0, 'circle', (0.0, 0.0), None, 1), Marker(32, 'circle', (10.0, 10.0), None, 1), Marker(64, 'line', None, (0, 1), 2)))
    assert OperationAxisSubelement(Operation('revolve_join'), Skewed) is None

# keeps this focused behavior isolated so regressions remain immediately visible
def TestABKTOAIPS() -> None:
    SketchA = Sketch(())
    ModelDoc = NativeModel(configurations=(), features=(), planes=(), sketches=(SketchA,), operations=(ReplaceData(Operation('join'), object_id=32),), names=(), classes=(), scalars=())
    assert NativeAxisBindings(ModelDoc) == frozenset({(32, 55, SubelementA)})

# keeps this focused behavior isolated so regressions remain immediately visible
def TestABIOWAPS() -> None:
    ModelDoc = NativeModel(configurations=(), features=(), planes=(), sketches=(), operations=(ReplaceData(Operation('join'), profile_id=None),), names=(), classes=(), scalars=())
    assert NativeAxisBindings(ModelDoc) == frozenset()
