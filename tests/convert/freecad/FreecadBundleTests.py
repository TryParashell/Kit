# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import replace as Replace
from datetime import datetime as Datetime, timezone as Timezone
import io as IoStream
from pathlib import Path as PathValue
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile
import convert.adapters.freecad.Adapter as FreecadAdapter
from convert.adapters.freecad import read_freecad as ReadFreecad, write_freecad as WriteFreecad
from interchange import Capability, ComponentDocument as ComponentDoc, Mesh as MeshValue, Vector3 as VectorThree
from tests.interchange.assembly.AssemblyTests import assembly_document as AsmDoc

# this definition exists because focused behavior needs one stable owner
def XmlAction(PathValue: Path) -> XmlTree.Element:
    with Zipfile.ZipFile(PathValue) as Archive:
        return XmlTree.fromstring(Archive.read('Document.xml'))

# this definition exists because focused behavior needs one stable owner
def LinkedObject(RootValue: ET.Element) -> XmlTree.Element:
    Result = next((Value for Value in RootValue.findall("./ObjectData/Object/Properties/Property[@name='LinkedObject']/XLink") if Value.get('file')))
    return Result

# this definition exists because focused behavior needs one stable owner
def DocTimestamp(RootValue: ET.Element, PropName: str) -> str:
    Result = RootValue.find(f"./Properties/Property[@name='{PropName}']/String")
    assert Result is not None
    return Result.get('value', '')

# this definition exists because focused behavior needs one stable owner
def Representation(RootValue: ET.Element, Target: str) -> str:
    Result = RootValue.find(f"./ObjectData/Object[@name='{Target}']/Properties/Property[@name='Representation']/String")
    assert Result is not None
    return Result.get('value', '')

# this definition exists because focused behavior needs one stable owner
def MeshSource(Linked: bool):
    Source = AsmDoc()
    AsmValue = Source.assembly
    assert AsmValue is not None
    MeshValue = MeshValue('mesh:part', 'Part geometry', (VectorThree(0.0, 0.0, 0.0), VectorThree(1.0, 0.0, 0.0), VectorThree(0.0, 1.0, 0.0)), ((0, 1, 2),))
    Definitions = tuple((Replace(Definition, document_id=Definition.document_id if Linked else '', body_ids=Definition.body_ids if Linked else (), mesh_ids=(MeshValue.id,), source_path='C:\\Toolbox\\Piston.SLDPRT', source_format_id='solidworks.sldprt') if Definition.id == 'definition:part' else Definition for Definition in AsmValue.definitions))
    Instances = (AsmValue.instances[0], Replace(AsmValue.instances[1], owner_definition_id=AsmValue.root_definition_id))
    MateEntities = (AsmValue.mate_entities[0], Replace(AsmValue.mate_entities[1], instance_path=(AsmValue.instances[1].id,)))
    return (Replace(Source, meshes=(MeshValue,), assembly=Replace(AsmValue, definitions=Definitions, instances=Instances, documents=AsmValue.documents if Linked else (), mate_entities=MateEntities)), MeshValue)

# this definition exists because focused behavior needs one stable owner
def TestPathAsmWith(TempPath: Path) -> None:
    Source, MeshValue = MeshSource(Linked=True)
    Output = TempPath / 'assembly.FCStd'
    Result = WriteFreecad(Source, Output)
    Component = TempPath / 'assembly' / 'Piston.FCStd'
    assert Component.is_file()
    RootValue = XmlAction(Output)
    LinkValue = LinkedObject(RootValue)
    assert LinkValue.get('file') == 'assembly/Piston.FCStd'
    Stamp = Datetime.fromtimestamp(Component.stat().st_mtime, Timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    assert LinkValue.get('stamp') == Stamp
    ComponentRoot = XmlAction(Component)
    for PropName in ('CreationDate', 'LastModifiedDate'):
        assert DocTimestamp(ComponentRoot, PropName) == Stamp
    assert DocTimestamp(RootValue, 'LastModifiedDate') == Stamp
    Target = ComponentRoot.find("./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='ExternalLinkTarget']/String")
    assert Target is not None
    assert LinkValue.get('name') == Target.get('value')
    TargetObject = ComponentRoot.find(f"./Objects/Object[@name='{Target.get('value')}']")
    assert TargetObject is not None
    assert TargetObject.get('type') == 'Part::Feature'
    assert Representation(ComponentRoot, Target.get('value', '')) == 'faceted'
    AsmValue = Source.assembly
    assert AsmValue is not None
    Linked = AsmValue.documents[0].document
    Restored = ReadFreecad(Component)
    assert Restored == Replace(Linked, meshes=(MeshValue,), capabilities=Linked.capabilities | {Capability.TESSELLATION})
    assert Result.metadata['component_file_count'] == 1
    assert Result.metadata['component_bytes_written'] == Component.stat().st_size

# this definition exists because focused behavior needs one stable owner
def TestPathAsmOne(TempPath: Path, MonkeyPatch) -> None:
    Fixed = Datetime(2026, 8, 1, 18, 0, 0, tzinfo=Timezone.utc)

    # this definition exists because focused behavior needs one stable owner
    class FixedDateTime(Datetime):

        # this definition exists because focused behavior needs one stable owner
        @classmethod
        def NowAction(ClassType, TzValue=None):
            return Fixed if TzValue is not None else Fixed.replace(tzinfo=None)
        locals()['now'] = NowAction
    MonkeyPatch.setattr(FreecadAdapter, 'datetime', FixedDateTime)
    Source, Ignored = MeshSource(Linked=True)
    Output = TempPath / 'assembly.FCStd'
    Component = TempPath / 'assembly' / 'Piston.FCStd'
    WriteFreecad(Source, Output)
    FirstRoot = XmlAction(Output)
    FirstComponent = XmlAction(Component)
    FirstStamp = '2026-08-01T18:00:00Z'
    assert LinkedObject(FirstRoot).get('stamp') == FirstStamp
    for RootValue in (FirstRoot, FirstComponent):
        assert DocTimestamp(RootValue, 'CreationDate') == FirstStamp
        assert DocTimestamp(RootValue, 'LastModifiedDate') == FirstStamp
    WriteFreecad(Source, Output, overwrite=True)
    SecondRoot = XmlAction(Output)
    SecondComponent = XmlAction(Component)
    SecondStamp = '2026-08-01T18:00:01Z'
    assert LinkedObject(SecondRoot).get('stamp') == SecondStamp
    for RootValue in (SecondRoot, SecondComponent):
        assert DocTimestamp(RootValue, 'CreationDate') == SecondStamp
        assert DocTimestamp(RootValue, 'LastModifiedDate') == SecondStamp
    SecondEpoch = Fixed.timestamp() + 1.0
    assert Output.stat().st_mtime == SecondEpoch
    assert Component.stat().st_mtime == SecondEpoch

# this definition exists because focused behavior needs one stable owner
def TestNestedAsmTo(TempPath: Path) -> None:
    Source, Ignored = MeshSource(Linked=True)
    AsmValue = Source.assembly
    assert AsmValue is not None
    Nested, Ignored = MeshSource(Linked=True)
    NestedAsm = Nested.assembly
    assert NestedAsm is not None
    Nested = Replace(Nested, meshes=(), assembly=Replace(NestedAsm, definitions=tuple((Replace(Definition, mesh_ids=()) if Definition.id == 'definition:part' else Definition for Definition in NestedAsm.definitions))))
    Definitions = tuple((Replace(Definition, document_id='document:subassembly') if Definition.id == 'definition:subassembly' else Definition for Definition in AsmValue.definitions))
    Source = Replace(Source, assembly=Replace(AsmValue, definitions=Definitions, documents=(*AsmValue.documents, ComponentDoc('document:subassembly', Nested))))
    Output = TempPath / 'nested.FCStd'
    WriteFreecad(Source, Output)
    AsmComponent = TempPath / 'nested' / 'Piston.FCStd'
    PartComponent = TempPath / 'nested' / 'Piston_2.FCStd'
    AsmRoot = XmlAction(AsmComponent)
    PartRoot = XmlAction(PartComponent)
    LinkValue = LinkedObject(AsmRoot)
    assert LinkValue.get('file') == 'Piston_2.FCStd'
    Target = LinkValue.get('name', '')
    TargetObject = PartRoot.find(f"./Objects/Object[@name='{Target}']")
    assert TargetObject is not None
    assert TargetObject.get('type') == 'Part::Feature'
    assert Representation(PartRoot, Target) == 'faceted'
    AsmTarget = AsmRoot.find("./ObjectData/Object[@name='KitMetadata']/Properties/Property[@name='ExternalLinkTarget']/String")
    assert AsmTarget is not None
    AsmObject = AsmRoot.find(f"./Objects/Object[@name='{AsmTarget.get('value')}']")
    assert AsmObject is not None
    assert AsmObject.get('type') == 'Assembly::AssemblyObject'

# this definition exists because focused behavior needs one stable owner
def TestPathAsmMesh(TempPath: Path) -> None:
    Source, MeshValue = MeshSource(Linked=False)
    Output = TempPath / 'toolbox.FCStd'
    WriteFreecad(Source, Output)
    Component = TempPath / 'toolbox' / 'Piston.FCStd'
    RootValue = XmlAction(Output)
    LinkValue = LinkedObject(RootValue)
    assert LinkValue.get('file') == 'toolbox/Piston.FCStd'
    Restored = ReadFreecad(Component)
    assert Restored.meshes == (MeshValue,)
    assert Restored.feature_timeline == ()
    assert Restored.assembly is None
    assert Restored.source.path == 'C:\\Toolbox\\Piston.SLDPRT'

# this definition exists because focused behavior needs one stable owner
def TestBinaryAsm() -> None:
    Stream = IoStream.BytesIO()
    Result = WriteFreecad(AsmDoc(), Stream)
    Stream.seek(0)
    with Zipfile.ZipFile(Stream) as Archive:
        RootValue = XmlTree.fromstring(Archive.read('Document.xml'))
    Links = RootValue.findall("./ObjectData/Object/Properties/Property[@name='LinkedObject']/XLink")
    assert Links
    assert all((not LinkValue.get('file') for LinkValue in Links))
    assert Result.path is None
    assert Result.metadata['component_file_count'] == 0
    assert Result.metadata['component_bytes_written'] == 0

# this binding exists because shared behavior needs one stable value
globals()['ComponentDocument'] = ComponentDoc

# this binding exists because shared behavior needs one stable value
globals()['ET'] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()['Mesh'] = MeshValue

# this binding exists because shared behavior needs one stable value
globals()['Path'] = PathValue

# this binding exists because shared behavior needs one stable value
globals()['Vector3'] = VectorThree

# this binding exists because shared behavior needs one stable value
globals()['_document_timestamp'] = DocTimestamp

# this binding exists because shared behavior needs one stable value
globals()['_linked_object'] = LinkedObject

# this binding exists because shared behavior needs one stable value
globals()['_mesh_source'] = MeshSource

# this binding exists because shared behavior needs one stable value
globals()['_representation'] = Representation

# this binding exists because shared behavior needs one stable value
globals()['_xml'] = XmlAction

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['assembly_document'] = AsmDoc

# this binding exists because shared behavior needs one stable value
globals()['datetime'] = Datetime

# this binding exists because shared behavior needs one stable value
globals()['freecad_adapter'] = FreecadAdapter

# this binding exists because shared behavior needs one stable value
globals()['io'] = IoStream

# this binding exists because shared behavior needs one stable value
globals()['read_freecad'] = ReadFreecad

# this binding exists because shared behavior needs one stable value
globals()['replace'] = Replace

# this binding exists because shared behavior needs one stable value
globals()['timezone'] = Timezone

# this binding exists because shared behavior needs one stable value
globals()['write_freecad'] = WriteFreecad

# this binding exists because shared behavior needs one stable value
globals()['zipfile'] = Zipfile
