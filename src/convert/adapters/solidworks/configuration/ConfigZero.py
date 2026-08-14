# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
import struct as Struct
from convert.adapters.solidworks.container.Archive import encode_class_definition as EncodeClassDefinition
from convert.adapters.solidworks.programs.configuration.fillet.views.Program import EncodeTwoViewAnnotationManager as EncodeFilletAnnotation
from convert.adapters.solidworks.programs.configuration.pattern.views.Program import EncodeTwoViewAnnotationManager as EncodePatternAnnotation
from convert.adapters.solidworks.programs.configuration.default.Program import ConfigOps, EncodeProgram, FieldOwners
from convert.adapters.solidworks.programs.configuration.views.pair.Program import EncodeTwoViewAnnotationManager as EncodeTwoViewAnnotation
from convert.adapters.solidworks.container.Container import SldprtFormatError

# this binding exists because shared behavior needs one stable value
KMoVersion = 18000

# this binding exists because shared behavior needs one stable value
KRefSessionStamp = 1

# this binding exists because shared behavior needs one stable value
KRefAtomId = 101

# this binding exists because shared behavior needs one stable value
KRefTreeId = 32

# this binding exists because shared behavior needs one stable value
KRefPartName = 'Part70'

# this binding exists because shared behavior needs one stable value
KRefHighWater = (101, 103)

# this binding exists because shared behavior needs one stable value
KRefShaTwoFiveSix = 'a0877db37735da4027459d8161425843e3ad90f1e3e90dc32835f9370dd643bb'

# this binding exists because shared behavior needs one stable value
KRefLength = 25214

# this binding exists because shared behavior needs one stable value
KSingleLengthUnitLength = 25148

# this binding exists because shared behavior needs one stable value
KTwoViewAnnotationBytes = 260

# this binding exists because shared behavior needs one stable value
KFilletAnnotationBytes = 258

# this binding exists because shared behavior needs one stable value
KPatternAnnotationBytes = 188

# this binding exists because shared behavior needs one stable value
KFilletAtomParentRelative = 60

# this binding exists because shared behavior needs one stable value
KFilletAtomLinkStampA = (84, 92)

# this binding exists because shared behavior needs one stable value
KFilletAtomLinkStamp = 650

# this binding exists because shared behavior needs one stable value
KPerFeatureAtomBytes = 88

# this binding exists because shared behavior needs one stable value
KPerSolidBodyBytes = 16

# this binding exists because shared behavior needs one stable value
KMeasuredVolumeMmThree = 8000.000000000001

# this binding exists because shared behavior needs one stable value
KConfigFieldCount = len(ConfigOps)

# this binding exists because shared behavior needs one stable value
KConfigOwnerCount = len(FieldOwners)

# this binding exists because shared behavior needs one stable value
KConfigOpaqueBytes = 0

# high water derivation stays separate because atom allocation has its own validation contract
def GetHighWater(Atoms: tuple[tuple[int, int], ...], HighWater: tuple[int, int] | None) -> tuple[int, int]:
    if HighWater is None:
        if not Atoms:
            raise SldprtFormatError('Contents/Config-0 needs at least one atom record')
        HighestId = max((AtomId for AtomId, TreeId in Atoms))
        return (HighestId, HighestId + 2 * len(Atoms))
    return HighWater


# terminal atom patching owns its recovered offsets so ordinary configuration encoding stays declarative
def PatchTerminal(StreamData: bytes, Atoms: tuple[tuple[int, int], ...], TerminalTreeId: int | None) -> bytes:
    if TerminalTreeId is None:
        return StreamData
    if len(Atoms) != 1 or not 1 <= TerminalTreeId <= 4294967295 or TerminalTreeId == Atoms[0][1]:
        raise SldprtFormatError('Config-0 terminal history requires one child atom and one distinct parent tree')
    AtomTag = EncodeClassDefinition('moAtom_c', 1)
    AtomStart = StreamData.find(AtomTag)
    if AtomStart < 0:
        raise SldprtFormatError('Config-0 terminal atom boundary changed')
    PatchedData = bytearray(StreamData)
    Struct.pack_into('<I', PatchedData, AtomStart + KFilletAtomParentRelative, TerminalTreeId)
    for RelativeOffset in KFilletAtomLinkStampA:
        Struct.pack_into('<I', PatchedData, AtomStart + RelativeOffset, KFilletAtomLinkStamp)
    return bytes(PatchedData)


# annotation variant selection remains explicit because each recovered manager has distinct bytes
def GetAnnotManager(VariantName: str, TerminalTreeId: int | None) -> bytes:
    if TerminalTreeId is not None:
        if VariantName != 'default':
            raise SldprtFormatError('terminal Config-0 history has a fixed annotation variant')
        return EncodeFilletAnnotation()
    if VariantName in {'linear_pattern', 'circular_pattern'}:
        return EncodePatternAnnotation()
    if VariantName == 'default':
        return EncodeTwoViewAnnotation()
    raise SldprtFormatError(f'unsupported Config-0 annotation variant {VariantName!r}')


# two view insertion owns boundary validation so the main encoder cannot splice unchecked offsets
def AddSecondView(StreamData: bytes, ViewCount: int, TerminalTreeId: int | None, VariantName: str) -> bytes:
    if ViewCount != 2:
        raise SldprtFormatError('Contents/Config-0 supports one or two recovered annotation views')
    AnnotationTag = EncodeClassDefinition('moAnnotationView_c', 1)
    MarkTag = EncodeClassDefinition('moPMarkRecord_c', 1)
    AnnotationStart = StreamData.find(AnnotationTag)
    AnnotationEnd = StreamData.find(MarkTag, AnnotationStart)
    CountOffset = AnnotationStart - 2
    if AnnotationStart < 2 or AnnotationEnd < 0 or Struct.unpack_from('<H', StreamData, CountOffset)[0] != 1:
        raise SldprtFormatError('Config-0 annotation manager boundaries changed')
    ManagerData = GetAnnotManager(VariantName, TerminalTreeId)
    return StreamData[:CountOffset] + Struct.pack('<H', ViewCount) + ManagerData + StreamData[AnnotationEnd:]


# public configuration encoding composes allocation terminal history and annotation phases
def EncodeConfig(PartName: str=KRefPartName, Atoms: tuple[tuple[int, int], ...]=((KRefAtomId, KRefTreeId),), SessionStamp: int=KRefSessionStamp, Generation: int=KMoVersion, DualLengthUnits: bool=True, HighWater: tuple[int, int] | None=None, PartRecordBody: bytes | None=None, AnnotationViewCount: int=1, TerminalParentTreeId: int | None=None, AnnotationViewVariant: str='default') -> bytes:
    if PartRecordBody is not None:
        raise SldprtFormatError('custom raw Config-0 prologue bodies are forbidden by first-principles writing')
    ResolvedHighWater = GetHighWater(Atoms, HighWater)
    StreamData = EncodeProgram(PartName=PartName, Atoms=tuple(Atoms), SessionStamp=SessionStamp, Generation=Generation, DualLengthUnits=DualLengthUnits, HighWater=ResolvedHighWater)
    StreamData = PatchTerminal(StreamData, Atoms, TerminalParentTreeId)
    if AnnotationViewCount == 1:
        if TerminalParentTreeId is not None:
            raise SldprtFormatError('Config-0 terminal fillet history requires its two annotation views')
        if AnnotationViewVariant != 'default':
            raise SldprtFormatError('Config-0 annotation variants require two annotation views')
        return StreamData
    return AddSecondView(StreamData, AnnotationViewCount, TerminalParentTreeId, AnnotationViewVariant)

# this definition exists because focused behavior needs one stable owner
def DeclaredOpaque(**KwargValues: object) -> dict[str, int]:
    StreamData = EncodeConfig(**KwargValues)
    return {'stream_bytes': len(StreamData), 'typed': len(StreamData), 'opaque': KConfigOpaqueBytes, 'accounted': len(StreamData), 'operations': KConfigFieldCount, 'owners': KConfigOwnerCount}

# this binding exists because shared behavior needs one stable value
globals()['CONFIG_FIELD_COUNT'] = KConfigFieldCount

# this binding exists because shared behavior needs one stable value
globals()['CONFIG_OPAQUE_BYTES'] = KConfigOpaqueBytes

# this binding exists because shared behavior needs one stable value
globals()['CONFIG_OWNER_COUNT'] = KConfigOwnerCount

# this binding exists because shared behavior needs one stable value
globals()['EncodeFilletAnnotationManager'] = EncodeFilletAnnotation

# this binding exists because shared behavior needs one stable value
globals()['EncodePatternAnnotationManager'] = EncodePatternAnnotation

# this binding exists because shared behavior needs one stable value
globals()['EncodeTwoViewAnnotationManager'] = EncodeTwoViewAnnotation

# this binding exists because shared behavior needs one stable value
globals()['FILLET_ANNOTATION_BYTES'] = KFilletAnnotationBytes

# this binding exists because shared behavior needs one stable value
globals()['FILLET_ATOM_LINK_STAMP'] = KFilletAtomLinkStamp

# this binding exists because shared behavior needs one stable value
globals()['FILLET_ATOM_LINK_STAMP_RELATIVES'] = KFilletAtomLinkStampA

# this binding exists because shared behavior needs one stable value
globals()['FILLET_ATOM_PARENT_RELATIVE'] = KFilletAtomParentRelative

# this binding exists because shared behavior needs one stable value
globals()['MEASURED_VOLUME_MM3'] = KMeasuredVolumeMmThree

# this binding exists because shared behavior needs one stable value
globals()['MO_VERSION'] = KMoVersion

# this binding exists because shared behavior needs one stable value
globals()['PATTERN_ANNOTATION_BYTES'] = KPatternAnnotationBytes

# this binding exists because shared behavior needs one stable value
globals()['PER_FEATURE_ATOM_BYTES'] = KPerFeatureAtomBytes

# this binding exists because shared behavior needs one stable value
globals()['PER_SOLID_BODY_BYTES'] = KPerSolidBodyBytes

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_ATOM_ID'] = KRefAtomId

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_HIGH_WATER'] = KRefHighWater

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_LENGTH'] = KRefLength

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_PART_NAME'] = KRefPartName

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_SESSION_STAMP'] = KRefSessionStamp

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_SHA256'] = KRefShaTwoFiveSix

# this binding exists because shared behavior needs one stable value
globals()['REFERENCE_TREE_ID'] = KRefTreeId

# this binding exists because shared behavior needs one stable value
globals()['SINGLE_LENGTH_UNIT_LENGTH'] = KSingleLengthUnitLength

# this binding exists because shared behavior needs one stable value
globals()['TWO_VIEW_ANNOTATION_BYTES'] = KTwoViewAnnotationBytes

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['declared_opaque_split'] = DeclaredOpaque

# this binding exists because shared behavior needs one stable value
globals()['encode_class_definition'] = EncodeClassDefinition

# this binding exists because shared behavior needs one stable value
globals()['encode_config0_stream'] = EncodeConfig

# this binding exists because shared behavior needs one stable value
globals()['struct'] = Struct
