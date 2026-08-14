# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import argparse as Argparse
import json as JsonData
import re as Regex
from typing import Dict as DictInfo, List as ListInfo, Optional, Tuple


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLegacyAttr(SelfRef, NameText):
    AliasName = SelfRef.KAliasNames.get(NameText)
    if AliasName is None:
        raise AttributeError(NameText)
    return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetLegacyMut(SelfRef, NameText, ValueData):
    TargetName = SelfRef.KAliasNames.get(NameText, NameText)
    object.__setattr__(SelfRef, TargetName, ValueData)

# needed to keep reverse engineering responsibilities isolated and maintainable
KScalarWidth = {'uchar': 1, 'char': 1, 'ushort': 2, 'short': 2, 'long': 4, 'ulong': 4, 'int': 4, 'uint': 4, 'float': 4, 'double': 8, '__int64': 8, 'int64': 8}

# needed to keep reverse engineering responsibilities isolated and maintainable
KBlockStartRe = Regex.compile('^=== FUNCTION (.+)$')

# needed to keep reverse engineering responsibilities isolated and maintainable
KAddressRe = Regex.compile('^=== ADDRESS ([0-9a-fA-F]+)$')

# needed to keep reverse engineering responsibilities isolated and maintainable
KGetReInfo = Regex.compile('su_CArchive::AR_get_([A-Za-z0-9_]+)\\s*\\(')

# needed to keep reverse engineering responsibilities isolated and maintainable
KPutRe = Regex.compile('su_CArchive::AR_put_([A-Za-z0-9_]+)\\s*\\(')

# needed to keep reverse engineering responsibilities isolated and maintainable
KDeclRe = Regex.compile('^\\s*(?:void|undefined\\d*|int|uint|longlong)\\s+[A-Za-z_][A-Za-z0-9_:<>,\\s]*?\\(\\s*([A-Za-z_][A-Za-z0-9_:<>,\\s]*?)\\s*(\\*+)?\\s*(this|param_1)\\s*[,)]')

# needed to keep reverse engineering responsibilities isolated and maintainable
KPointerScale = {'longlong': 8, 'ulonglong': 8, 'double': 8, 'int64': 8, '__int64': 8, 'int': 4, 'uint': 4, 'long': 4, 'ulong': 4, 'float': 4, 'short': 2, 'ushort': 2, 'wchar_t': 2}

# needed to keep reverse engineering responsibilities isolated and maintainable
KReadObjectRe = Regex.compile('(?:su_CArchive|su_CDBArchive)::ReadObject\\s*\\([^;]*?class([A-Za-z0-9_]+)')

# needed to keep reverse engineering responsibilities isolated and maintainable
KGlobalReadRe = Regex.compile('(?<!su_CArchive)(?<!su_CDBArchive)::operator>>\\s*\\(')

# needed to keep reverse engineering responsibilities isolated and maintainable
KCstringRe = Regex.compile('CStringT<wchar_t')

# needed to keep reverse engineering responsibilities isolated and maintainable
KSlotFiveRe = Regex.compile('\\(\\*\\*\\(code \\*\\*\\)\\(\\*\\(longlong \\*\\)\\((?:this|param_1)\\s*\\+\\s*(0x[0-9a-fA-F]+|\\d+)\\)\\s*\\+\\s*0x28\\)\\)')

# needed to keep reverse engineering responsibilities isolated and maintainable
KStringRe = Regex.compile('"([^"\\\\]{1,64})"')

# needed to keep reverse engineering responsibilities isolated and maintainable
KBaseCallRe = Regex.compile('\\b((?:FUN_[0-9a-f]+)|(?:[A-Za-z_][A-Za-z0-9_]*::Serialize))\\s*\\(\\s*(?:\\([A-Za-z0-9_:<>,\\s]*\\*+\\)\\s*)?(?:this|param_1)\\s*,\\s*(?:param_1|param_2)\\s*\\)')

# needed to keep reverse engineering responsibilities isolated and maintainable
KBaseSerialRe = Regex.compile('\\b([A-Za-z_][A-Za-z0-9_]*)::Serialize\\s*\\(')

# needed to keep reverse engineering responsibilities isolated and maintainable
KDbkeyNameRe = Regex.compile('CStringT\\s*\\(\\s*[^,]+,\\s*"([^"]+)"')

# needed to keep reverse engineering responsibilities isolated and maintainable
KReadCountRe = Regex.compile('su_CArchive::ReadCount\\s*\\(')

# needed to keep reverse engineering responsibilities isolated and maintainable
KVersionCmpRe = Regex.compile('(0x[0-9a-fA-F]+|\\d+)\\s*<\\s*(?:\\(int\\))?\\s*([iu]Var\\d+)|([iu]Var\\d+)\\s*<\\s*(0x[0-9a-fA-F]+|\\d+)')

# needed to keep reverse engineering responsibilities isolated and maintainable
KHasConditionRe = Regex.compile('hasCondition\\s*\\([^,]+,\\s*(0x[0-9a-fA-F]+|\\d+)\\s*\\)')


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParseInt(TextValueData: str) -> int:
    return int(TextValueData, 16) if TextValueData.lower().startswith('0x') else int(TextValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
def StripComments(TextValueData: str) -> str:
    return Regex.sub('/\\*.*?\\*/', ' ', TextValueData, flags=Regex.S)


# needed to keep reverse engineering responsibilities isolated and maintainable
class DumpRecord:


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __init__(SelfRef, Paths: ListInfo[str]) -> None:
        SelfRef.ByAddress: DictInfo[str, dict] = {}
        for PathInfoData in Paths:
            RawData = open(PathInfoData, encoding='utf-8', errors='replace').read()
            Lines = RawData.splitlines()
            Starts = [IndexInfo for IndexInfo, LineText in enumerate(Lines) if LineText.startswith('=== FUNCTION ')]
            Starts.append(len(Lines))
            for KeyIndex in range(len(Starts) - 1):
                Chunk = Lines[Starts[KeyIndex]:Starts[KeyIndex + 1]]
                NameTextInfo = KBlockStartRe.match(Chunk[0]).group(1).strip()
                Address = ''
                for LineText in Chunk[:6]:
                    Match = KAddressRe.match(LineText)
                    if Match:
                        Address = Match.group(1).lower()
                        break
                if not Address:
                    continue
                Record = {'name': NameTextInfo, 'address': Address, 'source': '%s:%d' % (PathInfoData.replace('\\', '/').rsplit('/', 1)[-1], Starts[KeyIndex] + 1), 'body': '\n'.join(Chunk)}
                SelfRef.ByAddress.setdefault(Address, Record)
        SelfRef.ByName: DictInfo[str, dict] = {}
        for Record in SelfRef.ByAddress.values():
            SelfRef.ByName.setdefault(Record['name'], Record)


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def GetValue(SelfRef, Address: str) -> Optional[dict]:
        return SelfRef.ByAddress.get(Address.lower())


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def ResolveInfo(SelfRef, Token: str) -> Optional[dict]:
        if Token.startswith('FUN_'):
            return SelfRef.GetValue(Token[4:])
        return SelfRef.ByName.get(Token)
    KAliasNames = {'get': 'GetValue', 'resolve': 'ResolveInfo'}

# needed to keep reverse engineering responsibilities isolated and maintainable
DumpRecord.__getattr__ = GetLegacyAttr

# needed to keep reverse engineering responsibilities isolated and maintainable
DumpRecord.__setattr__ = SetLegacyMut


# needed to keep reverse engineering responsibilities isolated and maintainable
def ConditionStack(BodyInfo: str) -> ListInfo[Tuple[int, str]]:
    TextValueData = StripComments(BodyInfo)
    Lines = TextValueData.splitlines()
    Stack: ListInfo[Tuple[int, str]] = []
    Result: ListInfo[Tuple[int, str]] = []
    Depth = 0
    Pending: Optional[str] = None
    for LineText in Lines:
        Stripped = LineText.strip()
        Match = Regex.match('^(?:\\}\\s*else\\s+)?if\\s*\\((.*)$', Stripped)
        if Match:
            Pending = Match.group(1)
        elif Stripped.startswith('} else'):
            Pending = '!previous'
        Opens = LineText.count('{')
        Closes = LineText.count('}')
        for SpareValue in range(Closes):
            if Stack and Stack[-1][0] == Depth:
                Stack.pop()
            Depth = max(0, Depth - 1)
        for SpareValue in range(Opens):
            Depth += 1
            Stack.append((Depth, Pending or ''))
            Pending = None
        Result.append((Depth, ' && '.join((ThirdValue for SpareValue, ThirdValue in Stack if ThirdValue))))
    return Result


# needed to keep reverse engineering responsibilities isolated and maintainable
def VersionGates(Condition: str) -> ListInfo[str]:
    Gates: ListInfo[str] = []
    for Match in KVersionCmpRe.finditer(Condition):
        if Match.group(1):
            Gates.append('version > %d' % ParseInt(Match.group(1)))
        elif Match.group(4):
            Gates.append('version < %d' % ParseInt(Match.group(4)))
    for Match in KHasConditionRe.finditer(Condition):
        Gates.append('hasCondition(0x%x)' % ParseInt(Match.group(1)))
    return Gates


# needed to keep reverse engineering responsibilities isolated and maintainable
def ObjectParam(BodyInfo: str) -> Tuple[str, int]:
    for LineText in StripComments(BodyInfo).splitlines():
        Match = KDeclRe.match(LineText)
        if Match:
            BaseInfo = (Match.group(1) or '').strip().split()[-1]
            Stars = Match.group(2) or ''
            NameTextInfo = Match.group(3)
            if len(Stars) >= 2:
                return (NameTextInfo, 8)
            return (NameTextInfo, KPointerScale.get(BaseInfo, 1))
    return ('param_1', 1)


# needed to keep reverse engineering responsibilities isolated and maintainable
def StructOffsets(LineText: str, Holder: str, Scale: int) -> ListInfo[int]:
    Found: ListInfo[int] = []
    Pattern = Regex.compile('\\(\\s*%s\\s*\\+\\s*(?:\\(longlong\\)[A-Za-z0-9_]+\\s*\\*\\s*\\d+\\s*\\+\\s*)?(0x[0-9a-fA-F]+|\\d+)\\s*\\)' % Regex.escape(Holder))
    for Match in Pattern.finditer(LineText):
        Found.append(ParseInt(Match.group(1)) * Scale)
    Subscript = Regex.compile('%s\\[\\s*(0x[0-9a-fA-F]+|\\d+)\\s*\\]' % Regex.escape(Holder))
    for Match in Subscript.finditer(LineText):
        Found.append(ParseInt(Match.group(1)) * Scale)
    if not Found and Regex.search('\\)\\s*%s\\s*[,)]' % Regex.escape(Holder), LineText):
        Found.append(0)
    return Found


# needed to keep reverse engineering responsibilities isolated and maintainable
def ExtractOps(Record: dict) -> dict:
    BodyInfo = Record['body']
    TextValueData = StripComments(BodyInfo)
    Lines = TextValueData.splitlines()
    Conditions = ConditionStack(BodyInfo)
    Holder, Scale = ObjectParam(BodyInfo)
    Reads: ListInfo[dict] = []
    Writes: ListInfo[dict] = []
    Bases: ListInfo[str] = []
    Dbkeys: ListInfo[dict] = []
    PendingName: Optional[str] = None
    PendingKey = False
    for IndexInfo, LineText in enumerate(Lines):
        Depth, Condition = Conditions[IndexInfo] if IndexInfo < len(Conditions) else (0, '')
        Gates = VersionGates(Condition)
        Offsets = StructOffsets(LineText, Holder, Scale)
        Literal = KStringRe.search(LineText)
        if Literal and 'Serialize' not in Literal.group(1):
            PendingName = Literal.group(1)
        for Match in KBaseCallRe.finditer(LineText):
            Bases.append(Match.group(1))
        GetMatch = KGetReInfo.search(LineText)
        if GetMatch:
            KindNameInfo = GetMatch.group(1)
            Reads.append({'op': 'AR_get_' + KindNameInfo, 'width': KScalarWidth.get(KindNameInfo, 0), 'type': KindNameInfo, 'struct_offset': Offsets[0] if Offsets else None, 'gates': Gates, 'condition': Condition, 'line': IndexInfo + 1})
            continue
        PutMatch = KPutRe.search(LineText)
        if PutMatch:
            KindNameInfo = PutMatch.group(1)
            Entry = {'op': 'AR_put_' + KindNameInfo, 'width': KScalarWidth.get(KindNameInfo, 0), 'type': KindNameInfo, 'struct_offset': Offsets[0] if Offsets else None, 'gates': Gates, 'line': IndexInfo + 1}
            if KindNameInfo == 'su_DBKey':
                if PendingName:
                    Dbkeys.append({'name': PendingName, 'line': IndexInfo + 1})
                    PendingKey = True
                    PendingName = None
            elif PendingKey and Dbkeys:
                Dbkeys[-1]['struct_offset'] = Entry['struct_offset']
                Dbkeys[-1]['width'] = Entry['width']
                Dbkeys[-1]['type'] = KindNameInfo
                PendingKey = False
            Writes.append(Entry)
            continue
        ReadObject = KReadObjectRe.search(LineText)
        if ReadObject:
            Reads.append({'op': 'ReadObject', 'width': None, 'type': ReadObject.group(1), 'struct_offset': Offsets[0] if Offsets else None, 'gates': Gates, 'condition': Condition, 'line': IndexInfo + 1})
            continue
        SlotFive = KSlotFiveRe.search(LineText)
        if SlotFive:
            Reads.append({'op': 'slot5_subrecord', 'width': None, 'type': 'member', 'struct_offset': ParseInt(SlotFive.group(1)), 'gates': Gates, 'condition': Condition, 'line': IndexInfo + 1})
            continue
        if KGlobalReadRe.search(LineText):
            Reads.append({'op': 'operator>>', 'width': None, 'type': 'CString' if KCstringRe.search(LineText) else 'object', 'struct_offset': Offsets[0] if Offsets else None, 'gates': Gates, 'condition': Condition, 'line': IndexInfo + 1})
            continue
        if KReadCountRe.search(LineText):
            Reads.append({'op': 'ReadCount', 'width': None, 'type': 'count', 'struct_offset': None, 'gates': Gates, 'condition': Condition, 'line': IndexInfo + 1})
    return {'function': Record['name'], 'address': '0x' + Record['address'], 'source': Record['source'], 'object_param': Holder, 'pointer_scale': Scale, 'bases': Bases, 'reads': Reads, 'writes': Writes, 'dbkeys': Dbkeys}


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument('dumps', nargs='+')
    ParserInfo.add_argument('--map', required=True)
    ParserInfo.add_argument('--classes', required=True)
    ParserInfo.add_argument('--out', required=True)
    ArgValues = ParserInfo.parse_args()
    DumpData = DumpRecord(ArgValues.dumps)
    SerialMap = JsonData.load(open(ArgValues.map, encoding='utf-8'))
    Classes = [LineText.strip() for LineText in open(ArgValues.classes, encoding='utf-8') if LineText.strip()]
    PayloadInfo: DictInfo[str, dict] = {}
    for NameTextInfo in Classes:
        Entry = SerialMap.get(NameTextInfo)
        if Entry is None:
            PayloadInfo[NameTextInfo] = {'status': 'no_serialize_map_entry'}
            continue
        Record = DumpData.get(Entry['serialize_addr'])
        if Record is None:
            PayloadInfo[NameTextInfo] = {'status': 'serialize_not_dumped', 'serialize_address': '0x' + Entry['serialize_addr']}
            continue
        Extracted = ExtractOps(Record)
        Extracted['status'] = 'ok'
        Chain: ListInfo[dict] = []
        SeenInfo = {Record['address']}
        Frontier = list(Extracted['bases'])
        while Frontier:
            Token = Frontier.pop(0)
            BaseInfo = DumpData.resolve(Token)
            if BaseInfo is None:
                Chain.append({'token': Token, 'status': 'not_dumped'})
                continue
            if BaseInfo['address'] in SeenInfo:
                continue
            SeenInfo.add(BaseInfo['address'])
            InfoInfo = ExtractOps(BaseInfo)
            InfoInfo['token'] = Token
            InfoInfo['status'] = 'ok'
            Chain.append(InfoInfo)
            Frontier.extend(InfoInfo['bases'])
        Extracted['chain'] = Chain
        PayloadInfo[NameTextInfo] = Extracted
    with open(ArgValues.out, 'w', encoding='utf-8') as Handle:
        JsonData.dump(PayloadInfo, Handle, indent=1)
        Handle.write('\n')
    OkInfo = sum((1 for ValueData in PayloadInfo.values() if ValueData.get('status') == 'ok'))
    print('classes=%d extracted=%d missing=%d' % (len(PayloadInfo), OkInfo, len(PayloadInfo) - OkInfo))
    return 0
if __name__ == '__main__':
    raise SystemExit(MainRun())
