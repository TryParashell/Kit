# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import EncodeProgram as EncodeMidplaneConfig
from convert.adapters.solidworks.programs.resolved.revolve.pin.midplane.Program import EncodeProgram as EncodeMidplaneFeatures
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import CalcPinBounds, PinEnvelope


# the recovered action stamps keep symmetric sketch and revolution history coupled
KHeaderStamps = ((1786487441, 1786487442), (1786487442,))

# the authored identity fields reproduce the complete symmetric model header
KHeaderIdentity = (1786487434, 106, 103, 1786487442)

# the authored username completes the deterministic header grammar
KHeaderUser = "odin"


# callers need one explicit entrypoint for the symmetric configuration grammar
def EncodeConfig() -> bytes:
    return EncodeMidplaneConfig()


# callers need one explicit entrypoint for the symmetric feature grammar
def EncodeFeatures() -> bytes:
    return EncodeMidplaneFeatures()


# the symmetric oracle requires all recovered header identity fields together
def EncodeHeader() -> bytes:
    from convert.adapters.solidworks.core import Native as NativeMod

    CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp = KHeaderIdentity
    IdentityData = NativeMod._NativeIdentity(
        CreatedStamp,
        ModifiedStamp,
        BaselineStamp,
        HeaderStamp,
        NativeMod._SOLIDWORKS_CONFIGURATION_FLAGS,
        "Part1",
    )
    return NativeMod._header_payload(
        IdentityData,
        "Default",
        (
            *NativeMod._HEADER_OBJECTS,
            (26, "Sketch1", True),
            (31, "Revolve1", False),
        ),
        "",
        KHeaderUser,
        32,
        {26: KHeaderStamps[0], 31: KHeaderStamps[1]},
        CalcPinBounds(),
    )


# integration needs one immutable carrier for every coupled symmetric stream
def BuildEnvelope() -> PinEnvelope:
    HeaderBounds = CalcPinBounds()
    return PinEnvelope(
        Config0Payload=EncodeConfig(),
        HeaderPayload=EncodeHeader(),
        HeaderStamps=KHeaderStamps,
        HeaderBounds=HeaderBounds,
        HeaderCreation=KHeaderIdentity[0],
    )
