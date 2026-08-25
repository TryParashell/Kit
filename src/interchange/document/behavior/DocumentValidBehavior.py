# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Callable as ValueFactory
from typing import cast as CastValue

# validator hooks bind late because validation rules sit above immutable storage
KValidatorHooks: dict[str, object] = {}


# one binder installs composed validation entries without importing rule modules upward
def BindValidator(HookName: str, HookValue: object) -> None:
    KValidatorHooks[HookName] = HookValue


# document validation methods preserve the historical model surface without owning rules
class DocumentValid:
    locals()["__slots__"] = ()

    # validation remains concrete so callers receive the runtime tuple contract directly
    def validate(self) -> tuple[str, ...]:
        HookValue = KValidatorHooks.get("validate")
        if not callable(HookValue):
            raise TypeError("document validation requires composed bindings")
        ValidatorFunc = CastValue(
            ValueFactory[[object], tuple[str, ...]],
            HookValue,
        )
        return ValidatorFunc(self)

    # assertion remains concrete so callers avoid object returning compatibility lookup
    def assert_valid(self) -> None:
        HookValue = KValidatorHooks.get("assert_valid")
        if not callable(HookValue):
            raise TypeError("document validation requires composed bindings")
        ValidatorFunc = CastValue(
            ValueFactory[[object], None],
            HookValue,
        )
        ValidatorFunc(self)

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def GetErrors(self) -> tuple[str, ...]:
        return self.validate()

    # pascal compatibility keeps existing adapters typed during lowercase method migration
    def AssertValid(self) -> None:
        self.assert_valid()
