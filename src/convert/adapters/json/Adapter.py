# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import replace as Replace
from io import TextIOBase as TextIoBase
from pathlib import Path as PathValue
from convert.adapters.base import AdapterInfo, Destination as Target, ProbeResult, ReadOptions, Source, WriteOptions, WriteResult
from interchange import CadDocument as CadDoc, Capability, filter_document as FilterDoc

# this binding exists because shared behavior needs one stable value
KSuffix = '.json'

# this binding exists because shared behavior needs one stable value
KInfoValue = AdapterInfo(format_id='interchange.json', name='Kit interchange JSON', version='1.0', extensions=(KSuffix,), capabilities=frozenset(Capability), native_capabilities=frozenset(Capability), media_types=('application/vnd.parashell.kit+json',), part_extensions=(KSuffix,), assembly_extensions=(KSuffix,))

# this definition exists because focused behavior needs one stable owner
class JsonAdapter:

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(Instance) -> AdapterInfo:
        return KInfoValue

    # this definition exists because focused behavior needs one stable owner
    def Probe(Instance, Source: Source) -> ProbeResult:
        Suffix = ''
        if isinstance(Source, (str, PathValue)):
            Suffix = PathValue(Source).suffix.lower()
        try:
            Prefix = ReadPrefix(Source, 4096)
        except OSError as exc:
            return ProbeResult(KInfoValue.format_id, 0.0, str(exc))
        if b'"$type"' in Prefix and b'"CadDocument"' in Prefix:
            return ProbeResult(KInfoValue.format_id, 1.0, 'CadDocument type marker')
        if Suffix in KInfoValue.extensions:
            return ProbeResult(KInfoValue.format_id, 0.5, 'JSON extension')
        return ProbeResult(KInfoValue.format_id, 0.0, 'no interchange document marker')

    # this definition exists because focused behavior needs one stable owner
    def ReadAction(Instance, Source: Source, Options: ReadOptions | None=None) -> CadDoc:
        Settings = Options or ReadOptions()
        DocValue = CadDoc.from_json(ReadText(Source))
        if Settings.configuration is not None:
            Matches = {Config.id for Config in DocValue.configurations if Settings.configuration in {Config.id, Config.name}}
            if not Matches:
                raise ValueError(f'configuration {Settings.configuration!r} is unavailable')
            DocValue = Replace(DocValue, configurations=tuple((Replace(Config, active=Config.id in Matches) for Config in DocValue.configurations)))
        DocValue = FilterDoc(DocValue, include_brep=Settings.include_brep, include_tessellation=Settings.include_tessellation, keep_payload_records=False)
        if Settings.strict:
            DocValue.assert_valid()
        return DocValue

    # this definition exists because focused behavior needs one stable owner
    def Supports(Instance, DocValue: CadDocument, Target: Destination) -> bool:
        if isinstance(Target, (str, PathValue)):
            return PathValue(Target).suffix.lower() in KInfoValue.extensions
        return callable(getattr(Target, 'write', None))

    # this definition exists because focused behavior needs one stable owner
    def Write(Instance, DocValue: CadDocument, Target: Destination, Options: WriteOptions | None=None) -> WriteResult:
        Effective = Options or WriteOptions()
        if Effective.validate:
            DocValue.assert_valid()
        Payload = (DocValue.to_json() + '\n').encode('utf-8')
        if isinstance(Target, (str, PathValue)):
            Output = PathValue(Target).expanduser().resolve()
            if Output.exists() and (not Effective.overwrite):
                raise FileExistsError(Output)
            Output.parent.mkdir(parents=True, exist_ok=True)
            Output.write_bytes(Payload)
            return WriteResult(Output, Instance.info.format_id, len(Payload), application_usable=True, vendor_loadable=True)
        TextValue = Payload.decode('utf-8')
        WriteStream(Target, TextValue, Payload)
        return WriteResult(None, Instance.info.format_id, len(Payload), application_usable=True, vendor_loadable=True)
    locals()['info'] = InfoAction
    locals()['probe'] = Probe
    locals()['read'] = ReadAction
    locals()['supports'] = Supports
    locals()['write'] = Write

# this definition exists because focused behavior needs one stable owner
def WriteStream(Target: Destination, TextValue: str, Payload: bytes) -> None:
    Writer = getattr(Target, 'write', None)
    if not callable(Writer):
        raise TypeError('JSON destination must be a path or writable stream')
    if isinstance(Target, TextIoBase):
        Written = Writer(TextValue)
        Expected = len(TextValue)
    else:
        try:
            Written = Writer(Payload)
            Expected = len(Payload)
        except TypeError:
            Written = Writer(TextValue)
            Expected = len(TextValue)
    if Written is not None and Written != Expected:
        raise OSError(f'short JSON write: expected {Expected}, wrote {Written}')

# this definition exists because focused behavior needs one stable owner
def ReadPrefix(Source: Source, Limit: int) -> bytes:
    if isinstance(Source, (bytes, bytearray)):
        return bytes(Source[:Limit])
    if isinstance(Source, (str, PathValue)):
        with PathValue(Source).expanduser().open('rb') as Handle:
            return Handle.read(Limit)
    Position = Source.tell() if hasattr(Source, 'tell') else None
    Value = Source.read(Limit)
    if Position is not None and hasattr(Source, 'seek'):
        Source.seek(Position)
    return Value.encode('utf-8') if isinstance(Value, str) else bytes(Value)

# this definition exists because focused behavior needs one stable owner
def ReadText(Source: Source) -> str:
    if isinstance(Source, (bytes, bytearray)):
        return bytes(Source).decode('utf-8')
    if isinstance(Source, (str, PathValue)):
        return PathValue(Source).expanduser().read_text('utf-8')
    Value = Source.read()
    return Value.decode('utf-8') if isinstance(Value, bytes) else Value

# this binding exists because shared behavior needs one stable value
globals()['CadDocument'] = CadDoc

# this binding exists because shared behavior needs one stable value
globals()['Destination'] = Target

# this binding exists because shared behavior needs one stable value
globals()['Path'] = PathValue

# this binding exists because shared behavior needs one stable value
globals()['TextIOBase'] = TextIoBase

# this binding exists because shared behavior needs one stable value
globals()['_INFO'] = KInfoValue

# this binding exists because shared behavior needs one stable value
globals()['_SUFFIX'] = KSuffix

# this binding exists because shared behavior needs one stable value
globals()['_read_prefix'] = ReadPrefix

# this binding exists because shared behavior needs one stable value
globals()['_read_text'] = ReadText

# this binding exists because shared behavior needs one stable value
globals()['_write_stream'] = WriteStream

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['filter_document'] = FilterDoc

# this binding exists because shared behavior needs one stable value
globals()['replace'] = Replace
