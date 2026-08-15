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
    locals().setdefault("__annotations__", {})
    __annotations__["key"] = "str"
    __annotations__["display"] = "str"
    __annotations__["segments"] = "tuple[float, ...]"
    __annotations__["flag"] = "int"
    locals()["flag"] = 0


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
    locals().setdefault("__annotations__", {})
    __annotations__["annotation"] = "str"
    __annotations__["font"] = "str"
    __annotations__["weight"] = "int"
    locals()["weight"] = 0
    __annotations__["width"] = "float"
    locals()["width"] = KLineFontInheritedWidth
    __annotations__["trailing"] = "int"
    locals()["trailing"] = 0


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
    locals().setdefault("__annotations__", {})
    __annotations__["rotation"] = "tuple[float, ...]"
    __annotations__["translation"] = "tuple[float, float, float]"
    __annotations__["scale"] = "float"
    __annotations__["gap"] = "int"
    __annotations__["centre"] = "tuple[float, float, float]"
    __annotations__["height"] = "float"
    __annotations__["trailer_flag"] = "int"
    __annotations__["trailer_first"] = "int"
    __annotations__["trailer_second"] = "int"
    __annotations__["trailer_value"] = "float"
    __annotations__["name"] = "str"
    __annotations__["has_window_placement"] = "bool"
    locals()["has_window_placement"] = False


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

    # this definition exists because focused behavior needs one stable owner
    def RawAction(Instance, Chunk: bytes) -> None:
        Instance.chunks.append(Chunk)

    # this definition exists because focused behavior needs one stable owner
    def UEight(Instance, Value: int) -> None:
        Instance.chunks.append(Struct.pack("<B", Value))

    # this definition exists because focused behavior needs one stable owner
    def UOneSix(Instance, Value: int) -> None:
        Instance.chunks.append(Struct.pack("<H", Value))

    # this definition exists because focused behavior needs one stable owner
    def IOneSix(Instance, Value: int) -> None:
        Instance.chunks.append(Struct.pack("<h", Value))

    # this definition exists because focused behavior needs one stable owner
    def IThreeTwo(Instance, Value: int) -> None:
        Instance.chunks.append(Struct.pack("<i", Value))

    # this definition exists because focused behavior needs one stable owner
    def UThreeTwo(Instance, Value: int) -> None:
        Instance.chunks.append(Struct.pack("<I", Value))

    # this definition exists because focused behavior needs one stable owner
    def FThreeTwo(Instance, Value: float) -> None:
        Instance.chunks.append(Struct.pack("<f", Value))

    # this definition exists because focused behavior needs one stable owner
    def FSixFour(Instance, Value: float) -> None:
        Instance.chunks.append(Struct.pack("<d", Value))

    # this definition exists because focused behavior needs one stable owner
    def Zeros(Instance, Count: int) -> None:
        Instance.chunks.append(bytes(Count))

    # this definition exists because focused behavior needs one stable owner
    def String(Instance, TextValue: str) -> None:
        Instance.chunks.append(EncodeString(TextValue))


# this definition exists because archive object state is separate from primitive value packing
class ArchiveWriter(ArchiveValues):
    KSlots = ("chunks", "classes", "next_index")

    # this definition exists because focused behavior needs one stable owner
    def InitAction(Instance) -> None:
        setattr(Instance, "chunks", [])
        setattr(Instance, "classes", {})
        setattr(Instance, "next_index", KFirstLoadArrayIndex)

    # this definition exists because focused behavior needs one stable owner
    def BeginObject(Instance, NameValue: str, Schema: int) -> None:
        Index = Instance.classes.get(NameValue)
        if Index is None:
            Encoded = NameValue.encode("ascii")
            Instance.u16(KNewClassToken)
            Instance.u16(Schema)
            Instance.u16(len(Encoded))
            Instance.raw(Encoded)
            Instance.classes[NameValue] = Instance.next_index
            setattr(Instance, "next_index", Instance.next_index + 1)
        else:
            Instance.u16(KBackRefToken | Index)
        setattr(Instance, "next_index", Instance.next_index + 1)

    # this definition exists because focused behavior needs one stable owner
    def Build(Instance) -> bytes:
        return b"".join(Instance.chunks)


# this assignment preserves the established constructor contract
ArchiveWriter.__init__ = ArchiveWriter.InitAction

setattr(ArchiveWriter, "begin_object", ArchiveWriter.BeginObject)

setattr(ArchiveWriter, "build", ArchiveWriter.Build)

setattr(ArchiveWriter, "f32", ArchiveWriter.FThreeTwo)

setattr(ArchiveWriter, "f64", ArchiveWriter.FSixFour)

setattr(ArchiveWriter, "i16", ArchiveWriter.IOneSix)

setattr(ArchiveWriter, "i32", ArchiveWriter.IThreeTwo)

setattr(ArchiveWriter, "raw", ArchiveWriter.RawAction)

setattr(ArchiveWriter, "string", ArchiveWriter.String)

setattr(ArchiveWriter, "u16", ArchiveWriter.UOneSix)

setattr(ArchiveWriter, "u32", ArchiveWriter.UThreeTwo)

setattr(ArchiveWriter, "u8", ArchiveWriter.UEight)

setattr(ArchiveWriter, "zeros", ArchiveWriter.Zeros)


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


# the lowercase body encoder accepts historical and canonical keywords
def EncodeBodyOld(**KwargValues: object) -> bytes:
    return EncodeBody(**LegacyArgs(KwargValues, KBodyNames))


# the lowercase stream encoder accepts historical and canonical keywords
def EncodeStreamOld(**KwargValues: object) -> bytes:
    return EncodeStream(**LegacyArgs(KwargValues, KStreamNames))


# the lowercase preamble encoder accepts historical and canonical keywords
def EncodePreOld(**KwargValues: object) -> bytes:
    return EncodePreamble(**LegacyArgs(KwargValues, KPreambleNames))


# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_CLSID"] = KAsmClsid

# this binding exists because shared behavior needs one stable value
globals()["BACK_REFERENCE_TOKEN"] = KBackRefToken

# this binding exists because shared behavior needs one stable value
globals()["BOM_INFO_COUNT"] = KBomInfoCount

# this binding exists because shared behavior needs one stable value
globals()["BOM_MANAGER_CLASS"] = KBomManagerClass

# this binding exists because shared behavior needs one stable value
globals()["BOM_MANAGER_SCHEMA"] = KBomManagerSchema

# this binding exists because shared behavior needs one stable value
globals()["DOCUMENT_GENERATION"] = KDocGeneration

# this binding exists because shared behavior needs one stable value
globals()["DRAFTING_STANDARDS"] = KDraftingStandards

# this binding exists because shared behavior needs one stable value
globals()["DRAFTING_STANDARD_SCHEMA"] = KDraftingStandardSchema

# this binding exists because shared behavior needs one stable value
globals()["DRAFTING_STANDARD_STATE"] = KDraftingStandardState

# this binding exists because shared behavior needs one stable value
globals()["ENVIRONMENT_BUILD_STAMP"] = KEnvironmentBuildStamp

# this binding exists because shared behavior needs one stable value
globals()["ENVIRONMENT_CAPACITY"] = KEnvironmentCapacity

# this binding exists because shared behavior needs one stable value
globals()["ENVIRONMENT_RESERVED_HEAD_BYTES"] = KEnvironmentReservedHead

# this binding exists because shared behavior needs one stable value
globals()["ENVIRONMENT_RESERVED_MIDDLE_BYTES"] = KEnvironmentReservedMiddA

# this binding exists because shared behavior needs one stable value
globals()["ENVIRONMENT_SENTINELS"] = KEnvironmentSentinels

# this binding exists because shared behavior needs one stable value
globals()["ENVIRONMENT_TRAILING_FLAG"] = KEnvironmentTrailingFlag

# this binding exists because shared behavior needs one stable value
globals()["FIRST_LOAD_ARRAY_INDEX"] = KFirstLoadArrayIndex

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_ATTACHMENT"] = KJournalAttachment

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_CLASS"] = KJournalClass

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_HEAD_FIRST_FLAG"] = KJournalHeadFirstFlag

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_HEAD_SCHEMA_FLAGS"] = KJournalHeadSchemaFlags

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_HEAD_SECOND_FLAG"] = KJournalHeadSecondFlag

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_HEAD_THIRD_FLAG"] = KJournalHeadThirdFlag

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_PAGE_HEIGHT"] = KJournalPageHeight

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_RECORD_HEAD_BYTES"] = KJournalRecordHeadBytes

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_RECORD_TAIL_BYTES"] = KJournalRecordTailBytes

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_SCHEMA"] = KJournalSchema

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_SLOTS"] = KJournalSlots

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_TAIL_OPTION_VALUES"] = KJournalTailOptionValues

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_TAIL_PAGE_UNITS"] = KJournalTailPageUnits

# this binding exists because shared behavior needs one stable value
globals()["JOURNAL_TAIL_STYLE"] = KJournalTailStyle

# this binding exists because shared behavior needs one stable value
globals()["LINE_FONT_BINDINGS"] = KLineFontBindings

# this binding exists because shared behavior needs one stable value
globals()["LINE_FONT_CONFIG_CLASS"] = KLineFontConfigClass

# this binding exists because shared behavior needs one stable value
globals()["LINE_FONT_CONFIG_SCHEMA"] = KLineFontConfigSchema

# this binding exists because shared behavior needs one stable value
globals()["LINE_FONT_INHERITED_WIDTH"] = KLineFontInheritedWidth

# this binding exists because shared behavior needs one stable value
globals()["LINE_FONT_MANAGER_CLASS"] = KLineFontManagerClass

# this binding exists because shared behavior needs one stable value
globals()["LINE_FONT_MANAGER_SCHEMA"] = KLineFontManagerSchema

# this binding exists because shared behavior needs one stable value
globals()["LINE_FONT_MANAGER_TRAILING"] = KLineFontManagerTrailing

# this binding exists because shared behavior needs one stable value
globals()["LINE_STYLES"] = KLineStyles

# this binding exists because shared behavior needs one stable value
globals()["LINE_STYLE_CLASS"] = KLineStyleClass

# this binding exists because shared behavior needs one stable value
globals()["LINE_STYLE_SCHEMA"] = KLineStyleSchema

# this binding exists because shared behavior needs one stable value
globals()["LONG_STRING_UNITS"] = KLongStringUnits

# this binding exists because shared behavior needs one stable value
globals()["MANAGER_TAIL_WORDS"] = KManagerTailWords

# this binding exists because shared behavior needs one stable value
globals()["NEW_CLASS_TOKEN"] = KNewClassToken

# this binding exists because shared behavior needs one stable value
globals()["OPAQUE_SPANS"] = KOpaqueSpans

# this binding exists because shared behavior needs one stable value
globals()["PART_CLSID"] = KPartClsid

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_FIELD12"] = KPreambleFieldOneTwo

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_FIELD16"] = KPreambleFieldOneSix

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_FIELD8"] = KPreambleFieldEight

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_FLAGS"] = KPreambleFlags

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_GENERATION"] = KPreambleGeneration

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_MIDDLE"] = KPreambleMiddle

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_PAD"] = KPreamblePad

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_RESERVED"] = KPreambleReserved

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_SCALE"] = KPreambleScale

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_TAIL"] = KPreambleTail

# this binding exists because shared behavior needs one stable value
globals()["PREAMBLE_TRAILER_WORDS"] = KPreambleTrailerWords

# this binding exists because shared behavior needs one stable value
globals()["SESSION_HEADER_WORDS"] = KSessionHeaderWords

# this binding exists because shared behavior needs one stable value
globals()["STRING_MARKER"] = KStringMarker

# this binding exists because shared behavior needs one stable value
globals()["USER_MODEL_ENV_CLASS"] = KUserModelEnvClass

# this binding exists because shared behavior needs one stable value
globals()["USER_MODEL_ENV_SCHEMA"] = KUserModelEnvSchema

# this binding exists because shared behavior needs one stable value
globals()["UUID"] = UuidValue

# this binding exists because shared behavior needs one stable value
globals()["VIEW_BLOCK_DOUBLES"] = KViewBlockDoubles

# this binding exists because shared behavior needs one stable value
globals()["VIEW_RECORDS"] = KViewRecords

# this binding exists because shared behavior needs one stable value
globals()["WINDOW_PLACEMENT_FIELDS"] = KWindowPlacementFields

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()["encode_body"] = EncodeBodyOld

# this binding exists because shared behavior needs one stable value
globals()["encode_definition_stream"] = EncodeStreamOld

# this binding exists because shared behavior needs one stable value
globals()["encode_preamble"] = EncodePreOld

# this binding exists because shared behavior needs one stable value
globals()["encode_string"] = EncodeString

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct

# this binding exists because shared behavior needs one stable value
globals()["write_bom_manager"] = WriteBomManager

# this binding exists because shared behavior needs one stable value
globals()["write_drafting_standard"] = WriteDrafting

# this binding exists because shared behavior needs one stable value
globals()["write_environment_tail"] = WriteTail

# this binding exists because shared behavior needs one stable value
globals()["write_journal"] = WriteJournal

# this binding exists because shared behavior needs one stable value
globals()["write_journal_head"] = WriteJournalA

# this binding exists because shared behavior needs one stable value
globals()["write_journal_tail"] = WriteJournalB

# this binding exists because shared behavior needs one stable value
globals()["write_line_fonts"] = WriteLineFonts

# this binding exists because shared behavior needs one stable value
globals()["write_line_styles"] = WriteLineStyles

# this binding exists because shared behavior needs one stable value
globals()["write_user_model_env"] = WriteUserModel

# this binding exists because shared behavior needs one stable value
globals()["write_view"] = WriteView

# this binding exists because shared behavior needs one stable value
globals()["write_window_placement"] = WriteWindow
