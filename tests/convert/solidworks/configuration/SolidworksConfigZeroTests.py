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
import struct as StructLib
import pytest as PytestLib
from convert.adapters.solidworks.configuration.ConfigZero import (
    CONFIG_FIELD_COUNT as Count,
    CONFIG_OPAQUE_BYTES as Bytes,
    CONFIG_OWNER_COUNT as CountA,
    FILLET_ANNOTATION_BYTES as BytesA,
    FILLET_ATOM_LINK_STAMP as Stamp,
    FILLET_ATOM_LINK_STAMP_RELATIVES as Relatives,
    FILLET_ATOM_PARENT_RELATIVE as Relative,
    MO_VERSION as Version,
    PATTERN_ANNOTATION_BYTES as BytesB,
    PER_FEATURE_ATOM_BYTES as BytesC,
    REFERENCE_ATOM_ID as IdInfo,
    REFERENCE_LENGTH as Length,
    REFERENCE_SHA256 as ShaTwoFiveSix,
    REFERENCE_TREE_ID as IdInfoA,
    SINGLE_LENGTH_UNIT_LENGTH as LengthA,
    TWO_VIEW_ANNOTATION_BYTES as BytesD,
    declared_opaque_split as DeclaredOpaqueSplit,
    encode_config0_stream as EncodeConfigZeroStream,
)
from convert.adapters.solidworks.container.Archive import (
    encode_class_definition as EncodeClassDefinition,
)
from convert.adapters.solidworks.programs.configuration.default.Program import (
    ConfigOps,
    FieldOwners,
    ReferenceLength,
    ShiftMapReference,
)
from convert.adapters.solidworks.programs.configuration.box.Program import (
    ConfigOps as BoxConfigOps,
    EncodeProgram as EncodeBoxConfigProgram,
    FieldOwners as BoxFieldOwners,
    ReferenceLength as BoxReferenceLength,
)
from convert.adapters.solidworks.programs.configuration.views.pair.Program import (
    AnnotationOps,
    FieldOwners as AnnotationFieldOwners,
    ReferenceLength as AnnotationReferenceLength,
)
from convert.adapters.solidworks.programs.configuration.fillet.views.Program import (
    AnnotationOps as FilletAnnotationOps,
    FieldOwners as FilletFieldOwners,
    ReferenceLength as FilletReferenceLength,
)
from convert.adapters.solidworks.programs.configuration.pattern.views.Program import (
    AnnotationOps as PatternAnnotationOps,
    FieldOwners as PatternFieldOwners,
    ReferenceLength as PatternReferenceLength,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError

# centralizes shared evidence so every related assertion uses one value
KBytes = 88

# centralizes shared evidence so every related assertion uses one value
KBytesA = 66


# keeps this focused behavior isolated so regressions remain immediately visible
def Atoms(FeatureCount: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        ((IdInfo + Index, IdInfoA + 8 * Index) for Index in range(FeatureCount))
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRFRTSBI() -> None:
    StreamData = EncodeConfigZeroStream()
    assert len(StreamData) == Length == ReferenceLength == 25214
    assert Hashlib.sha256(StreamData).hexdigest() == ShaTwoFiveSix


# keeps this focused behavior isolated so regressions remain immediately visible
def TestERBHEOTO() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in ConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(FieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
            "stringlist",
        } or KindName.startswith(("primitive:", "direct:"))
        assert "opaque" not in KindName
        assert "raw" not in KindName
        SourceCursor += FieldWidth
    assert SourceCursor == Length
    assert len(ConfigOps) == Count == 4341
    assert len(FieldOwners) == CountA == 1085


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/default/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDBCIET() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in BoxConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(BoxFieldOwners)
        assert "opaque" not in KindName.casefold()
        assert "raw" not in KindName.casefold()
        SourceCursor += FieldWidth
    assert SourceCursor == BoxReferenceLength == 25158
    assert len(EncodeBoxConfigProgram()) == BoxReferenceLength
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/box/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTVRPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/views/pair/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTVAMITAC() -> None:
    SingleData = EncodeConfigZeroStream(annotation_view_count=1)
    DoubleData = EncodeConfigZeroStream(annotation_view_count=2)
    AnnotationTag = EncodeClassDefinition("moAnnotationView_c", 1)
    AnnotationStart = DoubleData.index(AnnotationTag)
    assert StructLib.unpack_from("<H", DoubleData, AnnotationStart - 2)[0] == 2
    assert len(DoubleData) - len(SingleData) == BytesD == 260
    assert DoubleData.count(AnnotationTag) == 1
    assert "*Top".encode("utf-16-le") in DoubleData
    assert "*Right".encode("utf-16-le") in DoubleData
    assert AnnotationReferenceLength == 584
    assert len(AnnotationOps) == 113
    assert len(AnnotationFieldOwners) == 45


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTFCITAL() -> None:
    StreamData = EncodeConfigZeroStream(
        part_name="Part1",
        atoms=((101, 34),),
        high_water=(101, 103),
        annotation_view_count=2,
        terminal_parent_tree_id=32,
    )
    AtomTag = EncodeClassDefinition("moAtom_c", 1)
    AtomStart = StreamData.index(AtomTag)
    assert len(StreamData) == 25470
    assert StructLib.unpack_from("<I", StreamData, AtomStart + Relative) == (32,)
    assert all(
        (
            StructLib.unpack_from("<I", StreamData, AtomStart + RelativeOffset)[0]
            == Stamp
            for RelativeOffset in Relatives
        )
    )
    assert BytesA == 258
    assert FilletReferenceLength == 582
    assert len(FilletAnnotationOps) == 113
    assert len(FilletFieldOwners) == 45


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFVPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/fillet/views/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestLPAMITAC() -> None:
    SingleData = EncodeConfigZeroStream(
        part_name="Part1", atoms=((102, 40), (101, 32)), high_water=(102, 105)
    )
    PatternData = EncodeConfigZeroStream(
        part_name="Part1",
        atoms=((102, 40), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="linear_pattern",
    )
    AnnotationTag = EncodeClassDefinition("moAnnotationView_c", 1)
    AnnotationStart = PatternData.index(AnnotationTag)
    assert StructLib.unpack_from("<H", PatternData, AnnotationStart - 2)[0] == 2
    assert len(PatternData) == 25488
    assert len(PatternData) - len(SingleData) == BytesB == 188
    assert PatternReferenceLength == 512
    assert len(PatternAnnotationOps) == 104
    assert len(PatternFieldOwners) == 45


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCPAMMNPM() -> None:
    LinearData = EncodeConfigZeroStream(
        part_name="Part1",
        atoms=((102, 40), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="linear_pattern",
    )
    CircularData = EncodeConfigZeroStream(
        part_name="Part1",
        atoms=((102, 46), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="circular_pattern",
    )
    ExpectedData = EncodeConfigZeroStream(
        part_name="Part1",
        atoms=((102, 46), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="linear_pattern",
    )
    assert CircularData == ExpectedData
    assert len(CircularData) == len(LinearData)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPVPCNEVB() -> None:
    ProgramPath = (
        FilePath(__file__).parents[4]
        / "src/convert/adapters/solidworks/programs/configuration/pattern/views/Program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("ViewCount", (0, 3))
def TestUAVCIR(ViewCount: int) -> None:
    with PytestLib.raises(SldprtFormatError, match="one or two"):
        EncodeConfigZeroStream(annotation_view_count=ViewCount)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("FeatureCount", (1, 2, 3, 4, 5, 6, 7, 8))
def TestEFFAOMA(FeatureCount: int) -> None:
    StreamData = EncodeConfigZeroStream(atoms=Atoms(FeatureCount))
    assert len(StreamData) == Length + KBytes * (FeatureCount - 1)
    assert BytesC == KBytes
    AtomDefinition = b"\xff\xff\x01\x00\x08\x00moAtom_c"
    AtomPos = StreamData.index(AtomDefinition)
    assert StructLib.unpack_from("<II", StreamData, AtomPos - 8) == (
        100 + FeatureCount,
        FeatureCount,
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDAROPAMR() -> None:
    assert ShiftMapReference("classref", 57, 1) == 57
    assert ShiftMapReference("classref", 58, 1) == 59
    assert ShiftMapReference("objectref", 58, 1) == 58
    assert ShiftMapReference("objectref", 59, 1) == 60


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSLUIATOR() -> None:
    DualData = EncodeConfigZeroStream()
    SingleData = EncodeConfigZeroStream(dual_length_units=False)
    assert len(DualData) - len(SingleData) == KBytesA
    assert len(SingleData) == LengthA == 25148


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTFAFTEDS() -> None:
    SplitData = DeclaredOpaqueSplit(atoms=Atoms(3), part_name="TypedPart")
    assert SplitData["typed"] == SplitData["stream_bytes"]
    assert SplitData["accounted"] == SplitData["stream_bytes"]
    assert SplitData["opaque"] == Bytes == 0
    assert SplitData["operations"] == len(ConfigOps)
    assert SplitData["owners"] == len(FieldOwners)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNLMBTBPCU() -> None:
    assert len(EncodeConfigZeroStream(part_name="KitPart")) == Length + 2
    assert len(EncodeConfigZeroStream(part_name="Part1")) == Length - 2


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAICOTIF() -> None:
    FirstData = EncodeConfigZeroStream(atoms=((101, 27),))
    SecondData = EncodeConfigZeroStream(atoms=((102, 35),))
    Changed = [
        Index
        for Index, (FirstByte, SecondByte) in enumerate(zip(FirstData, SecondData))
        if FirstByte != SecondByte
    ]
    assert Changed
    assert len(FirstData) == len(SecondData) == Length


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEARIR() -> None:
    with PytestLib.raises(SldprtFormatError, match="at least one atom record"):
        EncodeConfigZeroStream(atoms=())


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFDGIR() -> None:
    with PytestLib.raises(SldprtFormatError, match="recovered at generation"):
        EncodeConfigZeroStream(generation=14000)
    assert Version == 18000


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCRPIR() -> None:
    with PytestLib.raises(SldprtFormatError, match="raw Config-0 prologue"):
        EncodeConfigZeroStream(part_record_body=b"not allowed")


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    "AtomData", (((-1, 32),), ((101, -1),), ((4294967296, 32),))
)
def TestOORAIAR(AtomData: tuple[tuple[int, int], ...]) -> None:
    with PytestLib.raises(SldprtFormatError, match="fit in 32 bits"):
        EncodeConfigZeroStream(atoms=AtomData)
