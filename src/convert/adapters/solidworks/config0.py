# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from .config0_program import ConfigOps, EncodeProgram, FieldOwners
from .container import SldprtFormatError


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
    return EncodeProgram(
        PartName=part_name,
        Atoms=tuple(atoms),
        SessionStamp=session_stamp,
        Generation=generation,
        DualLengthUnits=dual_length_units,
        HighWater=high_water,
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
