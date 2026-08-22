# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections import Counter
import itertools as Itertools
import os as OsModule
from pathlib import Path as PathValue, PureWindowsPath
import subprocess as Subprocess
from typing import cast as CastValue
import xml.etree.ElementTree as ElementTree
import zipfile as Zipfile

import pytest as Pytest
from convert.Security.PathBoundary import ResolveTemp
from convert.Security.ProgramBoundary import GetFreecadPath
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from interchange.assembly.AssemblyData import AssemblyData
from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.TransformMatrix import TransformMatrix
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumValues import ValueKind
from interchange.payloads.PayloadRoles import PayloadRole

# this binding exists because shared behavior needs one stable value
KRandom = PathValue(__file__).parents[3] / "examples" / "Random" / "V8_engine.SLDASM"

# this binding exists because shared behavior needs one stable value
KOracle = GetFreecadPath()


# this definition exists because focused behavior needs one stable owner
@Pytest.fixture(scope="module")
def RandomDocument() -> CadDocument:
    return OpenDocument(KRandom)


# this definition exists because focused behavior needs one stable owner
def Multiply(LeftValue: TransformMatrix, Right: TransformMatrix) -> TransformMatrix:
    return TransformMatrix(
        tuple(
            sum(
                LeftValue.Values[RowValue * 4 + Index]
                * Right.Values[Index * 4 + Column]
                for Index in range(4)
            )
            for RowValue in range(4)
            for Column in range(4)
        )
    )


# this definition exists because focused behavior needs one stable owner
def ExpandedI(
    Document: CadDocument,
) -> tuple[tuple[ComponentInst, TransformMatrix], ...]:
    Assembly = Document.Assembly
    assert Assembly is not None
    Children: dict[str, list[ComponentInst]] = {}
    for Instance in Assembly.Instances:
        Children.setdefault(Instance.OwnerDefinitionId, []).append(Instance)
    Result: list[tuple[ComponentInst, TransformMatrix]] = []

    # this definition exists because focused behavior needs one stable owner
    def Visit(DefinitionId: str, Parent: TransformMatrix) -> None:
        for Instance in Children.get(DefinitionId, []):
            World = Multiply(Parent, Instance.Transform)
            Result.append((Instance, World))
            Visit(Instance.DefinitionId, World)

    Visit(Assembly.RootDefinitionId, TransformMatrix())
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def DocumentCounts(Document: CadDocument) -> tuple[int, int]:
    Sketches = len(Document.Sketches)
    Timeline = len(Document.FeatureTimeline)
    Assembly = Document.Assembly
    if Assembly is None:
        return Sketches, Timeline
    Documents = {
        ItemValue.EntityId: ItemValue.Document for ItemValue in Assembly.Documents
    }
    for Definition in Assembly.Definitions:
        Child = Documents.get(Definition.DocumentId)
        if Child is None:
            continue
        ChildSketches, ChildTimeline = DocumentCounts(Child)
        Sketches += ChildSketches
        Timeline += ChildTimeline
    return Sketches, Timeline


# this definition exists because focused behavior needs one stable owner
def PlacedMB(Document: CadDocument) -> tuple[float, ...]:
    Assembly = Document.Assembly
    assert Assembly is not None
    Definitions = {ItemValue.EntityId: ItemValue for ItemValue in Assembly.Definitions}
    Meshes = {ItemValue.EntityId: ItemValue for ItemValue in Document.Meshes}
    CornersByDefinition: dict[str, tuple[tuple[float, float, float], ...]] = {}
    for Definition in Assembly.Definitions:
        Points = [
            (Vertex.XCoord, Vertex.YCoord, Vertex.ZCoord)
            for MeshId in Definition.MeshIds
            for Vertex in Meshes[MeshId].Vertices
        ]
        if not Points:
            continue
        Minimum = tuple(min(Point[Index] for Point in Points) for Index in range(3))
        Maximum = tuple(max(Point[Index] for Point in Points) for Index in range(3))
        CornersByDefinition[Definition.EntityId] = tuple(
            Itertools.product(
                (Minimum[0], Maximum[0]),
                (Minimum[1], Maximum[1]),
                (Minimum[2], Maximum[2]),
            )
        )
    Placed = [
        World.TransformPoint(Corner)
        for Instance, World in ExpandedI(Document)
        if Definitions[Instance.DefinitionId].EntityKind == ComponentKind.KPart
        for Corner in CornersByDefinition[Instance.DefinitionId]
    ]
    return tuple(
        [min(Point[Index] for Point in Placed) for Index in range(3)]
        + [max(Point[Index] for Point in Placed) for Index in range(3)]
    )


# this helper verifies root document history geometry and payload counts
def AssertRootStats(Document: CadDocument) -> None:
    Assembly = Document.Assembly
    assert Assembly is not None
    assert (len(Document.Sketches), len(Document.FeatureTimeline)) == (3, 327)
    assert len(
        {Feature.Attributes["native_object_id"] for Feature in Document.FeatureTimeline}
    ) == len(Document.FeatureTimeline)
    assert all(
        Feature.Attributes["native_type"] and Feature.Attributes["xml_tag"]
        for Feature in Document.FeatureTimeline
    )
    assert (len(Document.Parameters), len(Document.BrepPayloads)) == (3, 15)
    assert Counter(Payload.ValueRole for Payload in Document.BrepPayloads) == {
        PayloadRole.KBrep: 12,
        PayloadRole.KAssemblyStructure: 3,
    }


# this helper verifies expanded assembly structure and source format counts
def AssertAsmStats(Document: CadDocument) -> None:
    Assembly = Document.Assembly
    assert Assembly is not None
    assert (
        len(Assembly.Definitions),
        len(Assembly.Instances),
        len(Assembly.Documents),
        len(Document.Meshes),
    ) == (68, 288, 53, 65)
    assert Counter(Definition.EntityKind for Definition in Assembly.Definitions) == {
        ComponentKind.KPart: 65,
        ComponentKind.KAssembly: 3,
    }
    Expanded = ExpandedI(Document)
    Definitions = {ItemValue.EntityId: ItemValue for ItemValue in Assembly.Definitions}
    assert len(Expanded) == 358
    assert (
        sum(
            World.IsFinite()
            and Definitions[Instance.DefinitionId].EntityKind == ComponentKind.KPart
            for Instance, World in Expanded
        )
        == 342
    )
    assert Counter(
        ItemValue.Document.Source.FormatId for ItemValue in Assembly.Documents
    ) == {
        "solidworks.sldprt": 51,
        "solidworks.sldasm": 2,
    }


# this helper verifies linked equation variables and their driven parameters
def AssertVariables(Document: CadDocument) -> None:
    Assembly = Document.Assembly
    assert Assembly is not None
    GlobalVariables = {
        (
            PathValue(str(ItemValue.Document.Source.FilePath)).name,
            Parameter.EntityName,
        ): Parameter
        for ItemValue in Assembly.Documents
        for Parameter in ItemValue.Document.Parameters
        if Parameter.EntityId.startswith("sldprt:parameter:equation:")
    }
    assert {KeyValue[1] for KeyValue in GlobalVariables} == {"d", "r1", "r2"}
    assert {KeyValue[0] for KeyValue in GlobalVariables} == {"Camshaft.SLDPRT"}
    assert {
        NameValue: GlobalVariables[("Camshaft.SLDPRT", NameValue)].Value.Value
        for NameValue in ("d", "r1", "r2")
    } == {"d": 8.0, "r1": 18.0, "r2": 10.0}
    assert all(
        Parameter.Value.EntityKind is ValueKind.KNumber
        for Parameter in GlobalVariables.values()
    )
    GlobalVariableIds = {ItemValue.EntityId for ItemValue in GlobalVariables.values()}
    Driven = [
        Parameter
        for ItemValue in Assembly.Documents
        for Parameter in ItemValue.Document.Parameters
        if Parameter.Expression is not None
        and GlobalVariableIds & set(Parameter.Expression.ParameterIds)
    ]
    assert len(Driven) == 22


# this helper verifies aggregate linked document and nested assembly data
def AssertLinkDocs(Document: CadDocument) -> None:
    Assembly = Document.Assembly
    assert Assembly is not None
    LinkedCounts = (
        sum(len(ItemValue.Document.Sketches) for ItemValue in Assembly.Documents),
        sum(
            len(ItemValue.Document.FeatureTimeline) for ItemValue in Assembly.Documents
        ),
        sum(len(ItemValue.Document.Parameters) for ItemValue in Assembly.Documents),
        sum(len(ItemValue.Document.BrepPayloads) for ItemValue in Assembly.Documents),
    )
    assert LinkedCounts == (391, 2147, 1695, 303)
    assert Counter(
        Payload.ValueRole
        for ItemValue in Assembly.Documents
        for Payload in ItemValue.Document.BrepPayloads
    ) == {
        PayloadRole.KBrep: 301,
        PayloadRole.KAssemblyStructure: 2,
    }
    assert LinkedCounts[:2] == (
        Assembly.Attributes["linked_sketch_count"],
        Assembly.Attributes["linked_feature_count"],
    )
    Nested: dict[str, AssemblyData] = {}
    for ItemValue in Assembly.Documents:
        NestedAssembly = ItemValue.Document.Assembly
        if NestedAssembly is not None:
            Nested[PureWindowsPath(ItemValue.Document.Source.FilePath).name] = (
                NestedAssembly
            )
    assert set(Nested) == {"Conrod.SLDASM", "Piston.SLDASM"}
    assert len(Nested["Conrod.SLDASM"].Mates) == 13
    assert len(Nested["Piston.SLDASM"].Mates) == 6
    assert DocumentCounts(Document) == (394, 2474)


# this test verifies the complete random assembly semantic reconstruction
def TestRAPSRCNG(
    RandomDocument: CadDocument,
) -> None:
    Document = RandomDocument
    assert Document.Source.FormatId == "solidworks.sldasm"
    assert Document.GetErrors() == ()
    AssertRootStats(Document)
    AssertAsmStats(Document)
    AssertVariables(Document)
    AssertLinkDocs(Document)


# this definition exists because focused behavior needs one stable owner
def TestRAPMMAMT(
    RandomDocument: CadDocument,
) -> None:
    Assembly = RandomDocument.Assembly
    assert Assembly is not None
    assert sum(len(MeshValue.Vertices) for MeshValue in RandomDocument.Meshes) == 492148
    assert (
        sum(len(MeshValue.Triangles) for MeshValue in RandomDocument.Meshes) == 391218
    )
    PartDefinitions = [
        ItemValue
        for ItemValue in Assembly.Definitions
        if ItemValue.EntityKind == ComponentKind.KPart
    ]
    assert len(PartDefinitions) == 65
    assert all(len(ItemValue.MeshIds) == 1 for ItemValue in PartDefinitions)
    assert {
        MeshId for ItemValue in PartDefinitions for MeshId in ItemValue.MeshIds
    } == {MeshValue.EntityId for MeshValue in RandomDocument.Meshes}
    assert (
        len(Assembly.MateEntities),
        len(Assembly.Mates),
        len(Assembly.MateGroups),
    ) == (1261, 632, 3)
    assert Counter(MateValue.OwnerDefinitionId for MateValue in Assembly.Mates) == {
        "sldasm:definition:2": 613,
        "sldasm:definition:218": 6,
        "sldasm:definition:231": 13,
    }
    assert [len(Group.MateIds) for Group in Assembly.MateGroups] == [6, 2, 9]
    for Instance in Assembly.Instances:
        Native = Instance.Attributes["native_transform"]
        if not isinstance(Native, tuple):
            raise TypeError("native transform must contain sixteen values")
        NativeItems = CastValue(tuple[object, ...], Native)
        if len(NativeItems) != 16 or not all(
            isinstance(Value, (int, float)) and not isinstance(Value, bool)
            for Value in NativeItems
        ):
            raise TypeError("native transform must contain sixteen numeric values")
        NativeValues = CastValue(tuple[float, ...], NativeItems)
        Expected = (
            NativeValues[0],
            NativeValues[4],
            NativeValues[8],
            NativeValues[12] * 1000.0,
            NativeValues[1],
            NativeValues[5],
            NativeValues[9],
            NativeValues[13] * 1000.0,
            NativeValues[2],
            NativeValues[6],
            NativeValues[10],
            NativeValues[14] * 1000.0,
            0.0,
            0.0,
            0.0,
            NativeValues[15],
        )
        assert Instance.Transform.Values == Pytest.approx(Expected, abs=1e-12)
    assert max(
        abs(Instance.Transform.Values[Index])
        for Instance in Assembly.Instances
        for Index in (3, 7, 11)
    ) == Pytest.approx(395.0340546095202)
    assert PlacedMB(RandomDocument) == Pytest.approx(
        (
            -266.5,
            -220.00028984690346,
            -275.1418883526141,
            589.9999737739564,
            455.0340560996356,
            275.1418883526132,
        ),
        abs=1e-8,
    )


# this helper reads one freecad document root from its archive
def ReadDocRoot(DocumentPath: PathValue) -> ElementTree.Element:
    with Zipfile.ZipFile(DocumentPath) as Archive:
        return ElementTree.fromstring(Archive.read("Document.xml"))


# this helper counts non profile timeline objects across emitted documents
def CountTimeline(Output: PathValue, Components: tuple[PathValue, ...]) -> int:
    TimelineCount = 0
    for DocumentPath in (Output, *Components):
        DocumentRoot = ReadDocRoot(DocumentPath)
        for ItemValue in DocumentRoot.findall("./ObjectData/Object"):
            RoleValue = ItemValue.find("./Properties/Property[@name='KitRole']/String")
            if RoleValue is not None and RoleValue.get("value") != "profile-extrusion":
                TimelineCount += 1
    return TimelineCount


# this helper extracts the root assembly link collections under test
def RootLinkData(
    RootValue: ElementTree.Element,
) -> tuple[
    tuple[ElementTree.Element, ...],
    tuple[ElementTree.Element, ...],
    set[str],
    dict[str, ElementTree.Element],
]:
    Objects = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    AssemblyLinks = tuple(
        ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
        if Objects.get(ItemValue.get("name", "")) == "Assembly::AssemblyLink"
    )
    Occurrences = tuple(
        ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
        if ItemValue.find("./Properties/Property[@name='InstanceId']") is not None
    )
    LinkedFiles: set[str] = set()
    for ItemValue in AssemblyLinks:
        LinkValue = ItemValue.find("./Properties/Property[@name='LinkedObject']/XLink")
        assert LinkValue is not None
        Filename = LinkValue.get("file")
        assert Filename is not None
        LinkedFiles.add(Filename)
    DataValue = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
    }
    return AssemblyLinks, Occurrences, LinkedFiles, DataValue


# this helper verifies every root assembly proxy targets matching component data
def AssertProxies(
    AssemblyLinks: tuple[ElementTree.Element, ...],
    DataValue: dict[str, ElementTree.Element],
    TmpPath: PathValue,
) -> None:
    ProxyCount = 0
    ComponentRoots: dict[str, ElementTree.Element] = {}
    for AssemblyLink in AssemblyLinks:
        ParentLink = AssemblyLink.find(
            "./Properties/Property[@name='LinkedObject']/XLink"
        )
        assert ParentLink is not None
        ParentFile = ParentLink.get("file")
        assert ParentFile is not None
        Children: list[ElementTree.Element] = []
        for ItemValue in AssemblyLink.findall(
            "./Properties/Property[@name='Group']/LinkList/Link"
        ):
            ChildName = ItemValue.get("value")
            assert ChildName is not None
            Children.append(DataValue[ChildName])
        assert Children
        ProxyCount += len(Children)
        ComponentRoot = ComponentRoots.get(ParentFile)
        if ComponentRoot is None:
            ComponentRoot = ReadDocRoot(TmpPath / ParentFile)
            ComponentRoots[ParentFile] = ComponentRoot
        for Child in Children:
            Linked = Child.find("./Properties/Property[@name='LinkedObject']/XLink")
            assert Linked is not None
            assert Linked.get("file") == ParentFile
            assert Linked.get("stamp") == ParentLink.get("stamp")
            LinkedName = Linked.get("name")
            assert LinkedName is not None
            Source = ComponentRoot.find(f"./ObjectData/Object[@name='{LinkedName}']")
            assert Source is not None
            assert Source.find("./Properties/Property[@name='InstanceId']") is not None
    assert ProxyCount == 80


# this helper verifies nested component links resolve to native part features
def AssertCompLinks(LinkedFiles: set[str], TmpPath: PathValue) -> None:
    for Filename in LinkedFiles:
        Component = TmpPath / PathValue(Filename)
        Restored = OpenDocument(Component)
        assert Restored.Assembly is not None
        ComponentRoot = ReadDocRoot(Component)
        Target = ComponentRoot.find(
            "./ObjectData/Object[@name='KitMetadata']/Properties/"
            "Property[@name='ExternalLinkTarget']/String"
        )
        assert Target is not None
        TargetName = Target.get("value")
        assert TargetName is not None
        TargetObject = ComponentRoot.find(f"./Objects/Object[@name='{TargetName}']")
        assert TargetObject is not None
        assert TargetObject.get("type") == "Assembly::AssemblyObject"
        ComponentTypes = {
            ItemValue.get("name", ""): ItemValue.get("type", "")
            for ItemValue in ComponentRoot.findall("./Objects/Object")
        }
        ComponentLinks = [
            ItemValue
            for ItemValue in ComponentRoot.findall("./ObjectData/Object")
            if ComponentTypes.get(ItemValue.get("name", "")) == "App::Link"
            and ItemValue.find("./Properties/Property[@name='InstanceId']") is not None
        ]
        assert ComponentLinks
        for ComponentLink in ComponentLinks:
            Linked = ComponentLink.find(
                "./Properties/Property[@name='LinkedObject']/XLink"
            )
            assert Linked is not None
            LinkedFile = Linked.get("file")
            assert LinkedFile is not None
            LinkedComponent = Component.parent / LinkedFile
            LinkedRoot = ReadDocRoot(LinkedComponent)
            LinkedName = Linked.get("name")
            assert LinkedName is not None
            LinkedTarget = LinkedRoot.find(f"./Objects/Object[@name='{LinkedName}']")
            assert LinkedTarget is not None
            assert LinkedTarget.get("type") == "Part::Feature"


# this test verifies the emitted freecad assembly and every external link
def TestRAWECF(RandomDocument: CadDocument, TmpPath: PathValue) -> None:
    Output = TmpPath / "V8_engine.FCStd"
    Result = WriteDocument(RandomDocument, Output, AllowCarrier=True)
    assert Result.IsAppUsable is True
    assert Result.IsVendorLoadable is True
    assert Result.IsNearLossless is False
    ComponentDirectory = TmpPath / "V8_engine"
    Components = tuple(ComponentDirectory.glob("*.FCStd"))
    assert len(Components) == 67
    assert Result.MetadataMap["component_file_count"] == 67
    assert CountTimeline(Output, Components) == 2474
    RootValue = ReadDocRoot(Output)
    AssemblyLinks, Occurrences, LinkedFiles, DataValue = RootLinkData(RootValue)
    AssemblyRoot = next(
        ItemValue
        for ItemValue in DataValue.values()
        if ItemValue.find("./Properties/Property[@name='RootDefinitionId']") is not None
    )
    DirectOccurrences: list[ElementTree.Element] = []
    for ItemValue in AssemblyRoot.findall(
        "./Properties/Property[@name='Group']/LinkList/Link"
    ):
        OccurrenceName = ItemValue.get("value")
        assert OccurrenceName is not None
        Occurrence = DataValue[OccurrenceName]
        if Occurrence.find("./Properties/Property[@name='InstanceId']") is not None:
            DirectOccurrences.append(Occurrence)
    assert len(AssemblyLinks) == 16
    assert len(DirectOccurrences) == 278
    assert len(Occurrences) == 358
    assert len(LinkedFiles) == 2
    assert all(Filename.startswith("V8_engine/") for Filename in LinkedFiles)
    assert {PathValue(Filename).stem.split("_", 1)[0] for Filename in LinkedFiles} == {
        "Conrod",
        "Piston",
    }
    AssertProxies(AssemblyLinks, DataValue, TmpPath)
    AssertCompLinks(LinkedFiles, TmpPath)


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.skipif(not KOracle.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def TestRAFLRAPPE(RandomDocument: CadDocument, TmpPath: PathValue) -> None:
    Output = ResolveTemp(TmpPath / "V8_engine.FCStd")
    WriteDocument(RandomDocument, Output)
    ExpectedBounds = PlacedMB(RandomDocument)
    CodeValue = """
import os
import FreeCAD as App
d=App.open(os.environ['KIT_ORACLE_PATH'])
root=next(o for o in d.Objects if o.TypeId=='Assembly::AssemblyObject' and hasattr(o,'RootDefinitionId') and o.RootDefinitionId=='sldasm:definition:2')
d.recompute()
first_links=tuple(sorted(o.Name for o in d.Objects if o.TypeId in ('App::Link','Assembly::AssemblyLink')))
d.recompute()
links=[o for o in d.Objects if o.TypeId in ('App::Link','Assembly::AssemblyLink')]
stable_links=first_links==tuple(sorted(o.Name for o in links))
leaf=[o for o in links if o.TypeId=='App::Link' and hasattr(o,'Shape') and not o.Shape.isNull()]
sources={{(o.getLinkedObject(True).Document.Name,o.getLinkedObject(True).Name):o.getLinkedObject(True) for o in leaf}}
points=[]
for link in leaf:
    box=link.getLinkedObject(True).Shape.BoundBox
    placement=link.Placement
    parent=link.getParentGeoFeatureGroup()
    while parent is not None and parent != root:
        placement=parent.Placement*placement
        parent=parent.getParentGeoFeatureGroup()
    for x in (box.XMin,box.XMax):
        for y in (box.YMin,box.YMax):
            for z in (box.ZMin,box.ZMax):
                point=placement.multVec(App.Vector(x,y,z))
                points.append((point.x,point.y,point.z))
bounds=tuple([min(point[index] for point in points) for index in range(3)]+[max(point[index] for point in points) for index in range(3)])
documents=tuple(App.listDocuments().values())
breps=[o for document in documents for o in document.Objects if o.TypeId=='Part::Feature' and getattr(o,'Representation','')=='faceted']
sketches=[o for document in documents for o in document.Objects if o.TypeId=='Sketcher::SketchObject']
timeline=[o for document in documents for o in document.Objects if hasattr(o,'KitRole') and o.KitRole!='profile-extrusion']
mates=[o for o in d.Objects if hasattr(o,'MateId')]
all_mates=[o for document in documents for o in document.Objects if hasattr(o,'MateId')]
active_mates=[o for o in all_mates if not o.Suppressed]
valid_mates=all(o.Reference1[0] is not None and o.Reference2[0] is not None for o in active_mates)
mate_groups=[o for document in documents for o in document.Objects if hasattr(o,'MateGroupId')]
assemblies=[o for document in documents for o in document.Objects if o.TypeId=='Assembly::AssemblyObject']
print('KIT_RANDOM',len(documents),len(links),len(leaf),len(sources),len(breps),sum(len(o.Shape.Faces) for o in breps),sum(o.Shape.isValid() for o in breps),len(sketches),len(timeline),len(mates),len(all_mates),len(mate_groups),len(assemblies),stable_links,valid_mates,*bounds,flush=True)
"""
    OracleEnv = OsModule.environ.copy()
    OracleEnv["KIT_ORACLE_PATH"] = str(Output)
    Completed = Subprocess.run(
        [str(KOracle), "-c", CodeValue],
        capture_output=True,
        env=OracleEnv,
        text=True,
        timeout=300,
    )
    OutputText = Completed.stdout + Completed.stderr
    assert Completed.returncode == 0, OutputText[-8000:]
    for Message in (
        "The graph must be a DAG",
        "links are out of scope",
        "pending remove",
        "Time stamp changed on link",
    ):
        assert Message not in OutputText
    Lines = [
        Value
        for Value in Completed.stdout.splitlines()
        if Value.startswith("KIT_RANDOM")
    ]
    assert Lines, Completed.stdout[-4000:] + Completed.stderr[-4000:]
    LineValue = Lines[-1]
    Values = LineValue.split()[1:]
    assert tuple(int(Value) for Value in Values[:13]) == (
        68,
        358,
        342,
        65,
        65,
        391218,
        65,
        394,
        2474,
        613,
        632,
        3,
        3,
    )
    assert Values[13:15] == ["True", "True"]
    assert tuple(float(Value) for Value in Values[15:]) == Pytest.approx(
        ExpectedBounds, abs=1e-4
    )
    assert "Errors in neighbourhood of mesh found" not in OutputText
