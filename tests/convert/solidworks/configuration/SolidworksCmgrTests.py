# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
import struct as StructLib
import pytest as PytestLib
from convert.adapters.solidworks.container.Cmgr import ATOM_TABLE_HEAD as HeadInfo, CONFIGURATION_MANAGER_STREAM as Stream, DISPLAY_GEOMETRY_CACHE_BYTES as Bytes, DOCUMENT_BUILD as Build, DOCUMENT_GENERATION as Generation, FIRST_ATOM_ID as IdInfo, OBJECT_LIST_TAIL as TailInfo, RESIDUAL_SPANS as Spans, ROOT_CLASS as Class, VIEW_STYLE as Style, VISUAL_PROPERTIES as Properties, atom_ids_for as AtomIdsFor, declared_opaque_split as DeclaredOpaqueSplit, encode_cmgr_stream as EncodeCmgrStream, tree_ids_for as TreeIdsFor
from convert.adapters.solidworks.container.Container import SldprtFormatError

# centralizes shared evidence so every related assertion uses one value
KBytesA = 1957

# centralizes shared evidence so every related assertion uses one value
KDigest = '96d8137fb0ea8d4f5f7eb9c159ec5434903ccde9aee55334dd1e1ed59243f44c'

# centralizes shared evidence so every related assertion uses one value
KBytesD = 2081

# centralizes shared evidence so every related assertion uses one value
KDigestA = '964995442cbf20936436d7ee4a38a5819b6bdb9a9071f740b31e8e2fca92a81d'

# centralizes shared evidence so every related assertion uses one value
KBytesC = 62

# centralizes shared evidence so every related assertion uses one value
KBytes = 1957

# centralizes shared evidence so every related assertion uses one value
KBytesB = 0

# centralizes shared evidence so every related assertion uses one value
KCount = 0

# centralizes shared evidence so every related assertion uses one value
KMmThree = (1476.0000000000002, 11954.000000000002)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestOFDMTMD():
    StreamA = EncodeCmgrStream()
    assert len(StreamA) == KBytesA
    assert Hashlib.sha256(StreamA).hexdigest() == KDigest

# keeps this focused behavior isolated so regressions remain immediately visible
def TestTFDMTMD():
    StreamA = EncodeCmgrStream(feature_tree_ids=TreeIdsFor(3))
    assert len(StreamA) == KBytesD
    assert Hashlib.sha256(StreamA).hexdigest() == KDigestA

# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize('Features', (1, 2, 3, 4, 5, 6, 7, 8))
def TestSFTMPFSL(Features):
    StreamA = EncodeCmgrStream(feature_tree_ids=TreeIdsFor(Features))
    assert len(StreamA) == KBytesA + KBytesC * (Features - 1)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestCTFHUTRLGA() -> None:
    StreamData = EncodeCmgrStream(feature_tree_ids=(32, 40), connected_history=True)
    assert len(StreamData) == 2059
    assert StructLib.pack('<III', 1, 102, 101) in StreamData
    assert StructLib.pack('<III', 40, 110, 105) in StreamData
    assert StructLib.pack('<HI', 0, 2) + StructLib.pack('<III', 40, 31269785, 268435457) + StructLib.pack('<III', 32, 31269785, 268435456) in StreamData

# keeps this focused behavior isolated so regressions remain immediately visible
def TestCTFHUTRLG() -> None:
    StreamData = EncodeCmgrStream(feature_tree_ids=(32, 40, 47), connected_history=True)
    assert len(StreamData) == 2173
    assert StructLib.pack('<IIIII', 2, 103, 102, 102, 101) in StreamData
    assert StructLib.pack('<IIIII', 2, 102, 101, 103, 102) in StreamData
    assert StructLib.pack('<HI', 0, 3) + StructLib.pack('<III', 40, 31269785, 268435457) + StructLib.pack('<III', 47, 31269785, 268435458) + StructLib.pack('<III', 32, 31269785, 268435456) in StreamData

# keeps this focused behavior isolated so regressions remain immediately visible
def TestCFFHUTRLG() -> None:
    StreamData = EncodeCmgrStream(feature_tree_ids=(32, 40, 47, 54), connected_history=True)
    assert len(StreamData) == 2299
    assert StructLib.pack('<IIIIIII', 3, 104, 103, 103, 102, 102, 101) in StreamData
    assert StructLib.pack('<IIIIIII', 3, 102, 101, 103, 102, 104, 103) in StreamData
    assert StructLib.pack('<HI', 0, 4) + StructLib.pack('<III', 54, 31269785, 268435459) + StructLib.pack('<III', 40, 31269785, 268435457) + StructLib.pack('<III', 47, 31269785, 268435458) + StructLib.pack('<III', 32, 31269785, 268435456) in StreamData

# keeps this focused behavior isolated so regressions remain immediately visible
def TestTFHUTRLB() -> None:
    StreamData = EncodeCmgrStream(feature_tree_ids=(34,), part_name='Part1', terminal_parent_tree_id=32)
    TerminalBody = StructLib.pack('<IHI', 101, 1, 32) + StructLib.pack('<II', 1, 34) + bytes(30) + StructLib.pack('<I', 2) + bytes(8)
    assert len(StreamData) == 1973
    assert TerminalBody in StreamData
    assert StructLib.pack('<HI', 0, 2) + StructLib.pack('<III', 34, 31269785, 268435456) + StructLib.pack('<III', 32, 31269785, 268435457) in StreamData

# keeps this focused behavior isolated so regressions remain immediately visible
def TestDAOBTTS():
    Split = DeclaredOpaqueSplit()
    assert Split['stream_bytes'] == KBytesA
    assert Split['declared'] == KBytes
    assert Split['opaque'] == KBytesB
    assert Split['residual_spans'] == KCount
    assert Split['declared'] + Split['opaque'] == Split['accounted']
    assert Split['accounted'] == Split['stream_bytes']

# keeps this focused behavior isolated so regressions remain immediately visible
def TestDGCIFTRZD():
    assert Spans == ()
    assert KBytesB == 0

# keeps this focused behavior isolated so regressions remain immediately visible
def TestTSDCIRZD():
    StreamA = EncodeCmgrStream()
    assert bytes(Bytes) in StreamA

# keeps this focused behavior isolated so regressions remain immediately visible
def TestTSCEFC():
    for Features in (1, 4, 8):
        Split = DeclaredOpaqueSplit(feature_tree_ids=TreeIdsFor(Features))
        assert Split['opaque'] == 0
        assert Split['declared'] == Split['stream_bytes']

# keeps this focused behavior isolated so regressions remain immediately visible
def TestTHTRV():
    assert Generation == 18000
    assert Build == 2025268
    assert IdInfo == 101
    assert Stream == 'Contents/CMgr'
    assert len(Properties) == 77
    assert len(HeadInfo) == 13
    assert len(Style) == 9
    assert len(TailInfo) == 7
    assert dict(((NameText, ItemValue) for NameText, IgnoredValue, ItemValue in Properties))['material_name'] == 'Steel'

# keeps this focused behavior isolated so regressions remain immediately visible
def TestAIATIRFTRFV():
    assert AtomIdsFor(3) == (101, 102, 103)
    assert TreeIdsFor(3) == (32, 40, 48)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestSOWTCMCD():
    StreamA = EncodeCmgrStream()
    assert StreamA.startswith(b'\xff\xff\x01\x00' + bytes((len(Class), 0)))
    assert Class.encode('ascii') in StreamA

# keeps this focused behavior isolated so regressions remain immediately visible
def NamedTPNLMTSBTB():
    Short = EncodeCmgrStream(part_name='Part1')
    LongInfo = EncodeCmgrStream(part_name='Part70')
    assert len(LongInfo) == len(Short) + 2

# keeps this focused behavior isolated so regressions remain immediately visible
def TestMVARATPD():
    assert KMmThree == (1476.0000000000002, 11954.000000000002)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestAFDGIR():
    with PytestLib.raises(SldprtFormatError, match='generation'):
        EncodeCmgrStream(generation=14000)

# keeps this focused behavior isolated so regressions remain immediately visible
def TestAEFSIR():
    with PytestLib.raises(SldprtFormatError, match='at least one solid feature'):
        EncodeCmgrStream(feature_tree_ids=())

# keeps this focused behavior isolated so regressions remain immediately visible
def TestASDGCIR():
    with PytestLib.raises(SldprtFormatError, match='display_geometry_cache'):
        EncodeCmgrStream(display_geometry_cache=bytes(64))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestANDGCIR():
    with PytestLib.raises(SldprtFormatError, match='display_geometry_cache'):
        EncodeCmgrStream(display_geometry_cache=b'\x01' + bytes(Bytes - 1))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestALCWOTIPAIR():
    with PytestLib.raises(SldprtFormatError, match='tree ids'):
        EncodeCmgrStream(feature_tree_ids=(32, 40), link_atom_ids=(101, 102), link_tree_ids=(32,))

# keeps this focused behavior isolated so regressions remain immediately visible
def TestAZFATIR():
    with PytestLib.raises(SldprtFormatError, match='at least one solid feature'):
        AtomIdsFor(0)
    with PytestLib.raises(SldprtFormatError, match='at least one solid feature'):
        TreeIdsFor(0)
