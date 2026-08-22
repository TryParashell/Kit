# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass
import struct as Struct
from typing import TypeGuard, cast as Cast
from uuid import UUID as UuidValue
from convert.adapters.solidworks.container.Container import SldprtFormatError

# this binding exists because shared behavior needs one stable value
KDraftingStandards = ("moBS_c", "moISO_c", "moANSI_c")

# this binding exists because shared behavior needs one stable value
KDocGeneration = 18000

# this binding exists because shared behavior needs one stable value
KPartClsid = UuidValue("83a33d30-27c5-11ce-bfd4-00400513bb57").bytes_le

# this binding exists because shared behavior needs one stable value
KAsmClsid = UuidValue("83a33d36-27c5-11ce-bfd4-00400513bb57").bytes_le

# this binding exists because shared behavior needs one stable value
KPreambleFlags = 80

# this binding exists because shared behavior needs one stable value
KPreambleGeneration = 6

# this binding exists because shared behavior needs one stable value
KPreambleFieldEight = 50

# this binding exists because shared behavior needs one stable value
KPreambleFieldOneTwo = 1

# this binding exists because shared behavior needs one stable value
KPreambleFieldOneSix = 1

# this binding exists because shared behavior needs one stable value
KPreambleReserved = bytes(3)

# this binding exists because shared behavior needs one stable value
KPreambleMiddle = bytes(24)

# this binding exists because shared behavior needs one stable value
KPreambleScale = 1.0

# this binding exists because shared behavior needs one stable value
KPreamblePad = 0

# this binding exists because shared behavior needs one stable value
KPreambleTail = (0.0, 0.0, 0.0, 0.0)

# this binding exists because shared behavior needs one stable value
KPreambleTrailerWords = (768, 256, 512, 36090, 16294, 5129, 24576)

# this binding exists because shared behavior needs one stable value
KViewBlockDoubles = 9

# this binding exists because shared behavior needs one stable value
KNewClassToken = 65535

# this binding exists because shared behavior needs one stable value
KBackRefToken = 32768

# this binding exists because shared behavior needs one stable value
KFirstLoadArrayIndex = 1

# this binding exists because shared behavior needs one stable value
KStringMarker = b"\xff\xfe\xff"

# this binding exists because shared behavior needs one stable value
KLongStringUnits = 255

# this binding exists because shared behavior needs one stable value
KDraftingStandardSchema = 1

# this binding exists because shared behavior needs one stable value
KDraftingStandardState = 7

# this binding exists because shared behavior needs one stable value
KLineStyleClass = "moLineStyle_c"

# this binding exists because shared behavior needs one stable value
KLineStyleSchema = 1


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class LineStyle:
    key: str
    display: str
    segments: tuple[float, ...]
    flag: int = 0


# this binding exists because shared behavior needs one stable value
KLineStyles = (
    LineStyle("CONTINUOUS", "Solid", (12.0,)),
    LineStyle("HIDDEN", "Dashed", (0.25, -0.125)),
    LineStyle("PHANTOM", "Phantom", (1.25, -0.25, 0.25, -0.25, 0.25, -0.25)),
    LineStyle("CHAIN", "Chain", (1.25, -0.25, 0.25, -0.25)),
    LineStyle("CENTER", "Center", (3.0, -0.25, 0.25, -0.25)),
    LineStyle("STITCH", "Stitch", (0.0, -0.125)),
    LineStyle("CHAIN_THICK", "Thin/Thick Chain", (1.25, -0.25, 0.25, -0.25), 1),
)

# this binding exists because shared behavior needs one stable value
KLineFontManagerClass = "uiLineFontMgr_c"

# this binding exists because shared behavior needs one stable value
KLineFontManagerSchema = 1

# this binding exists because shared behavior needs one stable value
KLineFontManagerTrailing = 1

# this binding exists because shared behavior needs one stable value
KLineFontConfigClass = "uiLFConfig_c"

# this binding exists because shared behavior needs one stable value
KLineFontConfigSchema = 1

# this binding exists because shared behavior needs one stable value
KLineFontInheritedWidth = -1.0


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class LineFontBinding:
    annotation: str
    font: str
    weight: int = 0
    width: float = KLineFontInheritedWidth
    trailing: int = 0


# this binding exists because shared behavior needs one stable value
KLineFontDims = (
    LineFontBinding("Sketch", "CONTINUOUS"),
    LineFontBinding("Auxilliary", "HIDDEN"),
    LineFontBinding("ChamferDim", "CONTINUOUS"),
    LineFontBinding("LinearDim", "CONTINUOUS"),
    LineFontBinding("LinearDimExt", "CONTINUOUS"),
    LineFontBinding("ArcLenDim", "CONTINUOUS"),
    LineFontBinding("Hidden", "HIDDEN"),
    LineFontBinding("CosmeticThread", "DUMMYTHREAD"),
    LineFontBinding("Explodelines", "PHANTOM"),
    LineFontBinding("Callout", "CONTINUOUS"),
    LineFontBinding("BendDown", "HIDDEN"),
    LineFontBinding("AngOrdinateDim", "CONTINUOUS"),
    LineFontBinding("Visible", "CONTINUOUS", 1),
    LineFontBinding("Detail", "CONTINUOUS"),
    LineFontBinding("Section", "PHANTOM", 2),
    LineFontBinding("Dimensions", "CONTINUOUS"),
    LineFontBinding("BreakLines", "HIDDEN"),
    LineFontBinding("OrdinateDimExt", "CONTINUOUS"),
    LineFontBinding("ChamferDimExt", "CONTINUOUS"),
    LineFontBinding("Crosshatch", "CONTINUOUS"),
)

# this binding exists because shared behavior needs one stable value
KLineFontViews = (
    LineFontBinding("ViewArrow", "PHANTOM", 2),
    LineFontBinding("EmphasizedOutline", "CONTINUOUS", 2, KLineFontInheritedWidth, 2),
    LineFontBinding("AngleDimExt", "CONTINUOUS"),
    LineFontBinding("Adjoining Component", "PHANTOM"),
    LineFontBinding("TanHidden", "HIDDEN"),
    LineFontBinding("ArcLenDimExt", "CONTINUOUS"),
    LineFontBinding("AngleDim", "CONTINUOUS"),
    LineFontBinding("DiameterDim", "CONTINUOUS"),
    LineFontBinding("EnvelopComponent", "PHANTOM"),
    LineFontBinding("DiameterDimExt", "CONTINUOUS"),
    LineFontBinding("OrdinateDim", "CONTINUOUS"),
    LineFontBinding("CalloutExt", "CONTINUOUS"),
    LineFontBinding("AngOrdinateDimExt", "CONTINUOUS"),
    LineFontBinding("TanVisible", "PHANTOM"),
    LineFontBinding("RadialDim", "CONTINUOUS"),
    LineFontBinding("Centerlines", "CENTER"),
    LineFontBinding("DetailBorder", "CONTINUOUS"),
    LineFontBinding("RadialDimExt", "CONTINUOUS"),
    LineFontBinding("SpeedpakVisible", "CONTINUOUS"),
    LineFontBinding("BendUp", "CONTINUOUS"),
)

# this binding exists because shared behavior needs one stable value
KLineFontBindings = KLineFontDims + KLineFontViews

# this binding exists because shared behavior needs one stable value
KUserModelEnvClass = "uiUserModelEnv_c"

# this binding exists because shared behavior needs one stable value
KUserModelEnvSchema = 1

# this binding exists because shared behavior needs one stable value
KSessionHeaderWords = (1, 1, 778, 10, 1520, 10, 0, 0)

# this binding exists because shared behavior needs one stable value
KWindowPlacementFields = (1519, 227, 2, 1, 0, 750, 227, 10, -1)

# this binding exists because shared behavior needs one stable value
KEnvironmentReservedHead = 12

# this binding exists because shared behavior needs one stable value
KEnvironmentCapacity = 96

# this binding exists because shared behavior needs one stable value
KEnvironmentReservedMiddA = 20

# this binding exists because shared behavior needs one stable value
KEnvironmentSentinels = (-1, -1)

# this binding exists because shared behavior needs one stable value
KEnvironmentBuildStamp = 73781

# this binding exists because shared behavior needs one stable value
KEnvironmentTrailingFlag = 0


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ViewRecord:
    rotation: tuple[float, ...]
    translation: tuple[float, float, float]
    scale: float
    gap: int
    centre: tuple[float, float, float]
    height: float
    trailer_flag: int
    trailer_first: int
    trailer_second: int
    trailer_value: float
    name: str
    has_window_placement: bool = False


# this binding exists because shared behavior needs one stable value
KPrimaryView = ViewRecord(
    rotation=(
        0.8844181216774213,
        -0.24036589468392133,
        0.400036026779314,
        1.3877787807814457e-17,
        0.8571673007021341,
        0.5150380749100181,
        -0.4666953889300622,
        -0.4555090068042732,
        0.7580942940502868,
    ),
    translation=(0.0, 0.0, 0.0),
    scale=1.0,
    gap=0,
    centre=(0.03568485564735271, 0.004222922958999075, -0.007028124036209772),
    height=6.180518783629107,
    trailer_flag=0,
    trailer_first=3,
    trailer_second=1,
    trailer_value=-1.0,
    name="",
    has_window_placement=True,
)

# this binding exists because shared behavior needs one stable value
KSecondaryView = ViewRecord(
    rotation=(),
    translation=(0.0, 0.0, 0.0),
    scale=1.0,
    gap=0,
    centre=(0.0, 0.0, 0.0),
    height=1.0,
    trailer_flag=0,
    trailer_first=65535,
    trailer_second=0,
    trailer_value=-1.0,
    name="",
)

# this binding exists because shared behavior needs one stable value
KTertiaryView = ViewRecord(
    rotation=(),
    translation=(0.0, 0.0, 0.0),
    scale=1.0,
    gap=0,
    centre=(0.0, 0.0, 0.0),
    height=1.0,
    trailer_flag=0,
    trailer_first=65535,
    trailer_second=0,
    trailer_value=-1.0,
    name="",
)

# this binding exists because shared behavior needs one stable value
KViewRecords = (KPrimaryView, KSecondaryView, KTertiaryView)

# this binding exists because shared behavior needs one stable value
KBomManagerClass = "moBomInfoMgr_c"

# this binding exists because shared behavior needs one stable value
KBomManagerSchema = 1

# this binding exists because shared behavior needs one stable value
KBomInfoCount = 0

# this binding exists because shared behavior needs one stable value
KManagerTailWords = (1, 38284, 0, 515, 0)

# this binding exists because shared behavior needs one stable value
KJournalClass = "uoJournal_c"

# this binding exists because shared behavior needs one stable value
KJournalSchema = 0

# this binding exists because shared behavior needs one stable value
KJournalAttachment = "Design Journal.doc"

# this binding exists because shared behavior needs one stable value
KJournalSlots = (("", 0), ("", 0), ("", 0))

# this binding exists because shared behavior needs one stable value
KJournalPageHeight = 1000.0

# this binding exists because shared behavior needs one stable value
KJournalHeadFirstFlag = 1

# this binding exists because shared behavior needs one stable value
KJournalHeadSecondFlag = 1

# this binding exists because shared behavior needs one stable value
KJournalHeadThirdFlag = 1

# this binding exists because shared behavior needs one stable value
KJournalHeadSchemaFlags = 1537

# this binding exists because shared behavior needs one stable value
KJournalTailPageUnits = 100

# this binding exists because shared behavior needs one stable value
KJournalTailStyle = 5

# this binding exists because shared behavior needs one stable value
KJournalTailOptionValues = (1, 1, 1, 1, 1, 1, 1, 2, 3, 1)

# this binding exists because shared behavior needs one stable value
KJournalRecordHeadBytes = 47

# this binding exists because shared behavior needs one stable value
KJournalRecordTailBytes = 146

# this binding exists because shared behavior needs one stable value
KOpaqueSpans: tuple[bytes, ...] = ()


# this definition exists because focused behavior needs one stable owner
def EncodeString(TextValue: str) -> bytes:
    Units = TextValue.encode("utf-16-le")
    Count = len(Units) // 2
    if Count < KLongStringUnits:
        return KStringMarker + bytes([Count]) + Units
    return KStringMarker + b"\xff" + Struct.pack("<H", Count) + Units


# this definition exists because primitive archive values share one byte packing interface
class ArchiveValues:
    chunks: list[bytes]

    # this definition exists because focused behavior needs one stable owner
    def RawAction(self, Chunk: bytes) -> None:
        self.chunks.append(Chunk)

    # this definition exists because focused behavior needs one stable owner
    def UEight(self, Value: int) -> None:
        self.chunks.append(Struct.pack("<B", Value))

    # this definition exists because focused behavior needs one stable owner
    def UOneSix(self, Value: int) -> None:
        self.chunks.append(Struct.pack("<H", Value))

    # this definition exists because focused behavior needs one stable owner
    def IOneSix(self, Value: int) -> None:
        self.chunks.append(Struct.pack("<h", Value))

    # this definition exists because focused behavior needs one stable owner
    def IThreeTwo(self, Value: int) -> None:
        self.chunks.append(Struct.pack("<i", Value))

    # this definition exists because focused behavior needs one stable owner
    def UThreeTwo(self, Value: int) -> None:
        self.chunks.append(Struct.pack("<I", Value))

    # this definition exists because focused behavior needs one stable owner
    def FThreeTwo(self, Value: float) -> None:
        self.chunks.append(Struct.pack("<f", Value))

    # this definition exists because focused behavior needs one stable owner
    def FSixFour(self, Value: float) -> None:
        self.chunks.append(Struct.pack("<d", Value))

    # this definition exists because focused behavior needs one stable owner
    def Zeros(self, Count: int) -> None:
        self.chunks.append(bytes(Count))

    # this definition exists because focused behavior needs one stable owner
    def String(self, TextValue: str) -> None:
        self.chunks.append(EncodeString(TextValue))


# this definition exists because archive object state is separate from primitive value packing
class ArchiveWriter(ArchiveValues):
    chunks: list[bytes]
    classes: dict[str, int]
    next_index: int

    # this definition exists because focused behavior needs one stable owner
    def __init__(self) -> None:
        self.chunks = []
        self.classes = {}
        self.next_index = KFirstLoadArrayIndex

    # this definition exists because focused behavior needs one stable owner
    def BeginObject(self, NameValue: str, Schema: int) -> None:
        Index = self.classes.get(NameValue)
        if Index is None:
            Encoded = NameValue.encode("ascii")
            self.u16(KNewClassToken)
            self.u16(Schema)
            self.u16(len(Encoded))
            self.raw(Encoded)
            self.classes[NameValue] = self.next_index
            self.next_index += 1
        else:
            self.u16(KBackRefToken | Index)
        self.next_index += 1

    # this definition exists because focused behavior needs one stable owner
    def Build(self) -> bytes:
        return b"".join(self.chunks)

    begin_object = BeginObject
    build = Build
    f32 = ArchiveValues.FThreeTwo
    f64 = ArchiveValues.FSixFour
    i16 = ArchiveValues.IOneSix
    i32 = ArchiveValues.IThreeTwo
    raw = ArchiveValues.RawAction
    string = ArchiveValues.String
    u16 = ArchiveValues.UOneSix
    u32 = ArchiveValues.UThreeTwo
    u8 = ArchiveValues.UEight
    zeros = ArchiveValues.Zeros


# this definition exists because focused behavior needs one stable owner
def WriteDrafting(Writer: ArchiveWriter, Standard: str) -> None:
    if Standard not in KDraftingStandards:
        raise SldprtFormatError(f"unknown SOLIDWORKS drafting standard {Standard!r}")
    Writer.begin_object(Standard, KDraftingStandardSchema)
    Writer.u32(KDraftingStandardState)


# this definition exists because focused behavior needs one stable owner
def WriteLineStyles(Writer: ArchiveWriter) -> None:
    for Style in KLineStyles:
        Writer.begin_object(KLineStyleClass, KLineStyleSchema)
        Writer.string(Style.key)
        Writer.string(Style.display)
        Writer.u16(len(Style.segments))
        for Segment in Style.segments:
            Writer.f64(Segment)
        Writer.u8(Style.flag)


# this definition exists because focused behavior needs one stable owner
def WriteLineFonts(Writer: ArchiveWriter) -> None:
    Writer.begin_object(KLineFontManagerClass, KLineFontManagerSchema)
    Writer.u16(len(KLineFontBindings))
    for Binding in KLineFontBindings:
        Writer.string(Binding.annotation)
        Writer.begin_object(KLineFontConfigClass, KLineFontConfigSchema)
        Writer.string(Binding.font)
        Writer.i16(Binding.weight)
        Writer.f32(Binding.width)
        Writer.i16(Binding.trailing)
    Writer.u16(KLineFontManagerTrailing)


# this definition exists because focused behavior needs one stable owner
def WriteView(Writer: ArchiveWriter, ViewValue: ViewRecord) -> None:
    Writer.u8(1 if ViewValue.rotation else 0)
    for Value in ViewValue.rotation:
        Writer.f64(Value)
    for Value in ViewValue.translation:
        Writer.f64(Value)
    Writer.f64(ViewValue.scale)
    Writer.u16(ViewValue.gap)
    for Value in ViewValue.centre:
        Writer.f64(Value)
    Writer.f64(ViewValue.height)
    Writer.u8(ViewValue.trailer_flag)
    Writer.u16(ViewValue.trailer_first)
    Writer.u16(ViewValue.trailer_second)
    Writer.f64(ViewValue.trailer_value)
    Writer.string(ViewValue.name)
    if ViewValue.has_window_placement:
        WriteWindow(Writer)


# this definition exists because focused behavior needs one stable owner
def WriteWindow(Writer: ArchiveWriter) -> None:
    Writer.u32(KWindowPlacementFields[0])
    Writer.u32(KWindowPlacementFields[1])
    for ItemData in KWindowPlacementFields[2:-1]:
        Writer.u16(ItemData)
    Writer.i32(KWindowPlacementFields[-1])


# this definition exists because focused behavior needs one stable owner
def WriteTail(Writer: ArchiveWriter) -> None:
    Writer.zeros(KEnvironmentReservedHead)
    Writer.u32(KEnvironmentCapacity)
    Writer.zeros(KEnvironmentReservedMiddA)
    for ItemData in KEnvironmentSentinels:
        Writer.i32(ItemData)
    Writer.u32(KEnvironmentBuildStamp)
    Writer.u8(KEnvironmentTrailingFlag)


# this definition exists because focused behavior needs one stable owner
def WriteUserModel(Writer: ArchiveWriter, UserValue: str) -> None:
    Writer.begin_object(KUserModelEnvClass, KUserModelEnvSchema)
    Writer.string(UserValue)
    for ItemData in KSessionHeaderWords:
        Writer.u16(ItemData)
    for ViewValue in KViewRecords:
        WriteView(Writer, ViewValue)
    WriteTail(Writer)


# this definition exists because focused behavior needs one stable owner
def WriteBomManager(Writer: ArchiveWriter) -> None:
    Writer.begin_object(KBomManagerClass, KBomManagerSchema)
    Writer.u32(KBomInfoCount)
    HeadValue, BuildValue, ReservedValue, FlagValue, TailValue = KManagerTailWords
    Writer.u16(HeadValue)
    Writer.u16(BuildValue)
    Writer.u32(ReservedValue)
    Writer.u16(0)
    Writer.u16(FlagValue)
    Writer.u16(TailValue)


# this definition exists because focused behavior needs one stable owner
def WriteJournalA(Writer: ArchiveWriter) -> None:
    Writer.zeros(10)
    Writer.u16(KJournalHeadFirstFlag)
    Writer.zeros(4)
    Writer.u32(KJournalHeadSecondFlag)
    Writer.zeros(9)
    Writer.u32(KJournalHeadThirdFlag)
    Writer.zeros(3)
    Writer.u16(KJournalHeadSchemaFlags)
    Writer.zeros(9)


# this definition exists because focused behavior needs one stable owner
def WriteJournalB(Writer: ArchiveWriter) -> None:
    Writer.zeros(30)
    Writer.u32(KJournalTailPageUnits)
    Writer.u32(KJournalTailStyle)
    Writer.zeros(8)
    (
        FirstValue,
        SecondValue,
        ThirdValue,
        FourthValue,
        FifthValue,
        SixthValue,
        SeventhValue,
        EighthValue,
        NinthValue,
        TenthValue,
    ) = KJournalTailOptionValues
    Writer.u32(FirstValue)
    Writer.zeros(12)
    Writer.u32(SecondValue)
    Writer.zeros(8)
    Writer.u32(ThirdValue)
    Writer.u32(FourthValue)
    Writer.zeros(4)
    Writer.u32(FifthValue)
    Writer.zeros(6)
    Writer.u32(SixthValue)
    Writer.u32(SeventhValue)
    Writer.zeros(12)
    Writer.u32(EighthValue)
    Writer.zeros(14)
    Writer.u32(NinthValue)
    Writer.u32(TenthValue)
    Writer.zeros(4)


# this definition exists because focused behavior needs one stable owner
def WriteJournal(Writer: ArchiveWriter) -> None:
    Writer.begin_object(KJournalClass, KJournalSchema)
    Writer.string(KJournalAttachment)
    WriteJournalA(Writer)
    for TextValue, Trailing in KJournalSlots:
        Writer.string(TextValue)
        Writer.u16(Trailing)
    WriteJournalB(Writer)
    Writer.f64(KJournalPageHeight)


# this definition exists because focused behavior needs one stable owner
def EncodeBody(*, Standard: str = "moBS_c", UserValue: str = "Kit") -> bytes:
    Writer = ArchiveWriter()
    WriteDrafting(Writer, Standard)
    WriteLineStyles(Writer)
    WriteLineFonts(Writer)
    WriteUserModel(Writer, UserValue)
    WriteBomManager(Writer)
    WriteJournal(Writer)
    return Writer.build()


# this definition exists because focused behavior needs one stable owner
def EncodePreamble(
    *, Clsid: bytes = KPartClsid, ViewValue: tuple[float, ...] | None = None
) -> bytes:
    Chunk = bytearray()
    Chunk += Struct.pack(
        "<IIIII",
        KPreambleFlags,
        KPreambleGeneration,
        KPreambleFieldEight,
        KPreambleFieldOneTwo,
        KPreambleFieldOneSix,
    )
    Chunk += Clsid
    Chunk += KPreambleReserved + bytes([0 if ViewValue is None else 1])
    if ViewValue is not None:
        if len(ViewValue) != KViewBlockDoubles:
            raise SldprtFormatError(
                f"definition view block needs {KViewBlockDoubles} doubles, {len(ViewValue)} were supplied"
            )
        for Value in ViewValue:
            Chunk += Struct.pack("<d", Value)
    Chunk += KPreambleMiddle
    Chunk += Struct.pack("<d", KPreambleScale)
    Chunk += Struct.pack("<H", KPreamblePad)
    for Value in KPreambleTail:
        Chunk += Struct.pack("<d", Value)
    for ItemData in KPreambleTrailerWords:
        Chunk += Struct.pack("<H", ItemData)
    return bytes(Chunk)


# this definition exists because focused behavior needs one stable owner
def EncodeStream(
    *,
    Standard: str = "moBS_c",
    UserValue: str = "Kit",
    AsmValue: bool = False,
    ViewValue: tuple[float, ...] | None = None,
) -> bytes:
    Clsid = KAsmClsid if AsmValue else KPartClsid
    return EncodePreamble(Clsid=Clsid, ViewValue=ViewValue) + EncodeBody(
        Standard=Standard, UserValue=UserValue
    )


# this binding exists because lowercase body calls retain historical keywords
KBodyNames = (("standard", "Standard"), ("user", "UserValue"))

# this binding exists because lowercase stream calls retain historical keywords
KStreamNames = (
    *KBodyNames,
    ("assembly", "AsmValue"),
    ("view", "ViewValue"),
)

# this binding exists because lowercase preamble calls retain historical keywords
KPreambleNames = (("clsid", "Clsid"), ("view", "ViewValue"))


# legacy keyword translation keeps public compatibility explicit
def LegacyArgs(
    KwargValues: dict[str, object], NamePairs: tuple[tuple[str, str], ...]
) -> dict[str, object]:
    NameMap = dict(NamePairs)
    Canonical: dict[str, object] = {}
    for NameValue, ItemValue in KwargValues.items():
        TargetName = NameMap.get(NameValue, NameValue)
        if TargetName in Canonical:
            raise TypeError(f"duplicate definition keyword {TargetName}")
        Canonical[TargetName] = ItemValue
    return Canonical


# view payloads need uniform floating point entries before binary preamble packing begins
def IsViewValues(Value: object) -> TypeGuard[tuple[float, ...] | None]:
    if Value is None:
        return True
    if not isinstance(Value, tuple):
        return False
    ObjectValues = Cast(tuple[object, ...], Value)
    return all(isinstance(Item, float) for Item in ObjectValues)


# the lowercase body encoder accepts historical and canonical keywords
def EncodeBodyOld(**KwargValues: object) -> bytes:
    Values = LegacyArgs(KwargValues, KBodyNames)
    Standard = Values.get("Standard", "moBS_c")
    UserValue = Values.get("UserValue", "Kit")
    if not isinstance(Standard, str) or not isinstance(UserValue, str):
        raise TypeError("EncodeBody() requires string keyword values")
    return EncodeBody(Standard=Standard, UserValue=UserValue)


# the lowercase stream encoder accepts historical and canonical keywords
def EncodeStreamOld(**KwargValues: object) -> bytes:
    Values = LegacyArgs(KwargValues, KStreamNames)
    Standard = Values.get("Standard", "moBS_c")
    UserValue = Values.get("UserValue", "Kit")
    AsmValue = Values.get("AsmValue", False)
    ViewValue = Values.get("ViewValue")
    if (
        not isinstance(Standard, str)
        or not isinstance(UserValue, str)
        or not isinstance(AsmValue, bool)
        or not IsViewValues(ViewValue)
    ):
        raise TypeError("EncodeStream() received an invalid keyword value")
    return EncodeStream(
        Standard=Standard,
        UserValue=UserValue,
        AsmValue=AsmValue,
        ViewValue=ViewValue,
    )


# the lowercase preamble encoder accepts historical and canonical keywords
def EncodePreOld(**KwargValues: object) -> bytes:
    Values = LegacyArgs(KwargValues, KPreambleNames)
    Clsid = Values.get("Clsid", KPartClsid)
    ViewValue = Values.get("ViewValue")
    if not isinstance(Clsid, bytes) or not IsViewValues(ViewValue):
        raise TypeError("EncodePreamble() received an invalid keyword value")
    return EncodePreamble(Clsid=Clsid, ViewValue=ViewValue)


# this binding exists because shared behavior needs one stable value
ASSEMBLY_CLSID = KAsmClsid

# this binding exists because shared behavior needs one stable value
BACK_REFERENCE_TOKEN = KBackRefToken

# this binding exists because shared behavior needs one stable value
BOM_INFO_COUNT = KBomInfoCount

# this binding exists because shared behavior needs one stable value
BOM_MANAGER_CLASS = KBomManagerClass

# this binding exists because shared behavior needs one stable value
BOM_MANAGER_SCHEMA = KBomManagerSchema

# this binding exists because shared behavior needs one stable value
DOCUMENT_GENERATION = KDocGeneration

# this binding exists because shared behavior needs one stable value
DRAFTING_STANDARDS = KDraftingStandards

# this binding exists because shared behavior needs one stable value
DRAFTING_STANDARD_SCHEMA = KDraftingStandardSchema

# this binding exists because shared behavior needs one stable value
DRAFTING_STANDARD_STATE = KDraftingStandardState

# this binding exists because shared behavior needs one stable value
ENVIRONMENT_BUILD_STAMP = KEnvironmentBuildStamp

# this binding exists because shared behavior needs one stable value
ENVIRONMENT_CAPACITY = KEnvironmentCapacity

# this binding exists because shared behavior needs one stable value
ENVIRONMENT_RESERVED_HEAD_BYTES = KEnvironmentReservedHead

# this binding exists because shared behavior needs one stable value
ENVIRONMENT_RESERVED_MIDDLE_BYTES = KEnvironmentReservedMiddA

# this binding exists because shared behavior needs one stable value
ENVIRONMENT_SENTINELS = KEnvironmentSentinels

# this binding exists because shared behavior needs one stable value
ENVIRONMENT_TRAILING_FLAG = KEnvironmentTrailingFlag

# this binding exists because shared behavior needs one stable value
FIRST_LOAD_ARRAY_INDEX = KFirstLoadArrayIndex

# this binding exists because shared behavior needs one stable value
JOURNAL_ATTACHMENT = KJournalAttachment

# this binding exists because shared behavior needs one stable value
JOURNAL_CLASS = KJournalClass

# this binding exists because shared behavior needs one stable value
JOURNAL_HEAD_FIRST_FLAG = KJournalHeadFirstFlag

# this binding exists because shared behavior needs one stable value
JOURNAL_HEAD_SCHEMA_FLAGS = KJournalHeadSchemaFlags

# this binding exists because shared behavior needs one stable value
JOURNAL_HEAD_SECOND_FLAG = KJournalHeadSecondFlag

# this binding exists because shared behavior needs one stable value
JOURNAL_HEAD_THIRD_FLAG = KJournalHeadThirdFlag

# this binding exists because shared behavior needs one stable value
JOURNAL_PAGE_HEIGHT = KJournalPageHeight

# this binding exists because shared behavior needs one stable value
JOURNAL_RECORD_HEAD_BYTES = KJournalRecordHeadBytes

# this binding exists because shared behavior needs one stable value
JOURNAL_RECORD_TAIL_BYTES = KJournalRecordTailBytes

# this binding exists because shared behavior needs one stable value
JOURNAL_SCHEMA = KJournalSchema

# this binding exists because shared behavior needs one stable value
JOURNAL_SLOTS = KJournalSlots

# this binding exists because shared behavior needs one stable value
JOURNAL_TAIL_OPTION_VALUES = KJournalTailOptionValues

# this binding exists because shared behavior needs one stable value
JOURNAL_TAIL_PAGE_UNITS = KJournalTailPageUnits

# this binding exists because shared behavior needs one stable value
JOURNAL_TAIL_STYLE = KJournalTailStyle

# this binding exists because shared behavior needs one stable value
LINE_FONT_BINDINGS = KLineFontBindings

# this binding exists because shared behavior needs one stable value
LINE_FONT_CONFIG_CLASS = KLineFontConfigClass

# this binding exists because shared behavior needs one stable value
LINE_FONT_CONFIG_SCHEMA = KLineFontConfigSchema

# this binding exists because shared behavior needs one stable value
LINE_FONT_INHERITED_WIDTH = KLineFontInheritedWidth

# this binding exists because shared behavior needs one stable value
LINE_FONT_MANAGER_CLASS = KLineFontManagerClass

# this binding exists because shared behavior needs one stable value
LINE_FONT_MANAGER_SCHEMA = KLineFontManagerSchema

# this binding exists because shared behavior needs one stable value
LINE_FONT_MANAGER_TRAILING = KLineFontManagerTrailing

# this binding exists because shared behavior needs one stable value
LINE_STYLES = KLineStyles

# this binding exists because shared behavior needs one stable value
LINE_STYLE_CLASS = KLineStyleClass

# this binding exists because shared behavior needs one stable value
LINE_STYLE_SCHEMA = KLineStyleSchema

# this binding exists because shared behavior needs one stable value
LONG_STRING_UNITS = KLongStringUnits

# this binding exists because shared behavior needs one stable value
MANAGER_TAIL_WORDS = KManagerTailWords

# this binding exists because shared behavior needs one stable value
NEW_CLASS_TOKEN = KNewClassToken

# this binding exists because shared behavior needs one stable value
OPAQUE_SPANS = KOpaqueSpans

# this binding exists because shared behavior needs one stable value
PART_CLSID = KPartClsid

# this binding exists because shared behavior needs one stable value
PREAMBLE_FIELD12 = KPreambleFieldOneTwo

# this binding exists because shared behavior needs one stable value
PREAMBLE_FIELD16 = KPreambleFieldOneSix

# this binding exists because shared behavior needs one stable value
PREAMBLE_FIELD8 = KPreambleFieldEight

# this binding exists because shared behavior needs one stable value
PREAMBLE_FLAGS = KPreambleFlags

# this binding exists because shared behavior needs one stable value
PREAMBLE_GENERATION = KPreambleGeneration

# this binding exists because shared behavior needs one stable value
PREAMBLE_MIDDLE = KPreambleMiddle

# this binding exists because shared behavior needs one stable value
PREAMBLE_PAD = KPreamblePad

# this binding exists because shared behavior needs one stable value
PREAMBLE_RESERVED = KPreambleReserved

# this binding exists because shared behavior needs one stable value
PREAMBLE_SCALE = KPreambleScale

# this binding exists because shared behavior needs one stable value
PREAMBLE_TAIL = KPreambleTail

# this binding exists because shared behavior needs one stable value
PREAMBLE_TRAILER_WORDS = KPreambleTrailerWords

# this binding exists because shared behavior needs one stable value
SESSION_HEADER_WORDS = KSessionHeaderWords

# this binding exists because shared behavior needs one stable value
STRING_MARKER = KStringMarker

# this binding exists because shared behavior needs one stable value
USER_MODEL_ENV_CLASS = KUserModelEnvClass

# this binding exists because shared behavior needs one stable value
USER_MODEL_ENV_SCHEMA = KUserModelEnvSchema

# this binding exists because shared behavior needs one stable value
UUID = UuidValue

# this binding exists because shared behavior needs one stable value
VIEW_BLOCK_DOUBLES = KViewBlockDoubles

# this binding exists because shared behavior needs one stable value
VIEW_RECORDS = KViewRecords

# this binding exists because shared behavior needs one stable value
WINDOW_PLACEMENT_FIELDS = KWindowPlacementFields

# this binding exists because shared behavior needs one stable value
annotations = Annotations

# this binding exists because shared behavior needs one stable value
dataclass = Dataclass

# this binding exists because shared behavior needs one stable value
encode_body = EncodeBodyOld

# this binding exists because shared behavior needs one stable value
encode_definition_stream = EncodeStreamOld

# this binding exists because shared behavior needs one stable value
encode_preamble = EncodePreOld

# this binding exists because shared behavior needs one stable value
encode_string = EncodeString

# this binding exists because shared behavior needs one stable value
struct = Struct

# this binding exists because shared behavior needs one stable value
write_bom_manager = WriteBomManager

# this binding exists because shared behavior needs one stable value
write_drafting_standard = WriteDrafting

# this binding exists because shared behavior needs one stable value
write_environment_tail = WriteTail

# this binding exists because shared behavior needs one stable value
write_journal = WriteJournal

# this binding exists because shared behavior needs one stable value
write_journal_head = WriteJournalA

# this binding exists because shared behavior needs one stable value
write_journal_tail = WriteJournalB

# this binding exists because shared behavior needs one stable value
write_line_fonts = WriteLineFonts

# this binding exists because shared behavior needs one stable value
write_line_styles = WriteLineStyles

# this binding exists because shared behavior needs one stable value
write_user_model_env = WriteUserModel

# this binding exists because shared behavior needs one stable value
write_view = WriteView

# this binding exists because shared behavior needs one stable value
write_window_placement = WriteWindow
