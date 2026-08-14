# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.configuration.default.Program import EncodeField
from convert.adapters.solidworks.container.Container import SldprtFormatError


# recovered callsites make every annotation field traceable to its native serializer
FieldOwners = (
    "SLDMODU!mo3dView_c::Serialize+0x1091",
    "SLDMODU!mo3dView_c::Serialize+0x10dc",
    "SLDMODU!mo3dView_c::Serialize+0x1125",
    "SLDMODU!mo3dView_c::Serialize+0x115c",
    "SLDMODU!mo3dView_c::Serialize+0xda0",
    "SLDMODU!mo3dView_c::Serialize+0xf10",
    "SLDMODU!mo3dView_c::Serialize+0xf53",
    "SLDMODU!mo3dView_c::Serialize+0xfe8",
    "SLDMODU!mo3dView_c::Serialize+0xff8",
    "SLDMODU!moPartConfiguration_c::SerializeMBSMDataObjects+0x41a1",
    "SLDMODU!moPartConfiguration_c::SerializeMBSMDataObjects+0x41bd",
    "SLDMODU!moPartConfiguration_c::SerializeMBSMDataObjects+0x41f0",
    "SLDMODU!moPartConfiguration_c::SerializeMBSMDataObjects+0x4215",
    "SLDMODU!moPartConfiguration_c::SerializeMBSMDataObjects+0x4303",
    "SLDMODU!moPartConfiguration_c::SerializeMBSMDataObjects+0x4322",
    "SLDMODU!moView_c::Serialize+0x23d",
    "SLDMODU!moView_c::Serialize+0x257",
    "SLDMODU!moView_c::Serialize+0x298",
    "SLDMODU!moView_c::Serialize+0x2f8",
    "SLDMODU!moView_c::Serialize+0x3de",
    "SLDMODU!moView_c::Serialize+0x468",
    "SLDMODU!moView_c::Serialize+0x475",
    "SLDMODU!moView_c::Serialize+0x51d",
    "SLDMODU!moView_c::Serialize+0x52d",
    "SLDMODU!moView_c::Serialize+0x53a",
    "SLDMODU!moView_c::Serialize+0x5e7",
    "SLDMODU!moView_c::Serialize+0x621",
    "sldmgu!mgMatrix_c::restore+0x5a",
    "sldmgu!mgMatrix_c::restore+0x67",
    "sldmgu!mgMatrix_c::restore+0x74",
    "sldmgu!mgMatrix_c::restore+0x82",
    "sldmgu!mgMatrix_c::restore+0x90",
    "sldmgu!mgMatrix_c::restore+0x9e",
    "sldmgu!mgMatrix_c::restore+0xac",
    "sldmgu!mgMatrix_c::restore+0xba",
    "sldmgu!mgMatrix_c::restore+0xc8",
    "sldmgu!mgXform_c::restore+0x23",
    "sldmgu!mgXform_c::restore+0x43",
    "sldmgu!mgXform_c::restore+0x50",
    "sldmgu!mgXform_c::restore+0x5d",
    "sldmgu!mgXform_c::restore+0x6a",
    "sldmgu!mgXform_c::restore+0x78",
    "su_CArchive::ReadClass",
    "su_CArchive::WriteString",
    "swccu!su_CArchive::ReadCount+0x13",
)

# relative offsets preserve the two-view annotation manager's complete typed order
AnnotationOps = (
    (0, 24, 42, "definition", ("moAnnotationView_c", 1)),
    (24, 12, 43, "string", "*Top"),
    (36, 1, 36, "primitive:uchar", 1),
    (37, 8, 27, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (45, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
    (53, 8, 29, "primitive:double", float.fromhex("0x0.0p+0")),
    (61, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
    (69, 8, 31, "primitive:double", float.fromhex("0x0.0p+0")),
    (77, 8, 32, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (85, 8, 33, "primitive:double", float.fromhex("-0x0.0p+0")),
    (93, 8, 34, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
    (101, 8, 35, "primitive:double", float.fromhex("-0x0.0p+0")),
    (109, 8, 37, "primitive:double", float.fromhex("0x0.0p+0")),
    (117, 8, 38, "primitive:double", float.fromhex("0x0.0p+0")),
    (125, 8, 39, "primitive:double", float.fromhex("0x0.0p+0")),
    (133, 8, 40, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (141, 1, 41, "primitive:uchar", 0),
    (142, 1, 36, "primitive:uchar", 0),
    (143, 8, 37, "primitive:double", float.fromhex("0x0.0p+0")),
    (151, 8, 38, "primitive:double", float.fromhex("0x0.0p+0")),
    (159, 8, 39, "primitive:double", float.fromhex("0x0.0p+0")),
    (167, 8, 40, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (175, 1, 41, "primitive:uchar", 0),
    (176, 2, 15, "primitive:ushort", 0),
    (178, 4, 16, "primitive:long", -1),
    (182, 8, 17, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
    (190, 4, 18, "primitive:long", 0),
    (194, 4, 19, "primitive:long", 200),
    (198, 4, 20, "primitive:long", 0),
    (202, 4, 21, "primitive:long", 0),
    (206, 4, 22, "primitive:long", 0),
    (210, 8, 23, "primitive:double", float.fromhex("0x0.0p+0")),
    (218, 4, 24, "primitive:long", 0),
    (222, 4, 25, "primitive:long", 0),
    (226, 4, 26, "primitive:long", 0),
    (230, 4, 4, "primitive:long", 0),
    (234, 2, 42, "null", 0),
    (236, 2, 42, "null", 0),
    (238, 4, 5, "primitive:long", 0),
    (242, 8, 6, "primitive:double", float.fromhex("0x0.0p+0")),
    (250, 2, 42, "null", 0),
    (252, 4, 7, "primitive:long", 0),
    (256, 4, 8, "primitive:long", 1),
    (260, 2, 42, "null", 0),
    (262, 4, 0, "primitive:long", -1),
    (266, 4, 1, "primitive:long", 0),
    (270, 4, 2, "primitive:long", -1),
    (274, 4, 3, "primitive:long", -1),
    (278, 2, 42, "classref", 100),
    (280, 14, 43, "string", "*Back"),
    (294, 1, 36, "primitive:uchar", 1),
    (295, 8, 27, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
    (303, 8, 28, "primitive:double", float.fromhex("-0x0.0p+0")),
    (311, 8, 29, "primitive:double", float.fromhex("-0x0.0p+0")),
    (319, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
    (327, 8, 31, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (335, 8, 32, "primitive:double", float.fromhex("0x0.0p+0")),
    (343, 8, 33, "primitive:double", float.fromhex("-0x0.0p+0")),
    (351, 8, 34, "primitive:double", float.fromhex("-0x0.0p+0")),
    (359, 8, 35, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
    (367, 8, 37, "primitive:double", float.fromhex("0x0.0p+0")),
    (375, 8, 38, "primitive:double", float.fromhex("0x0.0p+0")),
    (383, 8, 39, "primitive:double", float.fromhex("0x0.0p+0")),
    (391, 8, 40, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (399, 1, 41, "primitive:uchar", 0),
    (400, 1, 36, "primitive:uchar", 0),
    (401, 8, 37, "primitive:double", float.fromhex("0x0.0p+0")),
    (409, 8, 38, "primitive:double", float.fromhex("0x0.0p+0")),
    (417, 8, 39, "primitive:double", float.fromhex("0x0.0p+0")),
    (425, 8, 40, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (433, 1, 41, "primitive:uchar", 0),
    (434, 2, 15, "primitive:ushort", 0),
    (436, 4, 16, "primitive:long", -1),
    (440, 8, 17, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
    (448, 4, 18, "primitive:long", 0),
    (452, 4, 19, "primitive:long", 201),
    (456, 4, 20, "primitive:long", 0),
    (460, 4, 21, "primitive:long", 0),
    (464, 4, 22, "primitive:long", 0),
    (468, 8, 23, "primitive:double", float.fromhex("0x0.0p+0")),
    (476, 4, 24, "primitive:long", 0),
    (480, 4, 25, "primitive:long", 0),
    (484, 4, 26, "primitive:long", 0),
    (488, 4, 4, "primitive:long", 0),
    (492, 2, 42, "null", 0),
    (494, 2, 42, "null", 0),
    (496, 4, 5, "primitive:long", 0),
    (500, 8, 6, "primitive:double", float.fromhex("0x0.0p+0")),
    (508, 2, 42, "null", 0),
    (510, 4, 7, "primitive:long", 0),
    (514, 4, 8, "primitive:long", 1),
    (518, 2, 42, "null", 0),
    (520, 4, 0, "primitive:long", -1),
    (524, 4, 1, "primitive:long", 0),
    (528, 4, 2, "primitive:long", -1),
    (532, 4, 3, "primitive:long", -1),
    (536, 4, 9, "primitive:long", 201),
    (540, 4, 10, "primitive:long", 199),
    (544, 4, 11, "primitive:long", 1),
    (548, 4, 12, "primitive:long", 199),
    (552, 2, 42, "null", 0),
    (554, 4, 13, "primitive:ulong", 0),
    (558, 4, 14, "primitive:long", 0),
    (562, 2, 44, "primitive:ushort", 0),
    (564, 2, 44, "primitive:ushort", 0),
    (566, 2, 44, "primitive:ushort", 0),
    (568, 2, 44, "primitive:ushort", 0),
    (570, 2, 44, "primitive:ushort", 0),
    (572, 2, 44, "primitive:ushort", 0),
    (574, 2, 44, "primitive:ushort", 0),
    (576, 2, 44, "primitive:ushort", 0),
    (578, 2, 42, "null", 0),
    (580, 2, 44, "primitive:ushort", 0),
)

# the source interval records where the reusable manager was observed
SourceRange = (24240, 24822)

# exact closure rejects any future field-width or ordering drift
ReferenceLength = 582


# typed field replay emits the two-view manager without retaining vendor byte spans
def EncodeTwoViewAnnotationManager() -> bytes:
    OutputData = bytearray()
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, FieldValue in AnnotationOps:
        if StartPos != SourceCursor:
            raise SldprtFormatError(f"annotation field program drifted at {StartPos}")
        FieldData = EncodeField(KindName, FieldValue)
        if len(FieldData) != FieldWidth:
            raise SldprtFormatError(f"annotation field width changed at {StartPos}")
        OutputData.extend(FieldData)
        SourceCursor += FieldWidth
    if SourceCursor != ReferenceLength:
        raise SldprtFormatError("annotation field program did not close its source")
    return bytes(OutputData)
