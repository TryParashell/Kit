# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import collections as Collects
import json as JsonData
import pathlib as Pathlib
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[4]
System.path.insert(0, str(KRootInfo / 'src'))
from convert.adapters.solidworks.container.Container import SldprtArchive
from scan_endspec import NAMES as KNames, marker as Marker, parts as Parts

# needed to keep reverse engineering responsibilities isolated and maintainable
KStream = 'Contents/Config-0-ResolvedFeatures'

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = Pathlib.Path(__file__).resolve().parents[4] / 're/data'

# needed to keep reverse engineering responsibilities isolated and maintainable
KLASS = 'moRevEndSpec_c'


# needed to keep reverse engineering responsibilities isolated and maintainable
def Decode(ByteBlob, DataValue):
    TagsInfo = [Struct.unpack_from('<H', ByteBlob, DataValue + 20 + 2 * KeyIndex)[0] for KeyIndex in range(4)]
    if any((TagInfoInfo != 0 for TagInfoInfo in TagsInfo)):
        return None
    return {'data': DataValue, 'singleEnd': Struct.unpack_from('<i', ByteBlob, DataValue)[0], 'f138': Struct.unpack_from('<i', ByteBlob, DataValue + 4)[0], 'f13c': Struct.unpack_from('<i', ByteBlob, DataValue + 8)[0], 'type0': Struct.unpack_from('<i', ByteBlob, DataValue + 12)[0], 'type1': Struct.unpack_from('<i', ByteBlob, DataValue + 16)[0], 'd38': Struct.unpack_from('<d', ByteBlob, DataValue + 28)[0], 'd40': Struct.unpack_from('<d', ByteBlob, DataValue + 36)[0], 'offsetReverse0': Struct.unpack_from('<i', ByteBlob, DataValue + 44)[0], 'offsetReverse1': Struct.unpack_from('<i', ByteBlob, DataValue + 48)[0]}


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo():
    Roots = System.argv[1:] or ['.rescratch/corpus/parts', '.rescratch/corpus2', 'examples']
    Needle = Marker(KLASS)
    Histogram = Collects.Counter()
    GetRows = []
    for PathInfoData in Parts(Roots):
        try:
            ArchiveInfo = SldprtArchive.open(PathInfoData)
            ByteBlob = ArchiveInfo.get(KStream)
        except Exception:
            continue
        if not ByteBlob:
            continue
        PosInfo = ByteBlob.find(Needle)
        if PosInfo < 0:
            continue
        Record = Decode(ByteBlob, PosInfo + 6 + len(KLASS))
        if Record is None:
            continue
        Histogram[Record['type0'], Record['type1'], Record['singleEnd'], Record['d38'], Record['d40']] += 1
        GetRows.append({'part': PathInfoData.name.encode('ascii', 'replace').decode('ascii'), **Record})
    print(f'parts with a {KLASS} definition: {len(GetRows)}')

    # needed to keep reverse engineering responsibilities isolated and maintainable
    for KeyName, CountInfo in sorted(Histogram.items(), key=lambda KvInfo: -KvInfo[1]):
        TZero, TOneInfo, Single, DThreeEight, DFourZero = KeyName
        print(f"  type0={TZero} ({KNames.get(TZero, '?')}) type1={TOneInfo} singleEnd={Single} d@0x38={DThreeEight!r} d@0x40={DFourZero!r} n={CountInfo}")
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / 'ScanRevendspec.json').write_text(JsonData.dumps(GetRows, indent=1))
if __name__ == '__main__':
    MainRunInfo()
