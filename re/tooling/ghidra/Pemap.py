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


# needed to keep reverse engineering responsibilities isolated and maintainable
def Sections(ByteBlob):
    PeInfo = Struct.unpack_from('<I', ByteBlob, 60)[0]
    Machine, NsecInfo = Struct.unpack_from('<HH', ByteBlob, PeInfo + 4)
    OptSize = Struct.unpack_from('<H', ByteBlob, PeInfo + 20)[0]
    Magic = Struct.unpack_from('<H', ByteBlob, PeInfo + 24)[0]
    if Magic == 523:
        ImageBase = Struct.unpack_from('<Q', ByteBlob, PeInfo + 24 + 24)[0]
    else:
        ImageBase = Struct.unpack_from('<I', ByteBlob, PeInfo + 24 + 28)[0]
    Table = PeInfo + 24 + OptSize
    OutputDataInfo = []
    for IndexInfo in range(NsecInfo):
        BaseInfo = Table + 40 * IndexInfo
        NameTextInfo = ByteBlob[BaseInfo:BaseInfo + 8].rstrip(b'\x00').decode('latin1')
        Vsize, Vaddr, Rsize, Raddr = Struct.unpack_from('<IIII', ByteBlob, BaseInfo + 8)
        OutputDataInfo.append((NameTextInfo, Vaddr, Vsize, Raddr, Rsize))
    return (ImageBase, OutputDataInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    PathInfoData = Pathlib.Path(System.argv[1])
    ByteBlob = PathInfoData.read_bytes()
    ImageBase, SecsInfo = Sections(ByteBlob)
    print(f'image_base 0x{ImageBase:x}')
    for NameTextInfo, Vaddr, Vsize, Raddr, Rsize in SecsInfo:
        print(f'  {NameTextInfo:9s} rva=0x{Vaddr:08x} vsize=0x{Vsize:08x} raw=0x{Raddr:08x} rsize=0x{Rsize:08x}')
    for ArgInfo in System.argv[2:]:
        OffInfo = int(ArgInfo, 0)
        for NameTextInfo, Vaddr, Vsize, Raddr, Rsize in SecsInfo:
            if Raddr <= OffInfo < Raddr + Rsize:
                RvaInfo = Vaddr + (OffInfo - Raddr)
                print(f'file 0x{OffInfo:x} -> section {NameTextInfo} rva 0x{RvaInfo:x} va 0x{ImageBase + RvaInfo:x}')
                break
        else:
            print(f'file 0x{OffInfo:x} -> not in any section raw range')
if __name__ == '__main__':
    MainRunInfo()
