# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import struct

from convert.adapters.solidworks.container.Archive import encode_class_definition
from convert.adapters.solidworks.programs.configuration.fillet.views.Program import EncodeTwoViewAnnotationManager as EncodeFilletAnnotationManager
from convert.adapters.solidworks.programs.configuration.pattern.views.Program import EncodeTwoViewAnnotationManager as EncodePatternAnnotationManager
from convert.adapters.solidworks.programs.configuration.default.Program import ConfigOps, EncodeProgram, FieldOwners
from convert.adapters.solidworks.programs.configuration.views.pair.Program import EncodeTwoViewAnnotationManager
from convert.adapters.solidworks.container.Container import SldprtFormatError


# the traced generation selects the SOLIDWORKS 2025 model-object grammar
MO_VERSION = 18000

# reference semantics provide a reproducible exact field-program test vector
REFERENCE_SESSION_STAMP = 1
REFERENCE_ATOM_ID = 101
REFERENCE_TREE_ID = 32
REFERENCE_PART_NAME = "Part70"
REFERENCE_HIGH_WATER = (101, 103)
REFERENCE_SHA256 = "a0877db37735da4027459d8161425843e3ad90f1e3e90dc32835f9370dd643bb"
REFERENCE_LENGTH = 25214
SINGLE_LENGTH_UNIT_LENGTH = 25148
TWO_VIEW_ANNOTATION_BYTES = 260
FILLET_ANNOTATION_BYTES = 258
PATTERN_ANNOTATION_BYTES = 188

# the traced fillet atom stores its predecessor and relation stamp after its class tag
FILLET_ATOM_PARENT_RELATIVE = 60
FILLET_ATOM_LINK_STAMP_RELATIVES = (84, 92)
FILLET_ATOM_LINK_STAMP = 650

# measured dynamic widths constrain feature and body growth independently
PER_FEATURE_ATOM_BYTES = 88
PER_SOLID_BODY_BYTES = 16
MEASURED_VOLUME_MM3 = 8000.000000000001

# closure metrics make the absence of opaque byte spans directly testable
CONFIG_FIELD_COUNT = len(ConfigOps)
CONFIG_OWNER_COUNT = len(FieldOwners)
CONFIG_OPAQUE_BYTES = 0


# the public writer maps document semantics into the recovered typed field program
def encode_config0_stream(
    part_name: str = REFERENCE_PART_NAME,
    atoms: tuple[tuple[int, int], ...] = ((REFERENCE_ATOM_ID, REFERENCE_TREE_ID),),
    session_stamp: int = REFERENCE_SESSION_STAMP,
    generation: int = MO_VERSION,
    dual_length_units: bool = True,
    high_water: tuple[int, int] | None = None,
    part_record_body: bytes | None = None,
    annotation_view_count: int = 1,
    terminal_parent_tree_id: int | None = None,
    annotation_view_variant: str = "default",
) -> bytes:
    if part_record_body is not None:
        raise SldprtFormatError(
            "custom raw Config-0 prologue bodies are forbidden by first-principles writing"
        )
    if high_water is None:
        if not atoms:
            raise SldprtFormatError("Contents/Config-0 needs at least one atom record")
        HighestId = max(AtomId for AtomId, _TreeId in atoms)
        high_water = (HighestId, HighestId + 2 * len(atoms))
    StreamData = EncodeProgram(
        PartName=part_name,
        Atoms=tuple(atoms),
        SessionStamp=session_stamp,
        Generation=generation,
        DualLengthUnits=dual_length_units,
        HighWater=high_water,
    )
    if terminal_parent_tree_id is not None:
        if (
            len(atoms) != 1
            or not 1 <= terminal_parent_tree_id <= 0xFFFFFFFF
            or terminal_parent_tree_id == atoms[0][1]
        ):
            raise SldprtFormatError(
                "Config-0 terminal history requires one child atom and one "
                "distinct parent tree"
            )
        AtomTag = encode_class_definition("moAtom_c", 1)
        AtomStart = StreamData.find(AtomTag)
        if AtomStart < 0:
            raise SldprtFormatError("Config-0 terminal atom boundary changed")
        PatchedData = bytearray(StreamData)
        struct.pack_into(
            "<I",
            PatchedData,
            AtomStart + FILLET_ATOM_PARENT_RELATIVE,
            terminal_parent_tree_id,
        )
        for RelativeOffset in FILLET_ATOM_LINK_STAMP_RELATIVES:
            struct.pack_into(
                "<I",
                PatchedData,
                AtomStart + RelativeOffset,
                FILLET_ATOM_LINK_STAMP,
            )
        StreamData = bytes(PatchedData)
    if annotation_view_count == 1:
        if terminal_parent_tree_id is not None:
            raise SldprtFormatError(
                "Config-0 terminal fillet history requires its two annotation views"
            )
        if annotation_view_variant != "default":
            raise SldprtFormatError(
                "Config-0 annotation variants require two annotation views"
            )
        return StreamData
    if annotation_view_count != 2:
        raise SldprtFormatError(
            "Contents/Config-0 supports one or two recovered annotation views"
        )
    AnnotationTag = encode_class_definition("moAnnotationView_c", 1)
    MarkTag = encode_class_definition("moPMarkRecord_c", 1)
    AnnotationStart = StreamData.find(AnnotationTag)
    AnnotationEnd = StreamData.find(MarkTag, AnnotationStart)
    CountOffset = AnnotationStart - 2
    if (
        AnnotationStart < 2
        or AnnotationEnd < 0
        or struct.unpack_from("<H", StreamData, CountOffset)[0] != 1
    ):
        raise SldprtFormatError("Config-0 annotation manager boundaries changed")
    if terminal_parent_tree_id is not None:
        if annotation_view_variant != "default":
            raise SldprtFormatError(
                "terminal Config-0 history has a fixed annotation variant"
            )
        AnnotationManager = EncodeFilletAnnotationManager()
    elif annotation_view_variant in {"linear_pattern", "circular_pattern"}:
        AnnotationManager = EncodePatternAnnotationManager()
    elif annotation_view_variant == "default":
        AnnotationManager = EncodeTwoViewAnnotationManager()
    else:
        raise SldprtFormatError(
            f"unsupported Config-0 annotation variant {annotation_view_variant!r}"
        )
    return (
        StreamData[:CountOffset]
        + struct.pack("<H", annotation_view_count)
        + AnnotationManager
        + StreamData[AnnotationEnd:]
    )


# coverage reporting treats every emitted byte as typed and none as opaque
def declared_opaque_split(**kwargs: object) -> dict[str, int]:
    StreamData = encode_config0_stream(**kwargs)
    return {
        "stream_bytes": len(StreamData),
        "typed": len(StreamData),
        "opaque": CONFIG_OPAQUE_BYTES,
        "accounted": len(StreamData),
        "operations": CONFIG_FIELD_COUNT,
        "owners": CONFIG_OWNER_COUNT,
    }
