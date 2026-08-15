# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import replace as Replace
from io import BytesIO as BytesIo, StringIO as StringIo
from pathlib import Path as FilePath
from typing import Generic
from typing import TypeVar
import pytest as Pytest
from convert import convert as Convert, open_document as OpenDoc
from convert.adapters import (
    AdapterInfo,
    AdapterNotFoundError,
    AdapterRegistry,
    AdapterRegistryError,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)
from convert.adapters.json import JsonAdapter
from interchange import CadDocument, Capability
from tests.interchange.document.DocumentTests import document as DocValue

# nonseekable test streams preserve their concrete text or binary payload type
KStreamData = TypeVar("KStreamData", str, bytes)


# this definition exists because focused behavior needs one stable owner
class FirstAdapter(JsonAdapter):

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(self) -> AdapterInfo:
        return AdapterInfo("first", "First", "1", (".first",), ("second",))

    locals()["info"] = InfoAction


# this definition exists because focused behavior needs one stable owner
class SecondAdapter(JsonAdapter):

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(self) -> AdapterInfo:
        return AdapterInfo("second", "Second", "1", (".second",))

    locals()["info"] = InfoAction


# this definition exists because focused behavior needs one stable owner
class Duplicate(JsonAdapter):

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(self) -> AdapterInfo:
        return AdapterInfo("first", "Duplicate", "1", (".first",), ("orphan",))

    locals()["info"] = InfoAction


# this definition exists because focused behavior needs one stable owner
class SwapAdapter(JsonAdapter):

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(self) -> AdapterInfo:
        return AdapterInfo(
            "first", "Replacement", "2", (".replacement",), ("replacement",)
        )

    locals()["info"] = InfoAction


# this definition exists because focused behavior needs one stable owner
class ReaderOnly:
    InfoValue: AdapterInfo
    Delegate: JsonAdapter

    # this definition exists because focused behavior needs one stable owner
    def __init__(self, InfoValue: AdapterInfo) -> None:
        self.InfoValue = InfoValue
        self.Delegate = JsonAdapter()

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(self) -> AdapterInfo:
        return self.InfoValue

    # this definition exists because focused behavior needs one stable owner
    def Probe(self, SourceValue: Source) -> ProbeResult:
        return self.Delegate.probe(SourceValue)

    # this definition exists because focused behavior needs one stable owner
    def ReadAction(
        self, SourceValue: Source, Options: ReadOptions | None = None
    ) -> CadDocument:
        return self.Delegate.read(SourceValue, Options)

    info = InfoAction
    probe = Probe
    read = ReadAction


# this definition exists because focused behavior needs one stable owner
class WriterOnly:
    InfoValue: AdapterInfo
    Delegate: JsonAdapter

    # this definition exists because focused behavior needs one stable owner
    def __init__(self, InfoValue: AdapterInfo) -> None:
        self.InfoValue = InfoValue
        self.Delegate = JsonAdapter()

    # this definition exists because focused behavior needs one stable owner
    @property
    def InfoAction(self) -> AdapterInfo:
        return self.InfoValue

    # this definition exists because focused behavior needs one stable owner
    def Supports(self, DocValue: CadDocument, Target: Destination) -> bool:
        return self.Delegate.supports(DocValue, Target)

    # this definition exists because focused behavior needs one stable owner
    def Write(
        self,
        DocValue: CadDocument,
        Target: Destination,
        Options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.Delegate.write(DocValue, Target, Options)

    info = InfoAction
    supports = Supports
    write = Write


# this definition exists because focused behavior needs one stable owner
class PartialBytesIo:

    # this definition exists because focused behavior needs one stable owner
    def Write(self, Value: bytes) -> int:
        return len(Value[:-1])

    write = Write


# this definition exists because focused behavior needs one stable owner
class PartialStringIo:

    # this definition exists because focused behavior needs one stable owner
    def Write(self, Value: str) -> int:
        return len(Value[:-1])

    write = Write


# this definition exists because focused behavior needs one stable owner
class NonSeekable(Generic[KStreamData]):
    StreamValue: KStreamData
    IsConsumed: bool

    # this definition exists because focused behavior needs one stable owner
    def __init__(self, Value: KStreamData) -> None:
        self.StreamValue = Value
        self.IsConsumed = False

    # this definition exists because focused behavior needs one stable owner
    def ReadAction(self, SizeValue: int | None = -1) -> KStreamData:
        if self.IsConsumed:
            return self.StreamValue[:0]
        self.IsConsumed = True
        return self.StreamValue

    read = ReadAction


# this definition exists because focused behavior needs one stable owner
def TestAdapter() -> None:
    assert JsonAdapter().info.capabilities == frozenset(Capability)


# this definition exists because focused behavior needs one stable owner
def TestRegistryA(TmpPath: FilePath) -> None:
    Adapter = JsonAdapter()
    Registry = AdapterRegistry()
    Registry.register(Adapter)
    Output = TmpPath / "model.json"
    Written = Registry.write(DocValue(), Output)
    Restored = Registry.read(Output)
    assert Written.path == Output.resolve()
    assert Restored == DocValue()
    assert Registry.format_ids() == ("interchange.json",)


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("StreamType", (BytesIo, StringIo))
def TestStreamUtf(StreamType: type[BytesIo] | type[StringIo]) -> None:
    Adapter = JsonAdapter()
    Value = DocValue()
    Value = Replace(Value, source=Replace(Value.source, path="mémoire"))
    Stream = StreamType()
    Result = Adapter.write(Value, Stream)
    Serialized = Stream.getvalue()
    TextValue = (
        Serialized.decode("utf-8") if isinstance(Serialized, bytes) else Serialized
    )
    assert "mémoire" in TextValue
    assert Result.bytes_written == len(TextValue.encode("utf-8"))
    InputStream = (
        BytesIo(Serialized) if isinstance(Serialized, bytes) else StringIo(Serialized)
    )
    assert Adapter.read(InputStream) == Value


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("StreamType", (PartialBytesIo, PartialStringIo))
def TestStream(
    StreamType: type[PartialBytesIo] | type[PartialStringIo],
) -> None:
    with Pytest.raises(OSError, match="short JSON write"):
        JsonAdapter().write(DocValue(), StreamType())


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("StreamType", (BytesIo, StringIo))
def TestProbeStream(StreamType: type[BytesIo] | type[StringIo]) -> None:
    Serialized = DocValue().to_json() + "\n"
    Serialized = "prefix:" + Serialized
    Stream = (
        BytesIo(Serialized.encode("utf-8"))
        if StreamType is BytesIo
        else StringIo(Serialized)
    )
    Stream.seek(7)
    assert JsonAdapter().probe(Stream).confidence == 1.0
    assert Stream.tell() == 7


# this definition exists because focused behavior needs one stable owner
def TestPublicSdk() -> None:
    Value = DocValue()
    Source = StringIo(Value.to_json() + "\n")
    assert OpenDoc(Source) == Value
    Source.seek(0)
    Target = StringIo()
    Result = Convert(Source, Target, destination_format="interchange.json")
    assert Result.destination_format == "interchange.json"
    assert JsonAdapter().read(StringIo(Target.getvalue())) == Value


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("Binary", (False, True))
def TestPublicSdkA(Binary: bool) -> None:
    Value = DocValue()
    Serialized = Value.to_json() + "\n"
    SourceData: NonSeekable[bytes] | NonSeekable[str]
    ConvertData: NonSeekable[bytes] | NonSeekable[str]
    if Binary:
        SourceData = NonSeekable(Serialized.encode("utf-8"))
        ConvertData = NonSeekable(Serialized.encode("utf-8"))
    else:
        SourceData = NonSeekable(Serialized)
        ConvertData = NonSeekable(Serialized)
    assert OpenDoc(SourceData) == Value
    Target = StringIo()
    Result = Convert(ConvertData, Target, destination_format="interchange.json")
    assert Result.document == Value
    assert JsonAdapter().read(StringIo(Target.getvalue())) == Value


# this definition exists because focused behavior needs one stable owner
def TestExplicitNon(TmpPath: FilePath) -> None:
    Source = StringIo(DocValue().to_json())
    with Pytest.raises(AdapterNotFoundError, match="does not support"):
        Convert(
            Source,
            TmpPath / "contradiction.SLDPRT",
            destination_format="interchange.json",
        )


# this definition exists because focused behavior needs one stable owner
def TestRegistry() -> None:
    Registry = AdapterRegistry()
    First = FirstAdapter()
    Registry.register(First)
    with Pytest.raises(AdapterRegistryError, match="already an alias"):
        Registry.register(SecondAdapter())
    assert Registry.reader("second") is First
    assert Registry.writer("second") is First
    assert Registry.format_ids() == ("first", "second")


# this definition exists because focused behavior needs one stable owner
def TestFailedDoes() -> None:
    Registry = AdapterRegistry()
    First = FirstAdapter()
    Registry.register(First)
    with Pytest.raises(
        AdapterRegistryError, match="metadata differ|already registered"
    ):
        Registry.register(Duplicate())
    with Pytest.raises(AdapterNotFoundError):
        Registry.reader("orphan")
    assert Registry.reader("first") is First
    assert Registry.format_ids() == ("first", "second")


# this definition exists because focused behavior needs one stable owner
def TestReplacement() -> None:
    Registry = AdapterRegistry()
    Registry.register(FirstAdapter())
    Replacement = SwapAdapter()
    Registry.register(Replacement, replace=True)
    with Pytest.raises(AdapterNotFoundError):
        Registry.reader("second")
    assert Registry.reader("replacement") is Replacement
    assert Registry.writer("replacement") is Replacement
    assert Registry.format_ids() == ("first", "replacement")


# this definition exists because focused behavior needs one stable owner
def TestSplitReadeA() -> None:
    InfoValue = AdapterInfo("split", "Split", "1", (".split",), ("split.alias",))
    Reader = ReaderOnly(InfoValue)
    Writer = WriterOnly(InfoValue)
    Registry = AdapterRegistry()
    Registry.register(Reader)
    Registry.register(Writer)
    assert Registry.reader("split.alias") is Reader
    assert Registry.writer("split.alias") is Writer


# this definition exists because focused behavior needs one stable owner
def TestSplitReader() -> None:
    ReaderInfo = AdapterInfo("split", "Split", "1", (".read",), ("read.alias",))
    WriterInfo = AdapterInfo("split", "Split", "1", (".write",), ("write.alias",))
    Reader = ReaderOnly(ReaderInfo)
    Registry = AdapterRegistry()
    Registry.register(Reader)
    with Pytest.raises(AdapterRegistryError, match="metadata differ"):
        Registry.register(WriterOnly(WriterInfo))
    with Pytest.raises(AdapterNotFoundError):
        Registry.writer("split")
    with Pytest.raises(AdapterNotFoundError):
        Registry.reader("write.alias")
    assert Registry.reader("read.alias") is Reader
    assert Registry.format_ids() == ("read.alias", "split")


# this binding exists because shared behavior needs one stable value
globals()["BytesIO"] = BytesIo

# this binding exists because shared behavior needs one stable value
globals()["DuplicateAdapter"] = Duplicate

# this binding exists because shared behavior needs one stable value
globals()["NonSeekableStream"] = NonSeekable

# this binding exists because shared behavior needs one stable value
globals()["PartialBytesIO"] = PartialBytesIo

# this binding exists because shared behavior needs one stable value
globals()["PartialStringIO"] = PartialStringIo

# this binding exists because shared behavior needs one stable value
globals()["ReplacementAdapter"] = SwapAdapter

# this binding exists because shared behavior needs one stable value
globals()["StringIO"] = StringIo

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["convert"] = Convert

# this binding exists because shared behavior needs one stable value
globals()["document"] = DocValue

# this binding exists because shared behavior needs one stable value
globals()["open_document"] = OpenDoc

# this binding exists because shared behavior needs one stable value
globals()["pytest"] = Pytest

# this binding exists because shared behavior needs one stable value
globals()["replace"] = Replace
