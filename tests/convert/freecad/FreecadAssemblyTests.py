# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import replace as Replace
import json as JsonValue
import os as OsModule
from pathlib import Path as FilePath
import struct as Struct
import subprocess as Subprocess
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile
import pytest as Pytest
from convert.adapters.freecad import read_freecad as ReadFreecad, write_freecad as WriteFreecad
from interchange import CadSource, ComponentDocument as ComponentDoc, MateKind, Matrix4 as MatrixFour, Mesh as MeshRecord, Vector3 as VectorThree
from tests.interchange.assembly.AssemblyTests import assembly_document as InterchangeAsmDoc
from tests.interchange.document.DocumentTests import document as DocValue

# this binding exists because shared behavior needs one stable value
KOracle = FilePath(OsModule.environ.get('KIT_FREECAD_ORACLE', ''))

# this definition exists because focused behavior needs one stable owner
def AsmDoc():
    Source = InterchangeAsmDoc()
    AsmValue = Source.assembly
    assert AsmValue is not None
    Mates = tuple((Replace(MateValue, kind=MateKind.LOCK) for MateValue in AsmValue.mates))
    return Replace(Source, assembly=Replace(AsmValue, mates=Mates))

# this definition exists because focused behavior needs one stable owner
def PropAction(NodeValue: ET.Element, NameValue: str) -> XmlTree.Element:
    Result = NodeValue.find(f"./Properties/Property[@name='{NameValue}']")
    assert Result is not None
    return Result

# this definition exists because focused behavior needs one stable owner
def MeshDoc():
    Source = AsmDoc()
    AsmValue = Source.assembly
    assert AsmValue is not None
    MeshValue = MeshRecord('mesh:part', 'Part geometry', (VectorThree(0.0, 0.0, 0.0), VectorThree(1.0, 0.0, 0.0), VectorThree(0.0, 1.0, 0.0), VectorThree(1.0, 1.0, 0.0)), ((0, 1, 2), (2, 1, 3)))
    Definitions = list(AsmValue.definitions)
    Definitions[2] = Replace(Definitions[2], document_id='', body_ids=(), mesh_ids=(MeshValue.id,))
    PartInstance = Replace(AsmValue.instances[1], owner_definition_id=AsmValue.root_definition_id, transform=AsmValue.instances[0].transform)
    Entities = tuple((Replace(Entity, instance_path=(PartInstance.id,)) if Index else Entity for Index, Entity in enumerate(AsmValue.mate_entities)))
    return Replace(Source, meshes=(MeshValue,), assembly=Replace(AsmValue, definitions=tuple(Definitions), instances=(PartInstance,), documents=(), mate_entities=Entities))

# this definition exists because focused behavior needs one stable owner
def NestedAsmDoc():
    Source = AsmDoc()
    AsmValue = Source.assembly
    assert AsmValue is not None
    PartMesh = MeshRecord('mesh:nested-part', 'Nested part geometry', (VectorThree(0.0, 0.0, 0.0), VectorThree(1.0, 0.0, 0.0), VectorThree(0.0, 1.0, 0.0)), ((0, 1, 2),))
    PartDoc = Replace(AsmValue.documents[0].document, meshes=(PartMesh,))
    PartLink = Replace(AsmValue.documents[0], document=PartDoc)
    NestedAsm = Replace(AsmValue, root_definition_id='definition:subassembly', definitions=tuple((ItemValue for ItemValue in AsmValue.definitions if ItemValue.id in {'definition:subassembly', 'definition:part'})), instances=(AsmValue.instances[1],), documents=(PartLink,), mate_entities=(), mates=(), mate_groups=())
    Nested = Replace(DocValue(), source=CadSource('test.assembly', 'nested', '2' * 64), assembly=NestedAsm)
    Definitions = tuple((Replace(ItemValue, document_id='document:subassembly') if ItemValue.id == 'definition:subassembly' else ItemValue for ItemValue in AsmValue.definitions))
    return Replace(Source, assembly=Replace(AsmValue, definitions=Definitions, documents=(PartLink, ComponentDoc('document:subassembly', Nested))))

# this definition exists because focused behavior needs one stable owner
def GeomFree(Source):
    AsmValue = Source.assembly
    if AsmValue is not None:
        AsmValue = Replace(AsmValue, definitions=tuple((Replace(ItemValue, body_ids=()) for ItemValue in AsmValue.definitions)), documents=tuple((Replace(ItemValue, document=GeomFree(ItemValue.document)) for ItemValue in AsmValue.documents)))
    return Replace(Source, parameters=(), support_planes=(), sketches=(), selections=(), feature_timeline=(), bodies=(), meshes=Source.meshes or (MeshRecord('mesh:geometry-free', 'Geometry', (VectorThree(0.0, 0.0, 0.0), VectorThree(1.0, 0.0, 0.0), VectorThree(0.0, 1.0, 0.0)), ((0, 1, 2),)),), assembly=AsmValue)

# this definition exists because focused behavior needs one stable owner
def TestFcstdAsmHas(TmpPath) -> None:
    Output = TmpPath / 'assembly.FCStd'
    WriteFreecad(AsmDoc(), Output)
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
    Objects = RootValue.findall('./Objects/Object')
    Types = [ItemValue.get('type') for ItemValue in Objects]
    assert Types.count('Assembly::AssemblyObject') == 1
    assert Types.count('Assembly::JointGroup') == 1
    assert Types.count('App::Origin') == 1
    Links = [ItemValue for ItemValue in Objects if ItemValue.get('type') == 'App::Link']
    assert len(Links) == 1
    DataValue = {ItemValue.get('name', ''): ItemValue for ItemValue in RootValue.findall('./ObjectData/Object')}
    LinkData = [DataValue[ItemValue.get('name', '')] for ItemValue in Links]
    assert all((PropAction(ItemValue, 'LinkTransform').find('Bool').get('value') == 'true' for ItemValue in LinkData))
    Placement = PropAction(LinkData[0], 'Placement').find('PropertyPlacement')
    assert Placement is not None
    assert (float(Placement.get('Px', '0')), float(Placement.get('Py', '0')), float(Placement.get('Pz', '0'))) == Pytest.approx((100.0, 20.0, 30.0))
    MateValue = next((ItemValue for ItemValue in DataValue.values() if ItemValue.find("./Properties/Property[@name='MateId']") is not None))
    JointType = PropAction(MateValue, 'JointType').find('Integer')
    EntityIds = PropAction(MateValue, 'EntityIds').findall('./StringList/String')
    ComponentLinks = PropAction(MateValue, 'ComponentLinks').findall('./StringList/String')
    assert JointType is not None and JointType.get('value') == '0'
    Proxy = PropAction(MateValue, 'Proxy').find('Python')
    assert Proxy is not None
    assert Proxy.attrib == {'value': 'bnVsbA==', 'encoded': 'yes', 'module': 'JointObject', 'class': 'Joint'}
    assert [ItemValue.get('value') for ItemValue in EntityIds] == ['mate-entity:assembly', 'mate-entity:part']
    AsmRoot = next((ItemValue for ItemValue in DataValue.values() if ItemValue.find("./Properties/Property[@name='RootDefinitionId']") is not None))
    RootOrigin = PropAction(AsmRoot, 'Origin').find('Link').get('value')
    assert len(ComponentLinks) == 2
    assert ComponentLinks[0].get('value') == RootOrigin
    RefOne = PropAction(MateValue, 'Reference1').find('XLink')
    RefTwo = PropAction(MateValue, 'Reference2').find('XLink')
    assert RefOne is not None
    assert RefTwo is not None
    assert RefOne.get('name') == RootOrigin
    assert RefTwo.get('name') == Links[0].get('name')
    assert [ItemValue.get('value') for ItemValue in RefOne.findall('Sub')] == ['', '']
    assert PropAction(MateValue, 'Suppressed').find('Bool').get('value') == 'false'
    assert PropAction(MateValue, 'Detach1').find('Bool').get('value') == 'false'
    assert PropAction(MateValue, 'Detach2').find('Bool').get('value') == 'false'
    assert PropAction(AsmRoot, 'OccurrenceCount').find('Integer').get('value') == '1'
    RootChildren = {ItemValue.get('value') for ItemValue in PropAction(AsmRoot, 'Group').findall('./LinkList/Link')}
    MetaGroups = {NameValue for NameValue in DataValue if NameValue.endswith(('_Definitions', '_Components', '_MateEntities'))}
    assert MetaGroups.isdisjoint(RootChildren)

# this definition exists because focused behavior needs one stable owner
def TestFcstdMate(TmpPath) -> None:
    Source = AsmDoc()
    AsmValue = Source.assembly
    assert AsmValue is not None
    Frame = MatrixFour((1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 2.0, 0.0, 0.0, 1.0, 3.0, 0.0, 0.0, 0.0, 1.0))
    TargetPath = AsmValue.mate_entities[1].instance_path
    Entities = (Replace(AsmValue.mate_entities[0], instance_path=TargetPath, source_entity_id='Face1', frame=Frame), Replace(AsmValue.mate_entities[1], source_entity_id='', frame=Frame))
    Source = Replace(Source, assembly=Replace(AsmValue, mate_entities=Entities))
    Output = TmpPath / 'connector_state.FCStd'
    WriteFreecad(Source, Output)
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
    MateValue = next((ItemValue for ItemValue in RootValue.findall('./ObjectData/Object') if ItemValue.find("./Properties/Property[@name='MateId']") is not None))
    RefOne = PropAction(MateValue, 'Reference1').find('XLink')
    RefTwo = PropAction(MateValue, 'Reference2').find('XLink')
    assert RefOne is not None
    assert RefTwo is not None
    assert RefOne.get('name') == RefTwo.get('name')
    assert [ItemValue.get('value') for ItemValue in RefOne.findall('Sub')] == ['Face1', 'Face1']
    assert [ItemValue.get('value') for ItemValue in RefTwo.findall('Sub')] == ['', '']
    assert PropAction(MateValue, 'Detach1').find('Bool').get('value') == 'false'
    assert PropAction(MateValue, 'Detach2').find('Bool').get('value') == 'true'
    assert PropAction(MateValue, 'Suppressed').find('Bool').get('value') == 'false'
    ComponentLinks = PropAction(MateValue, 'ComponentLinks').findall('./StringList/String')
    assert len(ComponentLinks) == 1

# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize('KindValue', (MateKind.COINCIDENT, MateKind.TANGENT, MateKind.COORDINATE, MateKind.UNIVERSAL_JOINT, MateKind.CAM, MateKind.SLOT, MateKind.WIDTH, MateKind.SYMMETRIC, MateKind.LINEAR_COUPLER, MateKind.PATH, MateKind.MAGNETIC, MateKind.PROFILE_CENTER, MateKind.NATIVE))
def TestFcstdMates(TmpPath, KindValue: MateKind) -> None:
    Source = GeomFree(AsmDoc())
    AsmValue = Source.assembly
    assert AsmValue is not None
    Source = Replace(Source, assembly=Replace(AsmValue, mates=(Replace(AsmValue.mates[0], kind=KindValue),)))
    Output = TmpPath / f'{KindValue.value}.FCStd'
    WriteFreecad(Source, Output)
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
    Carrier = next((ItemValue for ItemValue in RootValue.findall('./ObjectData/Object') if ItemValue.find("./Properties/Property[@name='MateId']") is not None))
    Marker = PropAction(Carrier, 'KitMateCarrier').find('Bool')
    MateType = PropAction(Carrier, 'MateType').find('String')
    Stored = PropAction(Carrier, 'MateDataJSON').find('String')
    assert Marker is not None and Marker.get('value') == 'true'
    assert MateType is not None and MateType.get('value') == KindValue.value
    assert Stored is not None
    assert JsonValue.loads(Stored.get('value', ''))['kind']['value'] == KindValue.value
    assert Carrier.find("./Properties/Property[@name='JointType']") is None
    assert Carrier.find("./Properties/Property[@name='Suppressed']") is None
    assert Carrier.find("./Properties/Property[@name='Proxy']") is None
    assert PropAction(Carrier, 'Reference1').find('XLink') is not None
    assert PropAction(Carrier, 'Reference2').find('XLink') is not None
    assert ReadFreecad(Output) == Source

# this definition exists because focused behavior needs one stable owner
def TestFcstdAsm(TmpPath) -> None:
    Source = MeshDoc()
    Output = TmpPath / 'mesh_assembly.FCStd'
    WriteFreecad(Source, Output)
    Component = TmpPath / 'mesh_assembly' / 'Piston.FCStd'
    with Zipfile.ZipFile(Component) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
        MeshValue = next((ItemValue for ItemValue in RootValue.findall('./Objects/Object') if ItemValue.get('type') == 'Mesh::Feature'))
        DataValue = next((ItemValue for ItemValue in RootValue.findall('./ObjectData/Object') if ItemValue.get('name') == MeshValue.get('name')))
        BrepValue = PropAction(DataValue, 'BRep').find('Link').get('value')
        Target = RootValue.find("./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='ExternalLinkTarget']/String").get('value')
        TargetData = RootValue.find(f"./ObjectData/Object[@name='{Target}']")
        TargetDependencies = next((ItemValue for ItemValue in RootValue.findall('./Objects/ObjectDeps') if ItemValue.get('Name') == Target))
        FileName = PropAction(DataValue, 'Mesh').find('Mesh').get('file')
        Payload = Archive.read(FileName)
    assert Target == BrepValue
    TargetGroups = {PropAction(TargetData, NameValue).find('Link').get('value') for NameValue in ('Sketches', 'FeatureTimeline')}
    assert TargetGroups.issubset({ItemValue.get('Name') for ItemValue in TargetDependencies.findall('Dep')})
    assert PropAction(DataValue, 'Visibility').find('Bool').get('value') == 'true'
    Magic, Version = Struct.unpack_from('<II', Payload)
    VertexCount, TriangleCount = Struct.unpack_from('<II', Payload, 264)
    FirstTriangle = Struct.unpack_from('<iiiiii', Payload, 320)
    SecondTriangle = Struct.unpack_from('<iiiiii', Payload, 344)
    assert (Magic, Version) == (2695938256, 65536)
    assert (VertexCount, TriangleCount) == (4, 2)
    assert FirstTriangle == (0, 1, 2, -1, 1, -1)
    assert SecondTriangle == (2, 1, 3, 0, -1, -1)

# this definition exists because focused behavior needs one stable owner
def TestFcstdKeeps(TmpPath) -> None:
    Source = AsmDoc()
    AsmValue = Source.assembly
    assert AsmValue is not None
    FirstSubassembly = AsmValue.instances[0]
    SecondSubassembly = Replace(FirstSubassembly, id='instance:subassembly:2', name='Piston-2', order=1)
    Entities = tuple((Replace(Entity, owner_definition_id='definition:subassembly', instance_path=('instance:part',) if Index else ()) for Index, Entity in enumerate(AsmValue.mate_entities)))
    MateValue = Replace(AsmValue.mates[0], owner_definition_id='definition:subassembly')
    Source = Replace(Source, assembly=Replace(AsmValue, instances=(FirstSubassembly, SecondSubassembly, AsmValue.instances[1]), mate_entities=Entities, mates=(MateValue,)))
    Output = TmpPath / 'repeated.FCStd'
    WriteFreecad(Source, Output)
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
    DataValue = RootValue.findall('./ObjectData/Object')
    Mates = [ItemValue for ItemValue in DataValue if ItemValue.find("./Properties/Property[@name='MateId']") is not None]
    assert Mates == []
    AsmRoot = next((ItemValue for ItemValue in DataValue if ItemValue.find("./Properties/Property[@name='RootDefinitionId']") is not None))
    assert PropAction(AsmRoot, 'MateCount').find('Integer').get('value') == '0'
    Restored = ReadFreecad(Output)
    assert Restored.assembly is not None
    assert Restored.assembly.mates == (MateValue,)
    assert Restored.assembly.mate_entities == Entities

# this definition exists because focused behavior needs one stable owner
def TestFcstdNesteA(TmpPath) -> None:
    Source = GeomFree(NestedAsmDoc())
    AsmValue = Source.assembly
    assert AsmValue is not None
    Documents = list(AsmValue.documents)
    NestedIndex = next((Index for Index, ItemValue in enumerate(Documents) if ItemValue.document.assembly is not None))
    NestedDoc = Documents[NestedIndex].document
    NestedAsm = NestedDoc.assembly
    assert NestedAsm is not None
    NestedInstance = NestedAsm.instances[0]
    CustomInstance = Replace(NestedInstance, attributes={'freecad': {'name': 'CustomPartLink', 'type_id': 'Vendor::DerivedLink', 'properties': {'LinkedObject': {}, 'LinkPlacement': {}, 'LinkTransform': {}}}})
    NestedDoc = Replace(NestedDoc, assembly=Replace(NestedAsm, instances=(CustomInstance,)))
    Documents[NestedIndex] = Replace(Documents[NestedIndex], document=NestedDoc)
    Source = Replace(Source, assembly=Replace(AsmValue, documents=tuple(Documents)))
    Output = TmpPath / 'structural_links.FCStd'
    WriteFreecad(Source, Output)
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
    DeclValue = next((ItemValue for ItemValue in RootValue.findall('./Objects/Object') if ItemValue.get('type') == 'Vendor::DerivedLink'))
    DataValue = RootValue.find(f"./ObjectData/Object[@name='{DeclValue.get('name')}']")
    assert DataValue is not None
    assert PropAction(DataValue, 'LinkedObject').find('XLink') is not None
    AsmLink = next((ItemValue for ItemValue in RootValue.findall('./ObjectData/Object') if ItemValue.find("./Properties/Property[@name='Rigid']") is not None and ItemValue.find("./Properties/Property[@name='LinkedObject']") is not None))
    Group = PropAction(AsmLink, 'Group').findall('./LinkList/Link')
    assert DeclValue.get('name') in {ItemValue.get('value') for ItemValue in Group}

# this definition exists because focused behavior needs one stable owner
def TestFcstdNested(TmpPath) -> None:
    Output = TmpPath / 'nested_history.FCStd'
    WriteFreecad(NestedAsmDoc(), Output)
    Component = TmpPath / 'nested_history' / 'Piston.FCStd'
    with Zipfile.ZipFile(Component) as Archive:
        ComponentRoot = XmlTree.fromstring(Archive.read('Document.xml'))
    ComponentObjects = ComponentRoot.findall('./Objects/Object')
    ComponentTypes = {ItemValue.get('name', ''): ItemValue.get('type', '') for ItemValue in ComponentObjects}
    ComponentData = {ItemValue.get('name', ''): ItemValue for ItemValue in ComponentRoot.findall('./ObjectData/Object')}
    assert sum((ItemValue.get('type') == 'Assembly::AssemblyObject' for ItemValue in ComponentObjects)) == 1
    assert any((ItemValue.get('type') == 'Part::Extrusion' for ItemValue in ComponentObjects))
    ComponentTarget = ComponentRoot.find("./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='ExternalLinkTarget']/String").get('value')
    SourceAsm = ComponentData[ComponentTarget]
    SourceChildren = [ItemValue.get('value') for ItemValue in PropAction(SourceAsm, 'Group').findall('./LinkList/Link') if ComponentData[ItemValue.get('value')].find("./Properties/Property[@name='InstanceId']") is not None]
    assert len(SourceChildren) == 1
    assert ComponentTypes[SourceChildren[0]] == 'App::Link'
    SourceSketches = PropAction(SourceAsm, 'Sketches').find('Link').get('value')
    SourceTimeline = PropAction(SourceAsm, 'FeatureTimeline').find('Link').get('value')
    SourceDependencies = next((ItemValue for ItemValue in ComponentRoot.findall('./Objects/ObjectDeps') if ItemValue.get('Name') == ComponentTarget))
    assert {SourceSketches, SourceTimeline}.issubset({ItemValue.get('Name') for ItemValue in SourceDependencies.findall('Dep')})
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
    Objects = RootValue.findall('./Objects/Object')
    Types = {ItemValue.get('name', ''): ItemValue.get('type', '') for ItemValue in Objects}
    DataValue = {ItemValue.get('name', ''): ItemValue for ItemValue in RootValue.findall('./ObjectData/Object')}
    AsmLinkName = next((NameValue for NameValue, TypeId in Types.items() if TypeId == 'Assembly::AssemblyLink'))
    AsmLink = DataValue[AsmLinkName]
    Extensions = AsmLink.find('Extensions')
    assert Extensions is not None
    assert [ItemValue.get('type') for ItemValue in Extensions.findall('Extension')] == ['App::OriginGroupExtension']
    Origin = PropAction(AsmLink, 'Origin').find('Link').get('value')
    Children = [ItemValue.get('value') for ItemValue in PropAction(AsmLink, 'Group').findall('./LinkList/Link')]
    assert Types[Origin] == 'App::Origin'
    assert len(Children) == 1
    Proxy = DataValue[Children[0]]
    assert Types[Children[0]] == ComponentTypes[SourceChildren[0]]
    ParentXlink = PropAction(AsmLink, 'LinkedObject').find('XLink')
    ProxyXlink = PropAction(Proxy, 'LinkedObject').find('XLink')
    assert ProxyXlink.get('file') == ParentXlink.get('file')
    assert ProxyXlink.get('stamp') == ParentXlink.get('stamp')
    assert ProxyXlink.get('name') == SourceChildren[0]
    assert [ItemValue.get('value') for ItemValue in PropAction(Proxy, 'InstancePath').findall('./StringList/String')] == ['instance:subassembly', 'instance:part']
    AsmLinkNode = next((ItemValue for ItemValue in Objects if ItemValue.get('name') == AsmLinkName))
    assert AsmLinkNode.get('Touched') == '1'
    Dependency = next((ItemValue for ItemValue in RootValue.findall('./Objects/ObjectDeps') if ItemValue.get('Name') == AsmLinkName))
    assert {ItemValue.get('Name') for ItemValue in Dependency.findall('Dep')} == {Origin, Children[0]}
    AsmPlacement = PropAction(AsmLink, 'Placement').find('PropertyPlacement')
    assert AsmPlacement is not None
    assert (float(AsmPlacement.get('Px', '0')), float(AsmPlacement.get('Py', '0')), float(AsmPlacement.get('Pz', '0'))) == Pytest.approx((100.0, 20.0, 30.0))
    assert PropAction(AsmLink, 'Visibility').find('Bool').get('value') == 'true'
    ProxyPlacement = PropAction(Proxy, 'Placement').find('PropertyPlacement')
    assert (float(ProxyPlacement.get('Px', '0')), float(ProxyPlacement.get('Py', '0')), float(ProxyPlacement.get('Pz', '0'))) == Pytest.approx((0.0, 0.0, 0.0))
    MateValue = next((ItemValue for ItemValue in DataValue.values() if ItemValue.find("./Properties/Property[@name='MateId']") is not None))
    RefValue = PropAction(MateValue, 'Reference2').find('XLink')
    assert RefValue.get('name') == AsmLinkName
    assert [ItemValue.get('value') for ItemValue in RefValue.findall('Sub')] == [f'{Children[0]}.', f'{Children[0]}.']
    AsmRoot = next((ItemValue for ItemValue in DataValue.values() if ItemValue.find("./Properties/Property[@name='RootDefinitionId']") is not None))
    RootChildren = {ItemValue.get('value') for ItemValue in PropAction(AsmRoot, 'Group').findall('./LinkList/Link')}
    assert AsmLinkName in RootChildren
    MetaGroups = {NameValue for NameValue in DataValue if NameValue.endswith(('_Definitions', '_Components', '_MateEntities'))}
    assert MetaGroups.isdisjoint(RootChildren)

# this definition exists because focused behavior needs one stable owner
@Pytest.mark.skipif(not KOracle.is_file(), reason='KIT_FREECAD_ORACLE is unavailable')
def TestLoadsAsm(TmpPath) -> None:
    Output = TmpPath / 'assembly.FCStd'
    WriteFreecad(MeshDoc(), Output)
    CodeValue = f"import FreeCAD as App;d=App.open(r'{Output}');d.recompute();d.recompute();links=[o for o in d.Objects if o.TypeId=='App::Link'];mates=[o for o in d.Objects if hasattr(o,'MateId')];shapelinks=[o for o in links if o.LinkedObject is not None and hasattr(o.LinkedObject,'Shape') and not o.LinkedObject.Shape.isNull()];documents=tuple(App.listDocuments().values());sources=[o for document in documents for o in document.Objects if o.TypeId=='Mesh::Feature'];target=shapelinks[0].LinkedObject;print('KIT_ASSEMBLY',len(links),len(mates),links[0].Placement.Base.x,links[0].Placement.Base.y,links[0].Placement.Base.z,links[0].LinkedObject is not None,len(shapelinks),len(target.Shape.Faces),target.Shape.BoundBox.XLength,target.TypeId,getattr(target,'Representation',''),len(sources),all(o.Visibility for o in sources),not any('Touched' in o.State for o in d.Objects))"
    Completed = Subprocess.run([str(KOracle), '-c', CodeValue], check=True, capture_output=True, text=True, timeout=120)
    OutputText = Completed.stdout + Completed.stderr
    for Message in ('The graph must be a DAG', 'links are out of scope', 'pending remove', 'Time stamp changed on link'):
        assert Message not in OutputText
    LineValue = next((Value for Value in Completed.stdout.splitlines() if Value.startswith('KIT_ASSEMBLY')))
    Values = LineValue.split()[1:]
    assert Values[:2] == ['1', '1']
    assert tuple((float(Value) for Value in Values[2:5])) == Pytest.approx((100.0, 20.0, 30.0))
    assert Values[5:8] == ['True', '1', '2']
    assert float(Values[8]) == Pytest.approx(1.0)
    assert Values[9:] == ['Part::Feature', 'faceted', '0', 'True', 'True']

# this definition exists because focused behavior needs one stable owner
@Pytest.mark.skipif(not KOracle.is_file(), reason='KIT_FREECAD_ORACLE is unavailable')
def TestLoadsNested(TmpPath) -> None:
    Output = TmpPath / 'nested.FCStd'
    WriteFreecad(NestedAsmDoc(), Output)
    CodeValue = f"import FreeCAD as App;d=App.open(r'{Output}');links=[o for o in d.Objects if o.TypeId=='Assembly::AssemblyLink'];a=links[0];before=tuple(o.Name for o in a.Group);d.recompute();first=tuple(o.Name for o in a.Group);d.recompute();second=tuple(o.Name for o in a.Group);children=[o for o in a.Group if o.TypeId=='App::Link'];c=children[0];print('KIT_NESTED',len(links),a.Origin is not None,len(children),before==first==second,c.getParentGeoFeatureGroup()==a,c.LinkedObject in a.LinkedObject.Group,c.LinkedObject.Document==a.LinkedObject.Document,a.Placement.Base.x,a.Placement.Base.y,a.Placement.Base.z,c.Placement.Base.x,c.Placement.Base.y,c.Placement.Base.z,c.LinkedObject is not None,a.LinkedObject is not None,a.Visibility,c.Visibility)"
    Completed = Subprocess.run([str(KOracle), '-c', CodeValue], check=True, capture_output=True, text=True, timeout=120)
    OutputText = Completed.stdout + Completed.stderr
    for Message in ('The graph must be a DAG', 'links are out of scope', 'pending remove', 'Time stamp changed on link'):
        assert Message not in OutputText
    LineValue = next((Value for Value in Completed.stdout.splitlines() if Value.startswith('KIT_NESTED')))
    assert LineValue.split()[1:] == ['1', 'True', '1', 'True', 'True', 'True', 'True', '100.0', '20.0', '30.0', '0.0', '0.0', '0.0', 'True', 'True', 'True', 'True']

# this binding exists because shared behavior needs one stable value
globals()['ComponentDocument'] = ComponentDoc

# this binding exists because shared behavior needs one stable value
globals()['ET'] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()['Matrix4'] = MatrixFour

# this binding exists because shared behavior needs one stable value
globals()['Mesh'] = MeshRecord

# this binding exists because shared behavior needs one stable value
globals()['ORACLE'] = KOracle

# this binding exists because shared behavior needs one stable value
globals()['Path'] = FilePath

# this binding exists because shared behavior needs one stable value
globals()['Vector3'] = VectorThree

# this binding exists because shared behavior needs one stable value
globals()['_geometry_free'] = GeomFree

# this binding exists because shared behavior needs one stable value
globals()['_mesh_document'] = MeshDoc

# this binding exists because shared behavior needs one stable value
globals()['_nested_assembly_document'] = NestedAsmDoc

# this binding exists because shared behavior needs one stable value
globals()['_property'] = PropAction

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['assembly_document'] = AsmDoc

# this binding exists because shared behavior needs one stable value
globals()['document'] = DocValue

# this binding exists because shared behavior needs one stable value
globals()['interchange_assembly_document'] = InterchangeAsmDoc

# this binding exists because shared behavior needs one stable value
globals()['json'] = JsonValue

# this binding exists because shared behavior needs one stable value
globals()['os'] = OsModule

# this binding exists because shared behavior needs one stable value
globals()['pytest'] = Pytest

# this binding exists because shared behavior needs one stable value
globals()['read_freecad'] = ReadFreecad

# this binding exists because shared behavior needs one stable value
globals()['replace'] = Replace

# this binding exists because shared behavior needs one stable value
globals()['struct'] = Struct

# this binding exists because shared behavior needs one stable value
globals()['subprocess'] = Subprocess

# this binding exists because shared behavior needs one stable value
globals()['write_freecad'] = WriteFreecad

# this binding exists because shared behavior needs one stable value
globals()['zipfile'] = Zipfile
