# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .enum_base import WireEnum


# value categories preserve parameter meaning beyond primitive python representation
class ValueKind(WireEnum):
    KLength = "length"
    KAngle = "angle"
    KQuantity = "quantity"
    KNumber = "number"
    KInteger = "integer"
    KBoolean = "boolean"
    KString = "string"


# parameter roles retain whether downstream systems may drive each value
class ParameterRole(WireEnum):
    KDriving = "driving"
    KDriven = "driven"
    KReference = "reference"
    KDerived = "derived"
