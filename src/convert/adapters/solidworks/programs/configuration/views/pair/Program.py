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
    (278, 2, 42, "classref", 101),
    (280, 16, 43, "string", "*Right"),
    (296, 1, 36, "primitive:uchar", 1),
    (297, 8, 27, "primitive:double", float.fromhex("0x0.0p+0")),
    (305, 8, 28, "primitive:double", float.fromhex("0x0.0p+0")),
    (313, 8, 29, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (321, 8, 30, "primitive:double", float.fromhex("0x0.0p+0")),
    (329, 8, 31, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (337, 8, 32, "primitive:double", float.fromhex("0x0.0p+0")),
    (345, 8, 33, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
    (353, 8, 34, "primitive:double", float.fromhex("-0x0.0p+0")),
    (361, 8, 35, "primitive:double", float.fromhex("-0x0.0p+0")),
    (369, 8, 37, "primitive:double", float.fromhex("0x0.0p+0")),
    (377, 8, 38, "primitive:double", float.fromhex("0x0.0p+0")),
    (385, 8, 39, "primitive:double", float.fromhex("0x0.0p+0")),
    (393, 8, 40, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (401, 1, 41, "primitive:uchar", 0),
    (402, 1, 36, "primitive:uchar", 0),
    (403, 8, 37, "primitive:double", float.fromhex("0x0.0p+0")),
    (411, 8, 38, "primitive:double", float.fromhex("0x0.0p+0")),
    (419, 8, 39, "primitive:double", float.fromhex("0x0.0p+0")),
    (427, 8, 40, "primitive:double", float.fromhex("0x1.0000000000000p+0")),
    (435, 1, 41, "primitive:uchar", 0),
    (436, 2, 15, "primitive:ushort", 0),
    (438, 4, 16, "primitive:long", -1),
    (442, 8, 17, "primitive:double", float.fromhex("-0x1.0000000000000p+0")),
    (450, 4, 18, "primitive:long", 0),
    (454, 4, 19, "primitive:long", 201),
    (458, 4, 20, "primitive:long", 0),
    (462, 4, 21, "primitive:long", 0),
    (466, 4, 22, "primitive:long", 0),
    (470, 8, 23, "primitive:double", float.fromhex("0x0.0p+0")),
    (478, 4, 24, "primitive:long", 0),
    (482, 4, 25, "primitive:long", 0),
    (486, 4, 26, "primitive:long", 0),
    (490, 4, 4, "primitive:long", 0),
    (494, 2, 42, "null", 0),
    (496, 2, 42, "null", 0),
    (498, 4, 5, "primitive:long", 0),
    (502, 8, 6, "primitive:double", float.fromhex("0x0.0p+0")),
    (510, 2, 42, "null", 0),
    (512, 4, 7, "primitive:long", 0),
    (516, 4, 8, "primitive:long", 1),
    (520, 2, 42, "null", 0),
    (522, 4, 0, "primitive:long", -1),
    (526, 4, 1, "primitive:long", 0),
    (530, 4, 2, "primitive:long", -1),
    (534, 4, 3, "primitive:long", -1),
    (538, 4, 9, "primitive:long", 201),
    (542, 4, 10, "primitive:long", 199),
    (546, 4, 11, "primitive:long", 1),
    (550, 4, 12, "primitive:long", 199),
    (554, 2, 42, "null", 0),
    (556, 4, 13, "primitive:ulong", 0),
    (560, 4, 14, "primitive:long", 0),
    (564, 2, 44, "primitive:ushort", 0),
    (566, 2, 44, "primitive:ushort", 0),
    (568, 2, 44, "primitive:ushort", 0),
    (570, 2, 44, "primitive:ushort", 0),
    (572, 2, 44, "primitive:ushort", 0),
    (574, 2, 44, "primitive:ushort", 0),
    (576, 2, 44, "primitive:ushort", 0),
    (578, 2, 44, "primitive:ushort", 0),
    (580, 2, 42, "null", 0),
    (582, 2, 44, "primitive:ushort", 0),
)

# the source interval records where the reusable manager was observed
SourceRange = (24360, 24944)

# exact closure rejects any future field-width or ordering drift
ReferenceLength = 584


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
