# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass
import struct as Struct
from convert.adapters.solidworks.container.Archive import CLASS_REFERENCE_KIND as ClassRefKind, DEFINITION_KIND as DefinitionKind, NULL_KIND as NullKind, OBJECT_REFERENCE_KIND as ObjectRefKind, Model, Node as NodeValue, encode_class_definition as EncodeClassDefinition, encode_string as EncodeString
from convert.adapters.solidworks.container.Container import SldprtFormatError

# this binding exists because shared behavior needs one stable value
KConfigManagerStream = 'Contents/CMgr'

# this binding exists because shared behavior needs one stable value
KRootClass = 'moConfigurationMgr_c'

# this binding exists because shared behavior needs one stable value
KConfigClass = 'moPartConfiguration_c'

# this binding exists because shared behavior needs one stable value
KNodeNameClass = 'moNodeName_c'

# this binding exists because shared behavior needs one stable value
KVisualClass = 'moVisualProperties_c'

# this binding exists because shared behavior needs one stable value
KLinkClass = 'moLinkedAtomIdNode_c'

# this binding exists because shared behavior needs one stable value
KExtObjectClass = 'moExtObject_c'

# this binding exists because shared behavior needs one stable value
KStringHandleClass = 'moCStringHandle_c'

# this binding exists because shared behavior needs one stable value
KObjectListClass = 'suObList'

# this binding exists because shared behavior needs one stable value
KClassSchema = 1

# this binding exists because shared behavior needs one stable value
KMapBase = 3

# this binding exists because shared behavior needs one stable value
KDocGeneration = 18000

# this binding exists because shared behavior needs one stable value
KDocBuild = 2025268

# this binding exists because shared behavior needs one stable value
KSessionCounter = 360108

# this binding exists because shared behavior needs one stable value
KFirstAtomId = 101

# this binding exists because shared behavior needs one stable value
KDisplayStateKind = 5

# this binding exists because shared behavior needs one stable value
KDisplayStateRevision = 2

# this binding exists because shared behavior needs one stable value
KDisplayStateMask = 2151678336

# this binding exists because shared behavior needs one stable value
KDisplayTail = (0, 0, 128, 157, 158, 37)

# this binding exists because shared behavior needs one stable value
KDisplayChordRatio = 0.99

# this binding exists because shared behavior needs one stable value
KViewStyleMode = 3

# this binding exists because shared behavior needs one stable value
KLinkTerminator = 2

# this binding exists because shared behavior needs one stable value
KLinkFlag = 1

# this binding exists because shared behavior needs one stable value
KObjectListKind = 2

# this binding exists because shared behavior needs one stable value
KNodeNameScale = 2.0

# this binding exists because shared behavior needs one stable value
KNodeNameFlags = 512

# this binding exists because shared behavior needs one stable value
KManagerScale = 2.0

# this binding exists because shared behavior needs one stable value
KStringHandleKind = 2

# this binding exists because shared behavior needs one stable value
KDefaultConfigName = 'Default'

# this binding exists because shared behavior needs one stable value
KDefaultPartName = 'Part1'

# this binding exists because shared behavior needs one stable value
KDefaultRenderStyle = 5

# this binding exists because shared behavior needs one stable value
KFirstTreeId = 32

# this binding exists because shared behavior needs one stable value
KTreeIdStep = 8

# this binding exists because shared behavior needs one stable value
KDocStampHigh = 31269785

# this binding exists because shared behavior needs one stable value
KDocStampLow = 268435456

# this binding exists because shared behavior needs one stable value
KDisplayGeomCacheBytes = 96

# this binding exists because shared behavior needs one stable value
KDisplayGeomCacheDefault = bytes(KDisplayGeomCacheBytes)

# this binding exists because shared behavior needs one stable value
KResidualSpans: tuple[tuple[str, str, int], ...] = ()

# this binding exists because shared behavior needs one stable value
KVisualProperties = (('appearance_id', 'u32', 15651274), ('reserved_4', 'zeros', 8), ('appearance_library', 'str', ''), ('material_name', 'str', 'Steel'), ('diffuse', 'f64', 1.0), ('specular', 'f64', 1.0), ('ambient', 'f64', 0.5), ('emission', 'f64', 0.3125), ('reserved_64', 'zeros', 20), ('use_material', 'u32', 1), ('reserved_86', 'u32', 0), ('use_appearance', 'u32', 1), ('use_texture', 'u32', 1), ('use_display', 'u32', 1), ('display_name', 'str', ''), ('visible', 'u32', 1), ('selectable', 'u32', 1), ('render_style', 'u32', KDefaultRenderStyle), ('reserved_118', 'u32', 0), ('appearance_name', 'str', 'defaultplastic'), ('optics_kind_and_id', 'u32', 4006726147), ('optics_head', 'u32', 2147483648), ('optics_scale', 'u32', 63), ('optics_zero_166', 'zeros', 11), ('optics_one_177', 'u32', 16256), ('optics_zero_181', 'zeros', 16), ('optics_one_197', 'u32', 81792), ('optics_highlight_201', 'u32', 2577006592), ('optics_highlight_205', 'u32', 15897), ('optics_zero_209', 'u32', 0), ('optics_minus_213', 'u32', 49024), ('optics_minus_217', 'u32', 49024), ('optics_minus_221', 'u32', 49024), ('optics_zero_225', 'zeros', 10), ('texture_path', 'str', 'C:\\PROGRA~1\\SOLIDW~1\\SOLIDW~1\\data\\graphics\\materials\\color.p2m'), ('texture_head', 'f64', 9.765627351043803e-05), ('texture_weight', 'f32', 1.0), ('texture_name', 'str', ''), ('texture_scale_u', 'f32', 0.0010000000474974513), ('texture_scale_v', 'f32', 0.0010000000474974513), ('texture_zero', 'u32', 0), ('texture_rows', 'u32', 320), ('matrix_zero_a', 'zeros', 10), ('matrix_one_a', 'u32', 16256), ('matrix_zero_b', 'zeros', 12), ('matrix_one_b', 'u32', 16256), ('matrix_zero_c', 'zeros', 12), ('matrix_one_c', 'u32', 16256), ('matrix_scale', 'u32', 17076), ('edge_one', 'u32', 16256), ('edge_minus_a', 'u32', 49024), ('edge_minus_b', 'u8', 128), ('edge_minus_c', 'u16', 65471), ('edge_pad_a', 'u32', 65534), ('edge_pad_b', 'u16', 0), ('edge_pad_c', 'u16', 65280), ('edge_pad_d', 'u16', 65534), ('edge_pad_e', 'u16', 65280), ('edge_pad_f', 'u16', 65534), ('edge_pad_g', 'u16', 65280), ('edge_pad_h', 'u32', 65534), ('reserved_478', 'zeros', 91), ('decal_name', 'str', ''), ('reserved_573', 'zeros', 8), ('scene_name', 'str', ''), ('scene_zero', 'u32', 0), ('scene_flag', 'u32', 1), ('light_name', 'str', ''), ('light_zero', 'u32', 0), ('light_flag', 'u32', 1), ('owner_handle', 'u32', 4294967295), ('identity_zero_a', 'zeros', 20), ('identity_atom', 'u32', KFirstAtomId), ('identity_zero_b', 'zeros', 13), ('identity_generation', 'u32', KDocGeneration), ('identity_zero_c', 'zeros', 8), ('identity_build', 'u32', KDocBuild))

# this binding exists because shared behavior needs one stable value
KAtomTableHead = (('table_flags', 'u32', 0), ('table_kind', 'u32', 65536), ('table_zero_a', 'zeros', 10), ('table_chord', 'f64', -0.007812500000000002), ('table_minus_one', 'f32', -1.0), ('table_zero_b', 'zeros', 8), ('table_flag_a', 'u32', 1), ('table_zero_c', 'zeros', 28), ('table_flag_b', 'u32', 1), ('table_zero_d', 'u32', 0), ('table_owner', 'u32', 4294967295), ('table_flag_c', 'u32', 1), ('table_zero_e', 'zeros', 12))

# this binding exists because shared behavior needs one stable value
KViewStyle = (('style_name', 'str', ''), ('style_zero', 'u8', 0), ('style_mask', 'u16', 65535), ('style_pad', 'u16', 0), ('style_mode', 'u8', KViewStyleMode), ('style_owner_a', 'u32', 4294967295), ('style_owner_b', 'u32', 4294967295), ('style_scale', 'f32', -1.0), ('style_offset', 'f64', 0.0))

# this binding exists because shared behavior needs one stable value
KObjectListTail = (('list_zero_a', 'zeros', 28), ('list_kind', 'u32', KObjectListKind), ('list_zero_b', 'zeros', 4), ('list_name', 'str', ''), ('list_zero_c', 'zeros', 12), ('list_owner', 'u32', 4294967295), ('list_zero_d', 'zeros', 8))

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class Stamp:
    locals().setdefault('__annotations__', {})
    __annotations__['high'] = 'int'
    __annotations__['low'] = 'int'

    # this definition exists because focused behavior needs one stable owner
    def PackAction(Instance) -> bytes:
        return Struct.pack('<II', Instance.high, Instance.low)
    locals()['pack'] = PackAction

# this binding exists because shared behavior needs one stable value
KZeroStamp = Stamp(0, 0)

# this binding exists because shared behavior needs one stable value
KDocStamp = Stamp(KDocStampHigh, KDocStampLow)

# this binding exists because shared behavior needs one stable value
KDefaultFeatureTreeIds = (KFirstTreeId,)

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class FeatureStamp:
    locals().setdefault('__annotations__', {})
    __annotations__['tree_id'] = 'int'
    __annotations__['stamp'] = 'Stamp'
    locals()['stamp'] = KZeroStamp

# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class CMgrParameters:
    locals().setdefault('__annotations__', {})
    __annotations__['configuration_name'] = 'str'
    __annotations__['part_name'] = 'str'
    __annotations__['name_stamp'] = 'int'
    __annotations__['atom_ids'] = 'tuple[int, ...]'
    __annotations__['link_atom_ids'] = 'tuple[int, ...]'
    __annotations__['link_tree_ids'] = 'tuple[int, ...]'
    __annotations__['reverse_atom_ids'] = 'tuple[int, ...]'
    __annotations__['feature_stamps'] = 'tuple[FeatureStamp, ...]'
    __annotations__['display_stamp'] = 'Stamp'
    __annotations__['view_stamp'] = 'Stamp'
    __annotations__['max_tree_id'] = 'int'
    __annotations__['next_id_a'] = 'int'
    __annotations__['next_id_b'] = 'int'
    __annotations__['render_style'] = 'int'
    __annotations__['atom_head_count'] = 'int'
    __annotations__['chord_ratio'] = 'float'
    __annotations__['generation'] = 'int'
    __annotations__['build'] = 'int'
    __annotations__['session_counter'] = 'int'
    __annotations__['display_geometry_cache'] = 'bytes'
    __annotations__['connected_history'] = 'bool'
    __annotations__['terminal_parent_tree_id'] = 'int | None'

    # this definition exists because focused behavior needs one stable owner
    def Validate(Instance) -> None:
        ValidateCmgr(Instance)
    locals()['validate'] = Validate

# this definition exists because configuration validation is independent from parameter storage
def ValidateCmgr(Params: CMgrParameters) -> None:
    if not Params.atom_ids:
        raise SldprtFormatError('a SOLIDWORKS configuration manager needs at least one atom id')
    if len(Params.link_tree_ids) != len(Params.link_atom_ids):
        raise SldprtFormatError(f'{len(Params.link_atom_ids)} linked atoms need {len(Params.link_atom_ids)} tree ids, got {len(Params.link_tree_ids)}')
    if Params.display_geometry_cache != KDisplayGeomCacheDefault:
        raise SldprtFormatError(f'display_geometry_cache must be the recovered {KDisplayGeomCacheBytes}-byte reserved-zero field')
    if Params.generation != KDocGeneration:
        raise SldprtFormatError(f'the recovered Contents/CMgr tables describe generation {KDocGeneration}, not {Params.generation}')
    if Params.connected_history and len(Params.link_atom_ids) not in {2, 3, 4}:
        raise SldprtFormatError('the recovered connected-history CMgr shape requires two to four atoms')
    if Params.terminal_parent_tree_id is not None and (Params.connected_history or len(Params.atom_ids) != 1 or len(Params.link_atom_ids) != 1 or (len(Params.link_tree_ids) != 1) or (Params.terminal_parent_tree_id <= 0) or (Params.terminal_parent_tree_id == Params.link_tree_ids[0])):
        raise SldprtFormatError('the recovered terminal-history CMgr shape requires one child atom and one distinct parent tree')

# this definition exists because focused behavior needs one stable owner
def PackAction(KindValue: str, Value: object) -> bytes:
    if KindValue == 'u8':
        return Struct.pack('<B', int(Value))
    if KindValue == 'u16':
        return Struct.pack('<H', int(Value))
    if KindValue == 'u32':
        return Struct.pack('<I', int(Value))
    if KindValue == 'f32':
        return Struct.pack('<f', float(Value))
    if KindValue == 'f64':
        return Struct.pack('<d', float(Value))
    if KindValue == 'str':
        return EncodeString(str(Value))
    if KindValue == 'zeros':
        return bytes(int(Value))
    raise SldprtFormatError(f'unsupported Contents/CMgr field kind {KindValue!r}')

# this definition exists because focused behavior needs one stable owner
def Table(Fields: tuple[tuple[str, str, object], ...], Overrides: dict[str, object] | None=None) -> bytes:
    OutValue = bytearray()
    for NameValue, KindValue, Value in Fields:
        if Overrides is not None and NameValue in Overrides:
            Value = Overrides[NameValue]
        OutValue += PackAction(KindValue, Value)
    return bytes(OutValue)

# this definition exists because focused behavior needs one stable owner
def ManagerHead() -> bytes:
    return PackAction('f64', KManagerScale) + PackAction('u32', 4294967295) + PackAction('u32', 0) + EncodeString('') + PackAction('u32', 0)

# this definition exists because focused behavior needs one stable owner
def IdentityBlock(AtomId: int, Generation: int, Build: int) -> bytes:
    return PackAction('u32', 0) + PackAction('u32', 0) + PackAction('u32', AtomId) + PackAction('u32', 0) + PackAction('u32', 0) + PackAction('u32', 0) + PackAction('u8', 0) + PackAction('u32', Generation) + PackAction('u32', 0) + PackAction('u32', 0) + PackAction('u32', Build)

# this definition exists because focused behavior needs one stable owner
def DisplayState(Stamp: Stamp, Session: int) -> bytes:
    return PackAction('u32', 0) + PackAction('u32', KDisplayStateKind) + PackAction('u32', 0) + PackAction('u16', 0) + PackAction('u32', 4294967295) + Stamp.pack() + PackAction('u16', KDisplayStateRevision) + PackAction('u32', Session) + PackAction('u32', 1)

# this definition exists because focused behavior needs one stable owner
def DisplayStateA(Params: CMgrParameters) -> bytes:
    return DisplayState(Params.view_stamp, Params.session_counter) + EncodeString('') + PackAction('u32', 4294967295) + PackAction('u32', KDisplayStateMask) + EncodeString('') + PackAction('u32', Params.max_tree_id) + PackAction('u32', Params.next_id_a) + PackAction('u32', Params.next_id_b) + bytes(Params.display_geometry_cache) + PackAction('u32', 1) + bytes(16) + PackAction('f64', Params.chord_ratio) + bytes(16) + EncodeString('') + EncodeString('') + bytes(28) + PackAction('f64', 1.0) + bytes(24) + PackAction('f64', 1.0) + bytes(24) + PackAction('f64', 1.0) + PackAction('u32', 1) + bytes(KDisplayTail)

# this definition exists because focused behavior needs one stable owner
def NodeName(NameValue: str) -> bytes:
    return EncodeString(NameValue) + PackAction('f64', KNodeNameScale) + PackAction('u32', 0) + PackAction('u32', KNodeNameFlags) + EncodeString('') + PackAction('u32', 0)

# this definition exists because focused behavior needs one stable owner
def Visual(Params: CMgrParameters) -> bytes:
    return Table(KVisualProperties, {'render_style': Params.render_style, 'identity_atom': Params.atom_ids[0], 'identity_generation': Params.generation, 'identity_build': Params.build})

# this definition exists because focused behavior needs one stable owner
def AtomHead(Count: int, Generation: int) -> bytes:
    return PackAction('u16', 0) + PackAction('u16', Count) + PackAction('u32', 0) + PackAction('u16', 0) + PackAction('u16', Generation) + PackAction('u16', 0) + PackAction('u16', 1)

# this definition exists because focused behavior needs one stable owner
def AtomTable(AtomIds: tuple[int, ...]) -> bytes:
    OutValue = bytearray(Table(KAtomTableHead))
    OutValue += PackAction('u32', len(AtomIds))
    for AtomValue in AtomIds:
        OutValue += PackAction('u32', AtomValue) + PackAction('u32', 0)
    OutValue += bytes(30)
    return bytes(OutValue)

# this definition exists because focused behavior needs one stable owner
def ConnectedAtom(AtomIds: tuple[int, ...]) -> bytes:
    if len(AtomIds) not in {2, 3, 4}:
        raise SldprtFormatError('the recovered connected-history atom table requires two to four atoms')
    OutputData = bytearray(Table(KAtomTableHead))
    OutputData += PackAction('u32', len(AtomIds))
    for AtomId in AtomIds:
        OutputData += PackAction('u32', AtomId) + PackAction('u32', 0)
    OutputData += bytes(4)
    OutputData += PackAction('u32', len(AtomIds) - 1)
    for AtomIndex in range(len(AtomIds) - 1, 0, -1):
        OutputData += PackAction('u32', AtomIds[AtomIndex])
        OutputData += PackAction('u32', AtomIds[AtomIndex - 1])
    OutputData += bytes(22)
    return bytes(OutputData)

# this definition exists because focused behavior needs one stable owner
def LinkHead(AtomIds: tuple[int, ...]) -> bytes:
    return PackAction('u32', 0) + PackAction('u32', 0) + PackAction('u32', len(AtomIds)) + PackAction('u32', AtomIds[0] if AtomIds else 0)

# this definition exists because focused behavior needs one stable owner
def LinkBody(AtomId: int, TreeId: int, NextId: int | None) -> bytes:
    HeadValue = PackAction('u32', AtomId) + PackAction('u16', KLinkFlag) + PackAction('u32', TreeId)
    if NextId is None:
        return HeadValue + bytes(34) + PackAction('u32', KLinkTerminator) + bytes(8)
    return HeadValue + bytes(18) + PackAction('u32', NextId)

# this definition exists because focused behavior needs one stable owner
def TerminalLink(AtomId: int, ParentTreeId: int, ChildTreeId: int) -> bytes:
    return b''.join((PackAction('u32', AtomId), PackAction('u16', KLinkFlag), PackAction('u32', ParentTreeId), PackAction('u32', 1), PackAction('u32', ChildTreeId), bytes(30), PackAction('u32', KLinkTerminator), bytes(8)))

# this definition exists because focused behavior needs one stable owner
def ConnectedLink(AtomIds: tuple[int, ...], TreeIds: tuple[int, ...]) -> tuple[tuple[bytes, tuple[bytes, ...]], ...]:
    if len(AtomIds) == 3 and len(TreeIds) == 3:
        FirstAtom, SecondAtom, ThirdAtom = AtomIds
        FirstTree, SecondTree, ThirdTree = TreeIds
        FirstHead = PackAction('u32', FirstAtom) + PackAction('u16', KLinkFlag) + PackAction('u32', FirstTree)
        SecondHead = PackAction('u32', SecondAtom) + PackAction('u16', KLinkFlag) + PackAction('u32', SecondTree)
        ThirdHead = PackAction('u32', ThirdAtom) + PackAction('u16', KLinkFlag) + PackAction('u32', ThirdTree)
        return ((FirstHead + bytes(6) + PackAction('u32', 1) + PackAction('u32', SecondAtom), (PackAction('u32', 0) + PackAction('u32', 2) + PackAction('u32', SecondAtom), PackAction('u32', ThirdAtom), PackAction('u32', SecondAtom))), (SecondHead + bytes(2) + PackAction('u32', 1) + PackAction('u32', FirstAtom), (PackAction('u32', 1) + PackAction('u32', ThirdAtom), PackAction('u32', 1) + PackAction('u32', FirstAtom), PackAction('u32', 1) + PackAction('u32', ThirdAtom), PackAction('u32', ThirdAtom))), (ThirdHead + bytes(2) + PackAction('u32', 1) + PackAction('u32', SecondAtom), (PackAction('u32', 0) + PackAction('u32', 2) + PackAction('u32', FirstAtom), PackAction('u32', SecondAtom), bytes(16) + PackAction('u32', 2) + PackAction('u32', SecondAtom) + PackAction('u32', FirstAtom) + PackAction('u32', ThirdAtom) + PackAction('u32', SecondAtom) + PackAction('u32', KLinkTerminator) + bytes(8))))
    if len(AtomIds) != 2 or len(TreeIds) != 2:
        raise SldprtFormatError('the recovered connected-history link graph requires two or three atoms')
    FirstAtom, SecondAtom = AtomIds
    FirstTree, SecondTree = TreeIds
    FirstHead = PackAction('u32', FirstAtom) + PackAction('u16', KLinkFlag) + PackAction('u32', FirstTree)
    SecondHead = PackAction('u32', SecondAtom) + PackAction('u16', KLinkFlag) + PackAction('u32', SecondTree)
    return ((FirstHead + bytes(6) + PackAction('u32', 1) + PackAction('u32', SecondAtom), (PackAction('u32', 0) + PackAction('u32', 1) + PackAction('u32', SecondAtom), PackAction('u32', SecondAtom))), (SecondHead + bytes(2) + PackAction('u32', 1) + PackAction('u32', FirstAtom), (PackAction('u32', 0) + PackAction('u32', 1) + PackAction('u32', FirstAtom), bytes(16) + PackAction('u32', 1) + PackAction('u32', SecondAtom) + PackAction('u32', FirstAtom) + PackAction('u32', KLinkTerminator) + bytes(8))))

# this definition exists because focused behavior needs one stable owner
def ConnectedFour(AtomIds: tuple[int, ...], TreeIds: tuple[int, ...]) -> tuple[tuple[bytes, tuple[bytes, ...]], ...]:
    if len(AtomIds) != 4 or len(TreeIds) != 4:
        raise SldprtFormatError('the recovered four-operation link graph requires four atoms')
    FirstAtom, SecondAtom, ThirdAtom, FourthAtom = AtomIds
    HeadsData = tuple((PackAction('u32', AtomId) + PackAction('u16', KLinkFlag) + PackAction('u32', TreeId) for AtomId, TreeId in zip(AtomIds, TreeIds, strict=True)))
    EdgeData = bytes(16) + PackAction('u32', 3) + PackAction('u32', SecondAtom) + PackAction('u32', FirstAtom) + PackAction('u32', ThirdAtom) + PackAction('u32', SecondAtom) + PackAction('u32', FourthAtom) + PackAction('u32', ThirdAtom) + PackAction('u32', KLinkTerminator) + bytes(8)
    return ((HeadsData[0] + bytes(6) + PackAction('u32', 1) + PackAction('u32', SecondAtom), (PackAction('u32', 0) + PackAction('u32', 3) + PackAction('u32', SecondAtom), PackAction('u32', ThirdAtom), PackAction('u32', FourthAtom), PackAction('u32', SecondAtom))), (HeadsData[1] + bytes(2) + PackAction('u32', 1) + PackAction('u32', FirstAtom), (PackAction('u32', 1) + PackAction('u32', ThirdAtom), PackAction('u32', 1) + PackAction('u32', FirstAtom), PackAction('u32', 2) + PackAction('u32', ThirdAtom), PackAction('u32', FourthAtom), PackAction('u32', ThirdAtom))), (HeadsData[2] + bytes(2) + PackAction('u32', 1) + PackAction('u32', SecondAtom), (PackAction('u32', 1) + PackAction('u32', FourthAtom), PackAction('u32', 2) + PackAction('u32', FirstAtom), PackAction('u32', SecondAtom), PackAction('u32', 1) + PackAction('u32', FourthAtom), PackAction('u32', FourthAtom))), (HeadsData[3] + bytes(2) + PackAction('u32', 1) + PackAction('u32', ThirdAtom), (PackAction('u32', 0) + PackAction('u32', 3) + PackAction('u32', FirstAtom), PackAction('u32', SecondAtom), PackAction('u32', ThirdAtom), EdgeData)))

# this definition exists because focused behavior needs one stable owner
def ReverseTable(AtomIds: tuple[int, ...]) -> bytes:
    OutValue = bytearray()
    OutValue += PackAction('u32', 0)
    OutValue += PackAction('u32', 4294967295)
    OutValue += PackAction('u32', len(AtomIds))
    for AtomValue in AtomIds:
        OutValue += PackAction('u32', AtomValue) + PackAction('u32', 0)
    OutValue += bytes(8)
    OutValue += PackAction('u32', 4294967295)
    OutValue += PackAction('u32', 4294967295)
    OutValue += bytes(8)
    return bytes(OutValue)

# this definition exists because focused behavior needs one stable owner
def StringHandle(Params: CMgrParameters) -> bytes:
    return EncodeString(Params.part_name) + PackAction('u16', KStringHandleKind) + PackAction('u8', 0) + PackAction('u32', Params.name_stamp) + EncodeString('') + EncodeString('') + EncodeString('') + bytes(18) + EncodeString(Params.configuration_name) + bytes(20) + EncodeString('') + bytes(4)

# this definition exists because focused behavior needs one stable owner
def StampList(Stamps: tuple[FeatureStamp, ...]) -> bytes:
    OutValue = bytearray()
    OutValue += PackAction('u16', 0)
    OutValue += PackAction('u32', len(Stamps))
    for Entry in Stamps:
        OutValue += PackAction('u32', Entry.tree_id) + Entry.stamp.pack()
    OutValue += bytes(8)
    OutValue += PackAction('u32', 1)
    OutValue += bytes(8)
    return bytes(OutValue)

# this definition exists because focused behavior needs one stable owner
def BuildModel(Params: CMgrParameters) -> Model:
    Params.validate()
    Nodes: list[NodeValue] = []
    Config = AddHeadMut(Nodes, Params)
    AddLinksMut(Nodes, Params)
    AddTailMut(Nodes, Params, Config)
    return Model(header=EncodeClassDefinition(KRootClass, KClassSchema), base=KMapBase, nodes=Nodes)

# this definition exists because null records need one consistent node constructor
def AddNullMut(Nodes: list[NodeValue], BodyValue: bytes) -> None:
    Nodes.append(NodeValue(kind=NullKind, body=BodyValue))

# this definition exists because definition records need one consistent node constructor
def AddDefMut(Nodes: list[NodeValue], NameValue: str, BodyValue: bytes) -> int:
    Nodes.append(NodeValue(kind=DefinitionKind, body=BodyValue, schema=KClassSchema, class_name=NameValue))
    return len(Nodes) - 1

# this definition exists because class references need one consistent node constructor
def AddClassMut(Nodes: list[NodeValue], Target: int, BodyValue: bytes) -> None:
    Nodes.append(NodeValue(kind=ClassRefKind, body=BodyValue, class_name=Nodes[Target].class_name, target=Target))

# this definition exists because object references need one consistent node constructor
def AddObjectMut(Nodes: list[NodeValue], Target: int, BodyValue: bytes) -> None:
    Nodes.append(NodeValue(kind=ObjectRefKind, body=BodyValue, target=Target))

# this definition exists because manager identity and display records form one section
def AddHeadMut(Nodes: list[NodeValue], Params: CMgrParameters) -> int:
    AddNullMut(Nodes, ManagerHead())
    AddNullMut(Nodes, IdentityBlock(Params.atom_ids[0], Params.generation, Params.build))
    AddNullMut(Nodes, Table(KViewStyle))
    AddNullMut(Nodes, DisplayState(Params.display_stamp, Params.session_counter))
    Config = AddDefMut(Nodes, KConfigClass, b'')
    AddDefMut(Nodes, KNodeNameClass, NodeName(Params.configuration_name))
    AddDefMut(Nodes, KVisualClass, Visual(Params))
    AddNullMut(Nodes, Table(KViewStyle))
    AddNullMut(Nodes, DisplayStateA(Params))
    AddNullMut(Nodes, AtomHead(Params.atom_head_count, Params.generation))
    AddNullMut(Nodes, ConnectedAtom(Params.atom_ids) if Params.connected_history else AtomTable(Params.atom_ids))
    AddNullMut(Nodes, LinkHead(Params.link_atom_ids))
    return Config

# this definition exists because linked atom graph variants share one dispatch boundary
def AddLinksMut(Nodes: list[NodeValue], Params: CMgrParameters) -> None:
    LinkValue = -1
    if Params.terminal_parent_tree_id is not None:
        AddDefMut(Nodes, KLinkClass, TerminalLink(Params.link_atom_ids[0], Params.terminal_parent_tree_id, Params.link_tree_ids[0]))
    elif Params.connected_history:
        LinkParts = ConnectedFour(Params.link_atom_ids, Params.link_tree_ids) if len(Params.link_atom_ids) == 4 else ConnectedLink(Params.link_atom_ids, Params.link_tree_ids)
        for Position, (BodyValue, ChildBodies) in enumerate(LinkParts):
            if Position == 0:
                LinkValue = AddDefMut(Nodes, KLinkClass, BodyValue)
            else:
                AddClassMut(Nodes, LinkValue, BodyValue)
            for ChildBody in ChildBodies:
                AddNullMut(Nodes, ChildBody)
    else:
        Total = len(Params.link_atom_ids)
        for Position, AtomValue in enumerate(Params.link_atom_ids):
            Following = Params.link_atom_ids[Position + 1] if Position + 1 < Total else None
            BodyValue = LinkBody(AtomValue, Params.link_tree_ids[Position], Following)
            if Position == 0:
                LinkValue = AddDefMut(Nodes, KLinkClass, BodyValue)
            else:
                AddClassMut(Nodes, LinkValue, BodyValue)

# this definition exists because manager references and object lists form one terminal section
def AddTailMut(Nodes: list[NodeValue], Params: CMgrParameters, Config: int) -> None:
    AddNullMut(Nodes, PackAction('u32', 0) + PackAction('u32', 1) + PackAction('u32', 4294967295))
    AddNullMut(Nodes, b'')
    AddNullMut(Nodes, bytes(36))
    AddNullMut(Nodes, b'')
    AddNullMut(Nodes, PackAction('f64', -1.0))
    AddNullMut(Nodes, PackAction('f64', 0.0))
    AddNullMut(Nodes, b'')
    AddNullMut(Nodes, ReverseTable(Params.reverse_atom_ids))
    AddObjectMut(Nodes, Config, PackAction('u32', 1) + PackAction('u16', 1))
    AddObjectMut(Nodes, Config, PackAction('u32', 1))
    AddDefMut(Nodes, KExtObjectClass, b'')
    Handle = AddDefMut(Nodes, KStringHandleClass, EncodeString(''))
    AddClassMut(Nodes, Handle, StringHandle(Params))
    ObjList = AddDefMut(Nodes, KObjectListClass, StampList(Params.feature_stamps))
    AddClassMut(Nodes, ObjList, Table(KObjectListTail))

# this definition exists because focused behavior needs one stable owner
def AtomIdsFor(FeatureCount: int) -> tuple[int, ...]:
    if FeatureCount < 1:
        raise SldprtFormatError('a SOLIDWORKS part carries at least one solid feature')
    return tuple((KFirstAtomId + Index for Index in range(FeatureCount)))

# this definition exists because focused behavior needs one stable owner
def TreeIdsFor(FeatureCount: int) -> tuple[int, ...]:
    if FeatureCount < 1:
        raise SldprtFormatError('a SOLIDWORKS part carries at least one solid feature')
    return tuple((KFirstTreeId + KTreeIdStep * Index for Index in range(FeatureCount)))

# this definition exists because focused behavior needs one stable owner
def EncodeCmgr(*, FeatureTreeIds: tuple[int, ...]=KDefaultFeatureTreeIds, ConfigName: str=KDefaultConfigName, PartName: str=KDefaultPartName, NameStamp: int=0, AtomIds: tuple[int, ...] | None=None, LinkAtomIds: tuple[int, ...] | None=None, LinkTreeIds: tuple[int, ...] | None=None, ReverseAtomIds: tuple[int, ...] | None=None, FeatureStamps: tuple[FeatureStamp, ...] | None=None, DocStamp: Stamp=KDocStamp, DisplayStamp: Stamp | None=None, ViewStamp: Stamp | None=None, MaxTreeId: int | None=None, NextIdA: int=0, NextIdB: int=0, RenderStyle: int=KDefaultRenderStyle, AtomHeadCount: int | None=None, ChordRatio: float=KDisplayChordRatio, SessionCounter: int=KSessionCounter, Generation: int=KDocGeneration, Build: int=KDocBuild, DisplayGeomCache: bytes=KDisplayGeomCacheDefault, ConnectedHistory: bool=False, TerminalParentTreeId: int | None=None) -> bytes:
    Trees = tuple(FeatureTreeIds)
    if not Trees:
        raise SldprtFormatError('Contents/CMgr needs at least one solid feature tree id')
    ResolvedAtoms = tuple(AtomIds) if AtomIds else AtomIdsFor(len(Trees))
    ResolvedChain = tuple(LinkAtomIds) if LinkAtomIds is not None else ResolvedAtoms
    ResolvedTrees = tuple(LinkTreeIds) if LinkTreeIds is not None else Trees
    ResolvedReverse = tuple(ReverseAtomIds) if ReverseAtomIds is not None else tuple(reversed(ResolvedAtoms))
    ResolvedStamps = tuple(FeatureStamps) if FeatureStamps is not None else tuple((FeatureStamp(tree_id=TreeId, stamp=Stamp(DocStamp.high, DocStamp.low + Index)) for Index, TreeId in enumerate(Trees)))
    if ConnectedHistory and FeatureStamps is None:
        StampOrders = {2: (1, 0), 3: (1, 2, 0), 4: (3, 1, 2, 0)}
        ResolvedStamps = tuple((ResolvedStamps[IndexValue] for IndexValue in StampOrders[len(ResolvedStamps)]))
    if TerminalParentTreeId is not None and FeatureStamps is None:
        ResolvedStamps = (ResolvedStamps[0], FeatureStamp(tree_id=TerminalParentTreeId, stamp=Stamp(DocStamp.high, DocStamp.low + 1)))
    ResolvedNextIdA = KFirstAtomId + 1 + 4 * len(ResolvedAtoms) if ConnectedHistory and NextIdA == 0 else NextIdA
    ResolvedNextIdB = KFirstAtomId + 2 * len(ResolvedAtoms) if ConnectedHistory and NextIdB == 0 else NextIdB
    Params = CMgrParameters(configuration_name=ConfigName, part_name=PartName, name_stamp=NameStamp, atom_ids=ResolvedAtoms, link_atom_ids=ResolvedChain, link_tree_ids=ResolvedTrees, reverse_atom_ids=ResolvedReverse, feature_stamps=ResolvedStamps, display_stamp=DocStamp if DisplayStamp is None else DisplayStamp, view_stamp=DocStamp if ViewStamp is None else ViewStamp, max_tree_id=max(Trees) if MaxTreeId is None else MaxTreeId, next_id_a=ResolvedNextIdA, next_id_b=ResolvedNextIdB, render_style=RenderStyle, atom_head_count=(1 if ConnectedHistory else len(ResolvedAtoms)) if AtomHeadCount is None else AtomHeadCount, chord_ratio=ChordRatio, generation=Generation, build=Build, session_counter=SessionCounter, display_geometry_cache=bytes(DisplayGeomCache), connected_history=ConnectedHistory, terminal_parent_tree_id=TerminalParentTreeId)
    return BuildModel(Params).emit()

# this definition exists because focused behavior needs one stable owner
def DeclaredOpaque(**KwargValues: object) -> dict[str, int]:
    Stream = EncodeCmgr(**KwargValues)
    Opaque = sum((Length for Ignored, Ignored, Length in KResidualSpans))
    return {'stream_bytes': len(Stream), 'declared': len(Stream) - Opaque, 'opaque': Opaque, 'accounted': len(Stream), 'residual_spans': len(KResidualSpans)}

# this binding exists because shared behavior needs one stable value
globals()['ATOM_TABLE_HEAD'] = KAtomTableHead

# this binding exists because shared behavior needs one stable value
globals()['CLASS_REFERENCE_KIND'] = ClassRefKind

# this binding exists because shared behavior needs one stable value
globals()['CLASS_SCHEMA'] = KClassSchema

# this binding exists because shared behavior needs one stable value
globals()['CONFIGURATION_CLASS'] = KConfigClass

# this binding exists because shared behavior needs one stable value
globals()['CONFIGURATION_MANAGER_STREAM'] = KConfigManagerStream

# this binding exists because shared behavior needs one stable value
globals()['DEFAULT_CONFIGURATION_NAME'] = KDefaultConfigName

# this binding exists because shared behavior needs one stable value
globals()['DEFAULT_FEATURE_TREE_IDS'] = KDefaultFeatureTreeIds

# this binding exists because shared behavior needs one stable value
globals()['DEFAULT_PART_NAME'] = KDefaultPartName

# this binding exists because shared behavior needs one stable value
globals()['DEFAULT_RENDER_STYLE'] = KDefaultRenderStyle

# this binding exists because shared behavior needs one stable value
globals()['DEFINITION_KIND'] = DefinitionKind

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_CHORD_RATIO'] = KDisplayChordRatio

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_GEOMETRY_CACHE_BYTES'] = KDisplayGeomCacheBytes

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_GEOMETRY_CACHE_DEFAULT'] = KDisplayGeomCacheDefault

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_STATE_KIND'] = KDisplayStateKind

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_STATE_MASK'] = KDisplayStateMask

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_STATE_REVISION'] = KDisplayStateRevision

# this binding exists because shared behavior needs one stable value
globals()['DISPLAY_TAIL'] = KDisplayTail

# this binding exists because shared behavior needs one stable value
globals()['DOCUMENT_BUILD'] = KDocBuild

# this binding exists because shared behavior needs one stable value
globals()['DOCUMENT_GENERATION'] = KDocGeneration

# this binding exists because shared behavior needs one stable value
globals()['DOCUMENT_STAMP'] = KDocStamp

# this binding exists because shared behavior needs one stable value
globals()['DOCUMENT_STAMP_HIGH'] = KDocStampHigh

# this binding exists because shared behavior needs one stable value
globals()['DOCUMENT_STAMP_LOW'] = KDocStampLow

# this binding exists because shared behavior needs one stable value
globals()['EXT_OBJECT_CLASS'] = KExtObjectClass

# this binding exists because shared behavior needs one stable value
globals()['FIRST_ATOM_ID'] = KFirstAtomId

# this binding exists because shared behavior needs one stable value
globals()['FIRST_TREE_ID'] = KFirstTreeId

# this binding exists because shared behavior needs one stable value
globals()['LINK_CLASS'] = KLinkClass

# this binding exists because shared behavior needs one stable value
globals()['LINK_FLAG'] = KLinkFlag

# this binding exists because shared behavior needs one stable value
globals()['LINK_TERMINATOR'] = KLinkTerminator

# this binding exists because shared behavior needs one stable value
globals()['MANAGER_SCALE'] = KManagerScale

# this binding exists because shared behavior needs one stable value
globals()['MAP_BASE'] = KMapBase

# this binding exists because shared behavior needs one stable value
globals()['NODE_NAME_CLASS'] = KNodeNameClass

# this binding exists because shared behavior needs one stable value
globals()['NODE_NAME_FLAGS'] = KNodeNameFlags

# this binding exists because shared behavior needs one stable value
globals()['NODE_NAME_SCALE'] = KNodeNameScale

# this binding exists because shared behavior needs one stable value
globals()['NULL_KIND'] = NullKind

# this binding exists because shared behavior needs one stable value
globals()['Node'] = NodeValue

# this binding exists because shared behavior needs one stable value
globals()['OBJECT_LIST_CLASS'] = KObjectListClass

# this binding exists because shared behavior needs one stable value
globals()['OBJECT_LIST_KIND'] = KObjectListKind

# this binding exists because shared behavior needs one stable value
globals()['OBJECT_LIST_TAIL'] = KObjectListTail

# this binding exists because shared behavior needs one stable value
globals()['OBJECT_REFERENCE_KIND'] = ObjectRefKind

# this binding exists because shared behavior needs one stable value
globals()['RESIDUAL_SPANS'] = KResidualSpans

# this binding exists because shared behavior needs one stable value
globals()['ROOT_CLASS'] = KRootClass

# this binding exists because shared behavior needs one stable value
globals()['SESSION_COUNTER'] = KSessionCounter

# this binding exists because shared behavior needs one stable value
globals()['STRING_HANDLE_CLASS'] = KStringHandleClass

# this binding exists because shared behavior needs one stable value
globals()['STRING_HANDLE_KIND'] = KStringHandleKind

# this binding exists because shared behavior needs one stable value
globals()['TREE_ID_STEP'] = KTreeIdStep

# this binding exists because shared behavior needs one stable value
globals()['VIEW_STYLE'] = KViewStyle

# this binding exists because shared behavior needs one stable value
globals()['VIEW_STYLE_MODE'] = KViewStyleMode

# this binding exists because shared behavior needs one stable value
globals()['VISUAL_CLASS'] = KVisualClass

# this binding exists because shared behavior needs one stable value
globals()['VISUAL_PROPERTIES'] = KVisualProperties

# this binding exists because shared behavior needs one stable value
globals()['ZERO_STAMP'] = KZeroStamp

# this binding exists because shared behavior needs one stable value
globals()['_ConnectedAtomTable'] = ConnectedAtom

# this binding exists because shared behavior needs one stable value
globals()['_ConnectedFourLinkParts'] = ConnectedFour

# this binding exists because shared behavior needs one stable value
globals()['_ConnectedLinkParts'] = ConnectedLink

# this binding exists because shared behavior needs one stable value
globals()['_TerminalLinkBody'] = TerminalLink

# this binding exists because shared behavior needs one stable value
globals()['_atom_head'] = AtomHead

# this binding exists because shared behavior needs one stable value
globals()['_atom_table'] = AtomTable

# this binding exists because shared behavior needs one stable value
globals()['_display_state'] = DisplayState

# this binding exists because shared behavior needs one stable value
globals()['_display_state_full'] = DisplayStateA

# this binding exists because shared behavior needs one stable value
globals()['_identity_block'] = IdentityBlock

# this binding exists because shared behavior needs one stable value
globals()['_link_body'] = LinkBody

# this binding exists because shared behavior needs one stable value
globals()['_link_head'] = LinkHead

# this binding exists because shared behavior needs one stable value
globals()['_manager_head'] = ManagerHead

# this binding exists because shared behavior needs one stable value
globals()['_node_name'] = NodeName

# this binding exists because shared behavior needs one stable value
globals()['_pack'] = PackAction

# this binding exists because shared behavior needs one stable value
globals()['_reverse_table'] = ReverseTable

# this binding exists because shared behavior needs one stable value
globals()['_stamp_list'] = StampList

# this binding exists because shared behavior needs one stable value
globals()['_string_handle_body'] = StringHandle

# this binding exists because shared behavior needs one stable value
globals()['_table'] = Table

# this binding exists because shared behavior needs one stable value
globals()['_visual_properties'] = Visual

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['atom_ids_for'] = AtomIdsFor

# this binding exists because shared behavior needs one stable value
globals()['build_model'] = BuildModel

# this binding exists because shared behavior needs one stable value
globals()['dataclass'] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()['declared_opaque_split'] = DeclaredOpaque

# this binding exists because shared behavior needs one stable value
globals()['encode_class_definition'] = EncodeClassDefinition

# this binding exists because shared behavior needs one stable value
globals()['encode_cmgr_stream'] = EncodeCmgr

# this binding exists because shared behavior needs one stable value
globals()['encode_string'] = EncodeString

# this binding exists because shared behavior needs one stable value
globals()['struct'] = Struct

# this binding exists because shared behavior needs one stable value
globals()['tree_ids_for'] = TreeIdsFor
