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
import xml.etree.ElementTree as ElementTree
import zipfile as Zipfile

import pytest as Pytest

from convert import open_document as OpenDocument, write_document as WriteDocument
from interchange import (
    CadDocument,
    ComponentKind,
    Matrix4 as MatrixFour,
    PayloadRole,
    ValueKind,
)

# this binding exists because shared behavior needs one stable value
KRandom = PathValue(__file__).parents[3] / "examples" / "Random" / "V8_engine.SLDASM"

# this binding exists because shared behavior needs one stable value
KOracle = PathValue(OsModule.environ.get("KIT_FREECAD_ORACLE", ""))


# this definition exists because focused behavior needs one stable owner
@Pytest.fixture(scope="module")
def RandomDocument() -> CadDocument:
    return OpenDocument(KRandom)


# this definition exists because focused behavior needs one stable owner
def Multiply(LeftValue: MatrixFour, Right: MatrixFour) -> MatrixFour:
    return MatrixFour(
        tuple(
            sum(
                LeftValue.values[RowValue * 4 + Index]
                * Right.values[Index * 4 + Column]
                for Index in range(4)
            )
            for RowValue in range(4)
            for Column in range(4)
        )
    )


# this definition exists because focused behavior needs one stable owner
def ExpandedI(
    Document: CadDocument,
) -> tuple[tuple[object, MatrixFour], ...]:
    Assembly = Document.assembly
    assert Assembly is not None
    Children: dict[str, list[object]] = {}
    for Instance in Assembly.instances:
        Children.setdefault(Instance.owner_definition_id, []).append(Instance)
    Result: list[tuple[object, MatrixFour]] = []

    # this definition exists because focused behavior needs one stable owner
    def Visit(DefinitionId: str, Parent: MatrixFour) -> None:
        for Instance in Children.get(DefinitionId, []):
            World = Multiply(Parent, Instance.transform)
            Result.append((Instance, World))
            Visit(Instance.definition_id, World)

    Visit(Assembly.root_definition_id, MatrixFour())
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def DocumentCounts(Document: CadDocument) -> tuple[int, int]:
    Sketches = len(Document.sketches)
    Timeline = len(Document.feature_timeline)
    Assembly = Document.assembly
    if Assembly is None:
        return Sketches, Timeline
    Documents = {ItemValue.id: ItemValue.document for ItemValue in Assembly.documents}
    for Definition in Assembly.definitions:
        Child = Documents.get(Definition.document_id)
        if Child is None:
            continue
        ChildSketches, ChildTimeline = DocumentCounts(Child)
        Sketches += ChildSketches
        Timeline += ChildTimeline
    return Sketches, Timeline


# this definition exists because focused behavior needs one stable owner
def PlacedMB(Document: CadDocument) -> tuple[float, ...]:
    Assembly = Document.assembly
    assert Assembly is not None
    Definitions = {ItemValue.id: ItemValue for ItemValue in Assembly.definitions}
    Meshes = {ItemValue.id: ItemValue for ItemValue in Document.meshes}
    CornersByDefinition: dict[str, tuple[tuple[float, float, float], ...]] = {}
    for Definition in Assembly.definitions:
        Points = [
            (Vertex.x, Vertex.y, Vertex.z)
            for MeshId in Definition.mesh_ids
            for Vertex in Meshes[MeshId].vertices
        ]
        if not Points:
            continue
        Minimum = tuple(min(Point[Index] for Point in Points) for Index in range(3))
        Maximum = tuple(max(Point[Index] for Point in Points) for Index in range(3))
        CornersByDefinition[Definition.id] = tuple(
            Itertools.product(
                (Minimum[0], Maximum[0]),
                (Minimum[1], Maximum[1]),
                (Minimum[2], Maximum[2]),
            )
        )
    Placed = [
        World.transform_point(Corner)
        for Instance, World in ExpandedI(Document)
        if Definitions[Instance.definition_id].kind == ComponentKind.PART
        for Corner in CornersByDefinition[Instance.definition_id]
    ]
    return tuple(
        [min(Point[Index] for Point in Placed) for Index in range(3)]
        + [max(Point[Index] for Point in Placed) for Index in range(3)]
    )


# this helper verifies root document history geometry and payload counts
def AssertRootStats(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert (len(Document.sketches), len(Document.feature_timeline)) == (3, 327)
    assert len(
        {
            Feature.attributes["native_object_id"]
            for Feature in Document.feature_timeline
        }
    ) == len(Document.feature_timeline)
    assert all(
        Feature.attributes["native_type"] and Feature.attributes["xml_tag"]
        for Feature in Document.feature_timeline
    )
    assert (len(Document.parameters), len(Document.brep_payloads)) == (3, 15)
    assert Counter(Payload.role for Payload in Document.brep_payloads) == {
        PayloadRole.BREP: 12,
        PayloadRole.ASSEMBLY_STRUCTURE: 3,
    }


# this helper verifies expanded assembly structure and source format counts
def AssertAsmStats(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert (
        len(Assembly.definitions),
        len(Assembly.instances),
        len(Assembly.documents),
        len(Document.meshes),
    ) == (68, 288, 53, 65)
    assert Counter(Definition.kind for Definition in Assembly.definitions) == {
        ComponentKind.PART: 65,
        ComponentKind.ASSEMBLY: 3,
    }
    Expanded = ExpandedI(Document)
    Definitions = {ItemValue.id: ItemValue for ItemValue in Assembly.definitions}
    assert len(Expanded) == 358
    assert (
        sum(
            Definitions[Instance.definition_id].kind == ComponentKind.PART
            for Instance, ValueA in Expanded
        )
        == 342
    )
    assert Counter(
        ItemValue.document.source.format_id for ItemValue in Assembly.documents
    ) == {
        "solidworks.sldprt": 51,
        "solidworks.sldasm": 2,
    }


# this helper verifies linked equation variables and their driven parameters
def AssertVariables(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    GlobalVariables = {
        (PathValue(str(ItemValue.document.source.path)).name, Parameter.name): Parameter
        for ItemValue in Assembly.documents
        for Parameter in ItemValue.document.parameters
        if Parameter.id.startswith("sldprt:parameter:equation:")
    }
    assert {KeyValue[1] for KeyValue in GlobalVariables} == {"d", "r1", "r2"}
    assert {KeyValue[0] for KeyValue in GlobalVariables} == {"Camshaft.SLDPRT"}
    assert {
        NameValue: GlobalVariables[("Camshaft.SLDPRT", NameValue)].value.value
        for NameValue in ("d", "r1", "r2")
    } == {"d": 8.0, "r1": 18.0, "r2": 10.0}
    assert all(
        Parameter.value.kind is ValueKind.NUMBER
        for Parameter in GlobalVariables.values()
    )
    GlobalVariableIds = {ItemValue.id for ItemValue in GlobalVariables.values()}
    Driven = [
        Parameter
        for ItemValue in Assembly.documents
        for Parameter in ItemValue.document.parameters
        if Parameter.expression is not None
        and GlobalVariableIds & set(Parameter.expression.parameter_ids)
    ]
    assert len(Driven) == 22


# this helper verifies aggregate linked document and nested assembly data
def AssertLinkDocs(Document: CadDocument) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    LinkedCounts = (
        sum(len(ItemValue.document.sketches) for ItemValue in Assembly.documents),
        sum(
            len(ItemValue.document.feature_timeline) for ItemValue in Assembly.documents
        ),
        sum(len(ItemValue.document.parameters) for ItemValue in Assembly.documents),
        sum(len(ItemValue.document.brep_payloads) for ItemValue in Assembly.documents),
    )
    assert LinkedCounts == (391, 2147, 1695, 303)
    assert Counter(
        Payload.role
        for ItemValue in Assembly.documents
        for Payload in ItemValue.document.brep_payloads
    ) == {
        PayloadRole.BREP: 301,
        PayloadRole.ASSEMBLY_STRUCTURE: 2,
    }
    assert LinkedCounts[:2] == (
        Assembly.attributes["linked_sketch_count"],
        Assembly.attributes["linked_feature_count"],
    )
    Nested = {
        PureWindowsPath(
            ItemValue.document.source.path
        ).name: ItemValue.document.assembly
        for ItemValue in Assembly.documents
        if ItemValue.document.assembly is not None
    }
    assert set(Nested) == {"Conrod.SLDASM", "Piston.SLDASM"}
    assert len(Nested["Conrod.SLDASM"].mates) == 13
    assert len(Nested["Piston.SLDASM"].mates) == 6
    assert DocumentCounts(Document) == (394, 2474)


# this test verifies the complete random assembly semantic reconstruction
def TestRAPSRCNG(
    RandomDocument: CadDocument,
) -> None:
    Document = RandomDocument
    assert Document.source.format_id == "solidworks.sldasm"
    assert Document.validate() == ()
    AssertRootStats(Document)
    AssertAsmStats(Document)
    AssertVariables(Document)
    AssertLinkDocs(Document)


# this definition exists because focused behavior needs one stable owner
def TestRAPMMAMT(
    RandomDocument: CadDocument,
) -> None:
    Assembly = RandomDocument.assembly
    assert Assembly is not None
    assert sum(len(MeshValue.vertices) for MeshValue in RandomDocument.meshes) == 492148
    assert (
        sum(len(MeshValue.triangles) for MeshValue in RandomDocument.meshes) == 391218
    )
    PartDefinitions = [
        ItemValue
        for ItemValue in Assembly.definitions
        if ItemValue.kind == ComponentKind.PART
    ]
    assert len(PartDefinitions) == 65
    assert all(len(ItemValue.mesh_ids) == 1 for ItemValue in PartDefinitions)
    assert {
        MeshId for ItemValue in PartDefinitions for MeshId in ItemValue.mesh_ids
    } == {MeshValue.id for MeshValue in RandomDocument.meshes}
    assert (
        len(Assembly.mate_entities),
        len(Assembly.mates),
        len(Assembly.mate_groups),
    ) == (1261, 632, 3)
    assert Counter(MateValue.owner_definition_id for MateValue in Assembly.mates) == {
        "sldasm:definition:2": 613,
        "sldasm:definition:218": 6,
        "sldasm:definition:231": 13,
    }
    assert [len(Group.mate_ids) for Group in Assembly.mate_groups] == [6, 2, 9]
    for Instance in Assembly.instances:
        Native = Instance.attributes["native_transform"]
        Expected = (
            Native[0],
            Native[4],
            Native[8],
            Native[12] * 1000.0,
            Native[1],
            Native[5],
            Native[9],
            Native[13] * 1000.0,
            Native[2],
            Native[6],
            Native[10],
            Native[14] * 1000.0,
            0.0,
            0.0,
            0.0,
            Native[15],
        )
        assert Instance.transform.values == Pytest.approx(Expected, abs=1e-12)
    assert max(
        abs(Instance.transform.values[Index])
        for Instance in Assembly.instances
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
def RootLinkData(RootValue: ElementTree.Element):
    Objects = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    AssemblyLinks = [
        ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
        if Objects.get(ItemValue.get("name", "")) == "Assembly::AssemblyLink"
    ]
    Occurrences = [
        ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
        if ItemValue.find("./Properties/Property[@name='InstanceId']") is not None
    ]
    LinkedFiles = {
        ItemValue.find("./Properties/Property[@name='LinkedObject']/XLink").get("file")
        for ItemValue in AssemblyLinks
    }
    DataValue = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
    }
    return AssemblyLinks, Occurrences, LinkedFiles, DataValue, DirectOccurrences


# this helper verifies every root assembly proxy targets matching component data
def AssertProxies(AssemblyLinks, DataValue, TmpPath: PathValue) -> None:
    ProxyCount = 0
    ComponentRoots: dict[str, ElementTree.Element] = {}
    for AssemblyLink in AssemblyLinks:
        ParentLink = AssemblyLink.find(
            "./Properties/Property[@name='LinkedObject']/XLink"
        )
        Children = [
            DataValue[ItemValue.get("value")]
            for ItemValue in AssemblyLink.findall(
                "./Properties/Property[@name='Group']/LinkList/Link"
            )
        ]
        assert Children
        ProxyCount += len(Children)
        ComponentRoot = ComponentRoots.get(ParentLink.get("file"))
        if ComponentRoot is None:
            ComponentRoot = ReadDocRoot(TmpPath / PathValue(ParentLink.get("file")))
            ComponentRoots[ParentLink.get("file")] = ComponentRoot
        for Child in Children:
            Linked = Child.find("./Properties/Property[@name='LinkedObject']/XLink")
            assert Linked.get("file") == ParentLink.get("file")
            assert Linked.get("stamp") == ParentLink.get("stamp")
            Source = ComponentRoot.find(
                f"./ObjectData/Object[@name='{Linked.get('name')}']"
            )
            assert Source is not None
            assert Source.find("./Properties/Property[@name='InstanceId']") is not None
    assert ProxyCount == 80


# this helper verifies nested component links resolve to native part features
def AssertCompLinks(LinkedFiles, TmpPath: PathValue) -> None:
    for Filename in LinkedFiles:
        Component = TmpPath / PathValue(Filename)
        Restored = OpenDocument(Component)
        assert Restored.assembly is not None
        ComponentRoot = ReadDocRoot(Component)
        Target = ComponentRoot.find(
            "./ObjectData/Object[@name='KitMetadata']/Properties/"
            "Property[@name='ExternalLinkTarget']/String"
        )
        assert Target is not None
        TargetObject = ComponentRoot.find(
            f"./Objects/Object[@name='{Target.get('value')}']"
        )
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
            assert Linked.get("file")
            LinkedComponent = Component.parent / Linked.get("file")
            LinkedRoot = ReadDocRoot(LinkedComponent)
            LinkedTarget = LinkedRoot.find(
                f"./Objects/Object[@name='{Linked.get('name')}']"
            )
            assert LinkedTarget is not None
            assert LinkedTarget.get("type") == "Part::Feature"


# this test verifies the emitted freecad assembly and every external link
def TestRAWECF(RandomDocument: CadDocument, TmpPath: PathValue) -> None:
    Output = TmpPath / "V8_engine.FCStd"
    Result = WriteDocument(RandomDocument, Output, allow_carrier=True)
    assert Result.application_usable is True
    assert Result.vendor_loadable is True
    assert Result.near_lossless is False
    ComponentDirectory = TmpPath / "V8_engine"
    Components = tuple(ComponentDirectory.glob("*.FCStd"))
    assert len(Components) == 67
    assert Result.metadata["component_file_count"] == 67
    assert CountTimeline(Output, Components) == 2474
    RootValue = ReadDocRoot(Output)
    AssemblyLinks, Occurrences, LinkedFiles, DataValue, DirectOccurrences = (
        RootLinkData(RootValue)
    )
    AssemblyRoot = next(
        ItemValue
        for ItemValue in DataValue.values()
        if ItemValue.find("./Properties/Property[@name='RootDefinitionId']") is not None
    )
    DirectOccurrences = [
        DataValue[ItemValue.get("value")]
        for ItemValue in AssemblyRoot.findall(
            "./Properties/Property[@name='Group']/LinkList/Link"
        )
        if DataValue[ItemValue.get("value")].find(
            "./Properties/Property[@name='InstanceId']"
        )
        is not None
    ]
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
    Output = TmpPath / "V8_engine.FCStd"
    WriteDocument(RandomDocument, Output)
    ExpectedBounds = PlacedMB(RandomDocument)
    CodeValue = f"""
import FreeCAD as App
d=App.open(r'{Output}')
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
    Completed = Subprocess.run(
        [str(KOracle), "-c", CodeValue],
        capture_output=True,
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
