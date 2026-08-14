# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import pathlib as Pathlib
import struct as Struct
import sys as System
System.path.insert(0, str(Pathlib.Path(__file__).resolve().parent))
from Pemap import Sections


# needed to keep reverse engineering responsibilities isolated and maintainable
def RvaToFile(SecsInfo, RvaInfo):
    for NameTextInfo, Vaddr, Vsize, Raddr, Rsize in SecsInfo:
        if Vaddr <= RvaInfo < Vaddr + max(Vsize, Rsize):
            return Raddr + (RvaInfo - Vaddr)
    return None


# needed to keep reverse engineering responsibilities isolated and maintainable
def Exports(PathInfoData):
    ByteBlob = PathInfoData.read_bytes()
    ImageBase, SecsInfo = Sections(ByteBlob)
    PeInfo = Struct.unpack_from('<I', ByteBlob, 60)[0]
    Magic = Struct.unpack_from('<H', ByteBlob, PeInfo + 24)[0]
    DdInfo = PeInfo + 24 + (112 if Magic == 523 else 96)
    EdirRva, EdirSize = Struct.unpack_from('<II', ByteBlob, DdInfo)
    BaseInfo = RvaToFile(SecsInfo, EdirRva)
    CountFuncs, CountNames = Struct.unpack_from('<II', ByteBlob, BaseInfo + 20)
    AddrFuncs, AddrNames, AddrOrds = Struct.unpack_from('<III', ByteBlob, BaseInfo + 28)
    Fbase = RvaToFile(SecsInfo, AddrFuncs)
    Nbase = RvaToFile(SecsInfo, AddrNames)
    Obase = RvaToFile(SecsInfo, AddrOrds)
    OutputDataInfo = []
    for IndexInfo in range(CountNames):
        NameRva = Struct.unpack_from('<I', ByteBlob, Nbase + 4 * IndexInfo)[0]
        NoffInfo = RvaToFile(SecsInfo, NameRva)
        EndIndex = ByteBlob.index(b'\x00', NoffInfo)
        NameTextInfo = ByteBlob[NoffInfo:EndIndex].decode('latin1')
        IndexData = Struct.unpack_from('<H', ByteBlob, Obase + 2 * IndexInfo)[0]
        FuncRva = Struct.unpack_from('<I', ByteBlob, Fbase + 4 * IndexData)[0]
        OutputDataInfo.append((NameTextInfo, FuncRva, ImageBase + FuncRva))
    return (ImageBase, OutputDataInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    PathInfoData = Pathlib.Path(System.argv[1])
    KeysInfo = System.argv[2:]
    ImageBase, Table = Exports(PathInfoData)
    print(f'image_base 0x{ImageBase:x} exports {len(Table)}')
    for NameTextInfo, RvaInfo, VaInfo in Table:
        if KeysInfo and (not any((KeyIndex in NameTextInfo for KeyIndex in KeysInfo))):
            continue
        print(f'  0x{VaInfo:x} rva=0x{RvaInfo:x} {NameTextInfo}')
if __name__ == '__main__':
    MainRunInfo()
