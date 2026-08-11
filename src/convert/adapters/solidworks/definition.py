# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass
import struct
from uuid import UUID

from .container import SldprtFormatError

DRAFTING_STANDARDS = ("moBS_c", "moISO_c", "moANSI_c")
DOCUMENT_GENERATION = 18000

# registered document class identifiers distinguish native part and assembly envelopes
PART_CLSID = UUID("83a33d30-27c5-11ce-bfd4-00400513bb57").bytes_le
ASSEMBLY_CLSID = UUID("83a33d36-27c5-11ce-bfd4-00400513bb57").bytes_le

PREAMBLE_FLAGS = 0x50
PREAMBLE_GENERATION = 6
PREAMBLE_FIELD8 = 50
PREAMBLE_FIELD12 = 1
PREAMBLE_FIELD16 = 1
PREAMBLE_RESERVED = bytes(3)
PREAMBLE_MIDDLE = bytes(24)
PREAMBLE_SCALE = 1.0
PREAMBLE_PAD = 0
PREAMBLE_TAIL = (0.0, 0.0, 0.0, 0.0)
# seven recovered trailer words close the generation-18000 definition preamble
PREAMBLE_TRAILER_WORDS = (768, 256, 512, 36090, 16294, 5129, 24576)
VIEW_BLOCK_DOUBLES = 9

NEW_CLASS_TOKEN = 0xFFFF
BACK_REFERENCE_TOKEN = 0x8000
FIRST_LOAD_ARRAY_INDEX = 1
STRING_MARKER = b"\xff\xfe\xff"
LONG_STRING_UNITS = 0xFF

DRAFTING_STANDARD_SCHEMA = 1
DRAFTING_STANDARD_STATE = 7

LINE_STYLE_CLASS = "moLineStyle_c"
LINE_STYLE_SCHEMA = 1


@dataclass(frozen=True, slots=True)
class LineStyle:
    key: str
    display: str
    segments: tuple[float, ...]
    flag: int = 0


LINE_STYLES = (
    LineStyle("CONTINUOUS", "Solid", (12.0,)),
    LineStyle("HIDDEN", "Dashed", (0.25, -0.125)),
    LineStyle("PHANTOM", "Phantom", (1.25, -0.25, 0.25, -0.25, 0.25, -0.25)),
    LineStyle("CHAIN", "Chain", (1.25, -0.25, 0.25, -0.25)),
    LineStyle("CENTER", "Center", (3.0, -0.25, 0.25, -0.25)),
    LineStyle("STITCH", "Stitch", (0.0, -0.125)),
    LineStyle("CHAIN_THICK", "Thin/Thick Chain", (1.25, -0.25, 0.25, -0.25), 1),
)

LINE_FONT_MANAGER_CLASS = "uiLineFontMgr_c"
LINE_FONT_MANAGER_SCHEMA = 1
LINE_FONT_MANAGER_TRAILING = 1
LINE_FONT_CONFIG_CLASS = "uiLFConfig_c"
LINE_FONT_CONFIG_SCHEMA = 1
LINE_FONT_INHERITED_WIDTH = -1.0


@dataclass(frozen=True, slots=True)
class LineFontBinding:
    annotation: str
    font: str
    weight: int = 0
    width: float = LINE_FONT_INHERITED_WIDTH
    trailing: int = 0


LINE_FONT_BINDINGS = (
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
    LineFontBinding("ViewArrow", "PHANTOM", 2),
    LineFontBinding("EmphasizedOutline", "CONTINUOUS", 2, LINE_FONT_INHERITED_WIDTH, 2),
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

USER_MODEL_ENV_CLASS = "uiUserModelEnv_c"
USER_MODEL_ENV_SCHEMA = 1

# typed session words preserve the environment schema and viewport dimensions
SESSION_HEADER_WORDS = (1, 1, 778, 10, 1520, 10, 0, 0)
# the primary window placement stores its extents, flags, and terminal sentinel
WINDOW_PLACEMENT_FIELDS = (1519, 227, 2, 1, 0, 750, 227, 10, -1)
# the environment tail contains reserved regions, capacity, sentinels, and build stamp
ENVIRONMENT_RESERVED_HEAD_BYTES = 12
ENVIRONMENT_CAPACITY = 96
ENVIRONMENT_RESERVED_MIDDLE_BYTES = 20
ENVIRONMENT_SENTINELS = (-1, -1)
ENVIRONMENT_BUILD_STAMP = 73781
ENVIRONMENT_TRAILING_FLAG = 0


@dataclass(frozen=True, slots=True)
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


VIEW_RECORDS = (
    ViewRecord(
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
        centre=(
            0.03568485564735271,
            0.004222922958999075,
            -0.007028124036209772,
        ),
        height=6.180518783629107,
        trailer_flag=0,
        trailer_first=3,
        trailer_second=1,
        trailer_value=-1.0,
        name="",
        has_window_placement=True,
    ),
    ViewRecord(
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
    ),
    ViewRecord(
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
    ),
)

BOM_MANAGER_CLASS = "moBomInfoMgr_c"
BOM_MANAGER_SCHEMA = 1
BOM_INFO_COUNT = 0
# the empty BOM manager tail retains its schema flags and native build identity
MANAGER_TAIL_WORDS = (1, 38284, 0, 515, 0)

JOURNAL_CLASS = "uoJournal_c"
JOURNAL_SCHEMA = 0
JOURNAL_ATTACHMENT = "Design Journal.doc"
JOURNAL_SLOTS = (("", 0), ("", 0), ("", 0))
JOURNAL_PAGE_HEIGHT = 1000.0
# sparse typed journal records replace the former copied binary spans
JOURNAL_HEAD_FIRST_FLAG = 1
JOURNAL_HEAD_SECOND_FLAG = 1
JOURNAL_HEAD_THIRD_FLAG = 1
JOURNAL_HEAD_SCHEMA_FLAGS = 1537
JOURNAL_TAIL_PAGE_UNITS = 100
JOURNAL_TAIL_STYLE = 5
JOURNAL_TAIL_OPTION_VALUES = (1, 1, 1, 1, 1, 1, 1, 2, 3, 1)
JOURNAL_RECORD_HEAD_BYTES = 47
JOURNAL_RECORD_TAIL_BYTES = 146

# every definition byte now has a typed owner
OPAQUE_SPANS: tuple[bytes, ...] = ()


def encode_string(text: str) -> bytes:
    units = text.encode("utf-16-le")
    count = len(units) // 2
    if count < LONG_STRING_UNITS:
        return STRING_MARKER + bytes([count]) + units
    return STRING_MARKER + b"\xff" + struct.pack("<H", count) + units


class ArchiveWriter:
    __slots__ = ("chunks", "classes", "next_index")

    def __init__(self) -> None:
        self.chunks: list[bytes] = []
        self.classes: dict[str, int] = {}
        self.next_index = FIRST_LOAD_ARRAY_INDEX

    def raw(self, chunk: bytes) -> None:
        self.chunks.append(chunk)

    def u8(self, value: int) -> None:
        self.chunks.append(struct.pack("<B", value))

    def u16(self, value: int) -> None:
        self.chunks.append(struct.pack("<H", value))

    def i16(self, value: int) -> None:
        self.chunks.append(struct.pack("<h", value))

    def i32(self, value: int) -> None:
        self.chunks.append(struct.pack("<i", value))

    def u32(self, value: int) -> None:
        self.chunks.append(struct.pack("<I", value))

    def f32(self, value: float) -> None:
        self.chunks.append(struct.pack("<f", value))

    def f64(self, value: float) -> None:
        self.chunks.append(struct.pack("<d", value))

    def zeros(self, count: int) -> None:
        self.chunks.append(bytes(count))

    def string(self, text: str) -> None:
        self.chunks.append(encode_string(text))

    def begin_object(self, name: str, schema: int) -> None:
        index = self.classes.get(name)
        if index is None:
            encoded = name.encode("ascii")
            self.u16(NEW_CLASS_TOKEN)
            self.u16(schema)
            self.u16(len(encoded))
            self.raw(encoded)
            self.classes[name] = self.next_index
            self.next_index += 1
        else:
            self.u16(BACK_REFERENCE_TOKEN | index)
        self.next_index += 1

    def build(self) -> bytes:
        return b"".join(self.chunks)


def write_drafting_standard(writer: ArchiveWriter, standard: str) -> None:
    if standard not in DRAFTING_STANDARDS:
        raise SldprtFormatError(f"unknown SOLIDWORKS drafting standard {standard!r}")
    writer.begin_object(standard, DRAFTING_STANDARD_SCHEMA)
    writer.u32(DRAFTING_STANDARD_STATE)


def write_line_styles(writer: ArchiveWriter) -> None:
    for style in LINE_STYLES:
        writer.begin_object(LINE_STYLE_CLASS, LINE_STYLE_SCHEMA)
        writer.string(style.key)
        writer.string(style.display)
        writer.u16(len(style.segments))
        for segment in style.segments:
            writer.f64(segment)
        writer.u8(style.flag)


def write_line_fonts(writer: ArchiveWriter) -> None:
    writer.begin_object(LINE_FONT_MANAGER_CLASS, LINE_FONT_MANAGER_SCHEMA)
    writer.u16(len(LINE_FONT_BINDINGS))
    for binding in LINE_FONT_BINDINGS:
        writer.string(binding.annotation)
        writer.begin_object(LINE_FONT_CONFIG_CLASS, LINE_FONT_CONFIG_SCHEMA)
        writer.string(binding.font)
        writer.i16(binding.weight)
        writer.f32(binding.width)
        writer.i16(binding.trailing)
    writer.u16(LINE_FONT_MANAGER_TRAILING)


def write_view(writer: ArchiveWriter, view: ViewRecord) -> None:
    writer.u8(1 if view.rotation else 0)
    for value in view.rotation:
        writer.f64(value)
    for value in view.translation:
        writer.f64(value)
    writer.f64(view.scale)
    writer.u16(view.gap)
    for value in view.centre:
        writer.f64(value)
    writer.f64(view.height)
    writer.u8(view.trailer_flag)
    writer.u16(view.trailer_first)
    writer.u16(view.trailer_second)
    writer.f64(view.trailer_value)
    writer.string(view.name)
    if view.has_window_placement:
        write_window_placement(writer)


# typed window coordinates replace the former fixed placement byte block
def write_window_placement(writer: ArchiveWriter) -> None:
    LeftValue, TopValue, *WordData, SentinelValue = WINDOW_PLACEMENT_FIELDS
    writer.u32(LeftValue)
    writer.u32(TopValue)
    for ItemData in WordData:
        writer.u16(ItemData)
    writer.i32(SentinelValue)


# the recovered environment tail is emitted from its primitive field grammar
def write_environment_tail(writer: ArchiveWriter) -> None:
    writer.zeros(ENVIRONMENT_RESERVED_HEAD_BYTES)
    writer.u32(ENVIRONMENT_CAPACITY)
    writer.zeros(ENVIRONMENT_RESERVED_MIDDLE_BYTES)
    for ItemData in ENVIRONMENT_SENTINELS:
        writer.i32(ItemData)
    writer.u32(ENVIRONMENT_BUILD_STAMP)
    writer.u8(ENVIRONMENT_TRAILING_FLAG)


def write_user_model_env(writer: ArchiveWriter, user: str) -> None:
    writer.begin_object(USER_MODEL_ENV_CLASS, USER_MODEL_ENV_SCHEMA)
    writer.string(user)
    for ItemData in SESSION_HEADER_WORDS:
        writer.u16(ItemData)
    for view in VIEW_RECORDS:
        write_view(writer, view)
    write_environment_tail(writer)


def write_bom_manager(writer: ArchiveWriter) -> None:
    writer.begin_object(BOM_MANAGER_CLASS, BOM_MANAGER_SCHEMA)
    writer.u32(BOM_INFO_COUNT)
    HeadValue, BuildValue, ReservedValue, FlagValue, TailValue = MANAGER_TAIL_WORDS
    writer.u16(HeadValue)
    writer.u16(BuildValue)
    writer.u32(ReservedValue)
    writer.u16(0)
    writer.u16(FlagValue)
    writer.u16(TailValue)


# the journal head uses fixed flags separated by explicitly sized reserved regions
def write_journal_head(writer: ArchiveWriter) -> None:
    writer.zeros(10)
    writer.u16(JOURNAL_HEAD_FIRST_FLAG)
    writer.zeros(4)
    writer.u32(JOURNAL_HEAD_SECOND_FLAG)
    writer.zeros(9)
    writer.u32(JOURNAL_HEAD_THIRD_FLAG)
    writer.zeros(3)
    writer.u16(JOURNAL_HEAD_SCHEMA_FLAGS)
    writer.zeros(9)


# the journal tail serializes its recovered sparse option table without raw bytes
def write_journal_tail(writer: ArchiveWriter) -> None:
    writer.zeros(30)
    writer.u32(JOURNAL_TAIL_PAGE_UNITS)
    writer.u32(JOURNAL_TAIL_STYLE)
    writer.zeros(8)
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
    ) = JOURNAL_TAIL_OPTION_VALUES
    writer.u32(FirstValue)
    writer.zeros(12)
    writer.u32(SecondValue)
    writer.zeros(8)
    writer.u32(ThirdValue)
    writer.u32(FourthValue)
    writer.zeros(4)
    writer.u32(FifthValue)
    writer.zeros(6)
    writer.u32(SixthValue)
    writer.u32(SeventhValue)
    writer.zeros(12)
    writer.u32(EighthValue)
    writer.zeros(14)
    writer.u32(NinthValue)
    writer.u32(TenthValue)
    writer.zeros(4)


def write_journal(writer: ArchiveWriter) -> None:
    writer.begin_object(JOURNAL_CLASS, JOURNAL_SCHEMA)
    writer.string(JOURNAL_ATTACHMENT)
    write_journal_head(writer)
    for text, trailing in JOURNAL_SLOTS:
        writer.string(text)
        writer.u16(trailing)
    write_journal_tail(writer)
    writer.f64(JOURNAL_PAGE_HEIGHT)


def encode_body(*, standard: str = "moBS_c", user: str = "Kit") -> bytes:
    writer = ArchiveWriter()
    write_drafting_standard(writer, standard)
    write_line_styles(writer)
    write_line_fonts(writer)
    write_user_model_env(writer, user)
    write_bom_manager(writer)
    write_journal(writer)
    return writer.build()


def encode_preamble(
    *, clsid: bytes = PART_CLSID, view: tuple[float, ...] | None = None
) -> bytes:
    chunk = bytearray()
    chunk += struct.pack(
        "<IIIII",
        PREAMBLE_FLAGS,
        PREAMBLE_GENERATION,
        PREAMBLE_FIELD8,
        PREAMBLE_FIELD12,
        PREAMBLE_FIELD16,
    )
    chunk += clsid
    chunk += PREAMBLE_RESERVED + bytes([0 if view is None else 1])
    if view is not None:
        if len(view) != VIEW_BLOCK_DOUBLES:
            raise SldprtFormatError(
                f"definition view block needs {VIEW_BLOCK_DOUBLES} doubles, "
                f"{len(view)} were supplied"
            )
        for value in view:
            chunk += struct.pack("<d", value)
    chunk += PREAMBLE_MIDDLE
    chunk += struct.pack("<d", PREAMBLE_SCALE)
    chunk += struct.pack("<H", PREAMBLE_PAD)
    for value in PREAMBLE_TAIL:
        chunk += struct.pack("<d", value)
    for ItemData in PREAMBLE_TRAILER_WORDS:
        chunk += struct.pack("<H", ItemData)
    return bytes(chunk)


def encode_definition_stream(
    *,
    standard: str = "moBS_c",
    user: str = "Kit",
    assembly: bool = False,
    view: tuple[float, ...] | None = None,
) -> bytes:
    clsid = ASSEMBLY_CLSID if assembly else PART_CLSID
    return encode_preamble(clsid=clsid, view=view) + encode_body(
        standard=standard, user=user
    )
