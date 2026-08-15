# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
from pathlib import Path as FilePath
import pytest as PytestLib
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.container.Definition import (
    ASSEMBLY_CLSID as Clsid,
    DOCUMENT_GENERATION as Generation,
    DRAFTING_STANDARDS as Standards,
    LINE_FONT_BINDINGS as Bindings,
    LINE_STYLES as Styles,
    OPAQUE_SPANS as Spans,
    PART_CLSID as ClsidA,
    encode_body as EncodeBody,
    encode_definition_stream as EncodeDefinitionStream,
    encode_string as EncodeString,
)

# centralizes shared evidence so every related assertion uses one value
KBytesB = 3618

# centralizes shared evidence so every related assertion uses one value
KDigestA = "f5b20e1c8dbe0efece6a9d07f0806a0c8d051509a8c38431024e61986d887a9e"

# centralizes shared evidence so every related assertion uses one value
KUserInfo = "odin"

# centralizes shared evidence so every related assertion uses one value
KBytesC = 3618

# centralizes shared evidence so every related assertion uses one value
KBytesD = 0

# centralizes shared evidence so every related assertion uses one value
KSpans = 0

# centralizes shared evidence so every related assertion uses one value
KBytesA = 3736

# centralizes shared evidence so every related assertion uses one value
KDigest = "7479a6640fa3647a4801f41bc2bd1cc4a08c845620fc0a4412dd2aa407aadf19"

# centralizes shared evidence so every related assertion uses one value
KOffset = 20

# centralizes shared evidence so every related assertion uses one value
KBytes = 16

# centralizes shared evidence so every related assertion uses one value
KBytesE = 72

# centralizes shared evidence so every related assertion uses one value
KViewInfo = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBIBITTRB():
    Encoded = EncodeBody(standard=Standards[0], user=KUserInfo)
    assert len(Encoded) == KBytesB
    assert Hashlib.sha256(Encoded).hexdigest() == KDigestA


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDBCTCB():
    Opaque = sum((len(SpanInfo) for SpanInfo in Spans))
    assert len(Spans) == KSpans
    assert Opaque == KBytesD
    assert KBytesC + Opaque == KBytesB
    Encoded = EncodeBody(standard=Standards[0], user=KUserInfo)
    assert len(Encoded) - Opaque == KBytesC


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDWCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/container/Definition.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "OPAQUE_SPANS = (" not in SourceText


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTHTRS():
    assert len(Styles) == 7
    assert len(Bindings) == 40
    assert Generation == 18000
    assert Standards == ("moBS_c", "moISO_c", "moANSI_c")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDSMTRD():
    Stream = EncodeDefinitionStream()
    assert len(Stream) == KBytesA
    assert Hashlib.sha256(Stream).hexdigest() == KDigest


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    ("Standard", "Expected"), (("moBS_c", 3736), ("moISO_c", 3737), ("moANSI_c", 3738))
)
def TestEDSEIRL(Standard, Expected):
    Stream = EncodeDefinitionStream(standard=Standard)
    assert len(Stream) == Expected
    assert Stream.count(Standard.encode("ascii")) == 1


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    ("UserInfo", "Expected"),
    (
        ("Kit", 3736),
        ("odin", 3738),
        ("Parashell", 3748),
        ("abcdefghijklmnopqrstuvwxyz1", 3784),
    ),
)
def NamedTUNLMTSBTB(UserInfo, Expected):
    Stream = EncodeDefinitionStream(user=UserInfo)
    assert len(Stream) == Expected
    assert Stream.count(EncodeString(UserInfo)) == 1


# keeps this focused behavior isolated so regressions remain immediately visible
def TestASTAC():
    PartDoc = EncodeDefinitionStream()
    Assembly = EncodeDefinitionStream(assembly=True)
    assert PartDoc[KOffset : KOffset + KBytes] == ClsidA
    assert Assembly[KOffset : KOffset + KBytes] == Clsid
    assert len(Assembly) == KBytesA


# keeps this focused behavior isolated so regressions remain immediately visible
def TestVBASTB():
    Stream = EncodeDefinitionStream(view=KViewInfo)
    assert len(Stream) == KBytesA + KBytesE
    assert Stream[KOffset + KBytes + 3] == 1


# keeps this focused behavior isolated so regressions remain immediately visible
def TestUDSIR():
    with PytestLib.raises(SldprtFormatError):
        EncodeDefinitionStream(standard="moDIN_c")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSVBIR():
    with PytestLib.raises(SldprtFormatError):
        EncodeDefinitionStream(view=(1.0, 0.0, 0.0))
