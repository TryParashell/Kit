# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Runtime override marker provisioning for interpreters lacking typing.override."""

from __future__ import annotations as Annotations

import typing as TypingCore
from typing import Callable as CallbackKind
from typing import ParamSpec as SignatureShape
from typing import TypeVar as LimitVariety

# signature shapes stay generic because every decorated declaration keeps its own parameters
KSignatureShape = SignatureShape("KSignatureShape")

# returned declarations keep their original type because markers never wrap behavior
KReturnValue = LimitVariety("KReturnValue")

# marker provisioning stays dynamic because static analyzers require the standard typing origin
KMarkerName = "override"

if not hasattr(TypingCore, KMarkerName):

    # decoration degrades to plain identity because older interpreters lack the standard marker
    def Override(
        NextValue: CallbackKind[KSignatureShape, KReturnValue],
    ) -> CallbackKind[KSignatureShape, KReturnValue]:
        return NextValue

    setattr(TypingCore, KMarkerName, Override)
